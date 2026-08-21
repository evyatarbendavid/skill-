"""Map a live URL to the local source file that produces it.

This is the seam between "audit a live URL" (read-only, needs nothing local) and
"fix the site" (writes files, needs the source tree). Getting it wrong means
writing to the wrong file, so every ambiguous case returns None and becomes a
HUMAN_JUDGMENT finding instead of a guess.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse

# Never write into build output or dependencies — those get regenerated and the
# fix would silently vanish (or worse, get committed).
FORBIDDEN_PARTS = {
    "node_modules", "dist", "build", ".next", ".nuxt", "out",
    ".git", "__pycache__", "vendor", ".venv", "venv", "target",
    ".output", ".svelte-kit", "_site",
}

# Extensions we are willing to edit.
EDITABLE_SUFFIXES = {".html", ".htm"}


def is_forbidden(path: Path, root: Path) -> bool:
    """True if the path sits inside build output or dependencies."""
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True  # outside the root entirely — never touch it
    return any(part in FORBIDDEN_PARTS for part in relative.parts)


def candidate_paths(local_dir: Path, url: str) -> List[Path]:
    """Plausible local files for a URL, most likely first."""
    url_path = unquote(urlparse(url).path or "/")
    url_path = url_path.strip("/")

    if not url_path:
        return [local_dir / "index.html", local_dir / "index.htm"]

    base = local_dir / url_path
    candidates = []

    suffix = Path(url_path).suffix.lower()
    if suffix in EDITABLE_SUFFIXES:
        candidates.append(base)
    elif suffix:
        # A URL ending in .php/.aspx/.jsp has no HTML file we can safely edit.
        return []
    else:
        # Extensionless URL: could be a directory index or a sibling .html file.
        candidates.extend([
            base / "index.html",
            base / "index.htm",
            base.with_suffix(".html"),
            base.with_suffix(".htm"),
        ])
    return candidates


def resolve(local_dir: Path, url: str) -> Optional[Path]:
    """Resolve a URL to exactly one existing, editable local file.

    Returns None when nothing matches, when the match is in build output, or
    when several distinct files could plausibly be the source — the caller must
    then ask a human rather than pick.
    """
    local_dir = Path(local_dir)
    matches = []
    for candidate in candidate_paths(local_dir, url):
        if candidate.is_file() and not is_forbidden(candidate, local_dir):
            resolved = candidate.resolve()
            if resolved not in matches:
                matches.append(resolved)

    if len(matches) == 1:
        return matches[0]
    return None  # zero matches, or genuinely ambiguous


def explain_failure(local_dir: Path, url: str) -> str:
    """Human-readable reason resolve() returned None, for the report."""
    local_dir = Path(local_dir)
    candidates = candidate_paths(local_dir, url)

    if not candidates:
        return (
            f"{url} has a non-HTML extension — there is no static HTML file to "
            "edit. If this is server-rendered, the fix belongs in the template."
        )

    existing = [c for c in candidates if c.is_file()]
    if not existing:
        # Before reporting a missing index.html, check whether this project has
        # HTML files at all. On a framework project it does not, and "could not
        # find index.html" reads as a broken tool rather than as the answer.
        framework = detect_framework(local_dir)
        if framework is not None:
            source = likely_source(local_dir, url)
            where = (f"That URL is produced by "
                     f"{source.relative_to(local_dir)}. " if source else "")
            return (
                f"this is a {framework.name} project, so its pages are route "
                f"files, not HTML files this tool can safely edit. {where}"
                f"Make the change there — {framework.metadata_hint}. "
                f"Everything above still applies; only the automatic fix is off."
            )
        tried = ", ".join(str(c.relative_to(local_dir)) for c in candidates)
        return f"could not find a local file for {url} (tried: {tried})"

    blocked = [c for c in existing if is_forbidden(c, local_dir)]
    if blocked and len(blocked) == len(existing):
        return (
            f"the only local match for {url} is inside build output "
            f"({blocked[0].relative_to(local_dir)}) — edit the source template instead"
        )

    return (
        f"several files could be the source for {url}: "
        + ", ".join(str(c.relative_to(local_dir)) for c in existing)
        + " — tell me which one"
    )


# --------------------------------------------------------------------------
# Framework projects
#
# This tool only edits static HTML, which is the right limit — rewriting a JSX
# component or a Svelte route by pattern is how you corrupt someone's source.
# But most sites people ask about are framework projects, and telling them
# "could not find index.html" reads as a broken tool rather than as the real
# answer, which is "your pages aren't HTML files, and here is the file that
# actually produces this URL".
# --------------------------------------------------------------------------

ROUTE_SUFFIXES = (".tsx", ".jsx", ".ts", ".js", ".mjs", ".astro", ".svelte",
                  ".vue", ".md", ".mdx")


@dataclass
class Framework:
    name: str
    # Where the routes live, relative to the project root.
    routes_dir: str = ""
    # Basename a route file uses inside its own directory, if the framework
    # uses that shape ("page" for Next app router, "+page" for SvelteKit).
    route_basename: str = ""
    # Whether a route can also be a bare file next to its siblings.
    flat_files: bool = True
    # One sentence on where page metadata is actually set.
    metadata_hint: str = ""
    # Directory whose contents are served from the site root. A sitemap.xml at
    # the project root is not served by any of these frameworks.
    static_dir: str = ""
    # Route files that would generate a sitemap dynamically. If one exists, a
    # static file next to it is at best redundant and at worst conflicting.
    generated_sitemap_globs: tuple = ()


def _reads_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def detect_framework(local_dir: Path) -> Optional[Framework]:
    """Identify the framework behind a project, or None for plain HTML.

    Directory shape decides it — a dependency in package.json can be a leftover
    or a transitive pull, but app/page.tsx only exists because someone routes
    with it.
    """
    local_dir = Path(local_dir)
    pkg = _reads_json(local_dir / "package.json")
    deps = {}
    for key in ("dependencies", "devDependencies"):
        value = pkg.get(key)
        if isinstance(value, dict):
            deps.update(value)

    def has_route_files(directory: Path, basename: str = "") -> bool:
        if not directory.is_dir():
            return False
        pattern = f"{basename}.*" if basename else "*"
        for path in directory.rglob(pattern):
            if path.is_file() and path.suffix.lower() in ROUTE_SUFFIXES:
                if not is_forbidden(path, local_dir):
                    return True
        return False

    if has_route_files(local_dir / "app", "page") or has_route_files(local_dir / "src" / "app", "page"):
        root = "src/app" if (local_dir / "src" / "app").is_dir() else "app"
        return Framework(
            "Next.js (app router)", root, "page", flat_files=False,
            metadata_hint="title, description and canonical come from the "
                          "`export const metadata` (or `generateMetadata`) in "
                          "page.tsx and layout.tsx",
            static_dir="public",
            generated_sitemap_globs=(f"{root}/sitemap.*",))

    if has_route_files(local_dir / "pages") and "next" in deps:
        return Framework(
            "Next.js (pages router)", "pages",
            metadata_hint="head tags come from next/head inside the page "
                          "component, or from pages/_app and pages/_document",
            static_dir="public",
            generated_sitemap_globs=("pages/sitemap.xml.*",))

    if has_route_files(local_dir / "src" / "routes", "+page"):
        return Framework(
            "SvelteKit", "src/routes", "+page", flat_files=False,
            metadata_hint="head tags come from <svelte:head> in +page.svelte, "
                          "and shared ones from +layout.svelte",
            static_dir="static",
            generated_sitemap_globs=("src/routes/sitemap.xml/+server.*",))

    if has_route_files(local_dir / "src" / "pages") and "astro" in deps:
        return Framework(
            "Astro", "src/pages",
            metadata_hint="head tags usually live in a layout component under "
                          "src/layouts, with per-page values passed into it",
            static_dir="public")

    if has_route_files(local_dir / "src" / "pages") and "gatsby" in deps:
        return Framework(
            "Gatsby", "src/pages",
            metadata_hint="head tags come from the Head export or the Seo "
                          "component most Gatsby starters ship with",
            static_dir="static")

    if has_route_files(local_dir / "pages") and "nuxt" in deps:
        return Framework(
            "Nuxt", "pages",
            metadata_hint="head tags come from useHead/definePageMeta in the "
                          "page component, and app.vue for shared ones",
            static_dir="public")

    if (local_dir / "config.toml").is_file() or (local_dir / "hugo.toml").is_file():
        return Framework("Hugo", "content",
                         metadata_hint="head tags come from the templates in "
                                       "layouts/, with values from each page's "
                                       "front matter",
                         static_dir="static")

    if (local_dir / "_config.yml").is_file():
        return Framework("Jekyll", "",
                         metadata_hint="head tags come from _layouts and "
                                       "_includes, with values from front matter")

    return None


def _segment_matches(actual: str, candidate: str) -> bool:
    """Whether one route-directory name can serve a URL segment.

    Dynamic segments are written differently by every framework — [slug],
    [...rest], [[...opt]], $slug, :slug — and all of them match anything.
    """
    if candidate == actual:
        return True
    return (
        (candidate.startswith("[") and candidate.endswith("]"))
        or candidate.startswith("$")
        or candidate.startswith(":")
    )


def likely_source(local_dir: Path, url: str) -> Optional[Path]:
    """Best guess at the route file behind a URL in a framework project.

    Reported, never edited — the point is to hand someone the file to open.
    Returns None rather than guessing between equally plausible matches.
    """
    local_dir = Path(local_dir)
    framework = detect_framework(local_dir)
    if framework is None:
        return None

    root = local_dir / framework.routes_dir if framework.routes_dir else local_dir
    if not root.is_dir():
        return None

    segments = [s for s in (unquote(urlparse(url).path or "/")).split("/") if s]

    # Walk the URL's segments through the route tree, allowing dynamic ones.
    current = root
    for segment in segments:
        if not current.is_dir():
            return None
        children = [c for c in sorted(current.iterdir()) if c.is_dir()
                    and not is_forbidden(c, local_dir)]
        exact = [c for c in children if c.name == segment]
        dynamic = [c for c in children
                   if c.name != segment and _segment_matches(segment, c.name)]
        if exact:
            current = exact[0]
        elif len(dynamic) == 1:
            current = dynamic[0]
        elif dynamic:
            return None  # two dynamic routes could both serve this
        else:
            # No directory — the last segment may be a flat file instead.
            if segment is segments[-1] and framework.flat_files:
                flat = _files_named(current, segment, local_dir)
                return flat[0] if len(flat) == 1 else None
            return None

    names = [framework.route_basename] if framework.route_basename else ["index"]
    for name in names:
        found = _files_named(current, name, local_dir)
        if len(found) == 1:
            return found[0]
        if found:
            return None
    return None


def _files_named(directory: Path, stem: str, root: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.iterdir()
        if path.is_file()
        and path.stem == stem
        and path.suffix.lower() in ROUTE_SUFFIXES
        and not is_forbidden(path, root)
    )


def find_site_root_files(local_dir: Path, limit: int = 500) -> List[Path]:
    """All editable HTML files under local_dir, skipping build output."""
    local_dir = Path(local_dir)
    found = []
    for suffix in sorted(EDITABLE_SUFFIXES):
        for path in local_dir.rglob(f"*{suffix}"):
            if is_forbidden(path, local_dir):
                continue
            found.append(path)
            if len(found) >= limit:
                return sorted(found)
    return sorted(found)


def sitemap_target(local_dir: Path) -> tuple:
    """Where a sitemap.xml should be written, or why it should not be.

    Returns (path, None) when there is a safe place to write one, or
    (None, reason) when there isn't. On a framework project, a sitemap.xml at
    the repository root is not served at /sitemap.xml — it has to sit in the
    directory that framework copies to the site root, and if the project
    already generates one, a second static file is worse than nothing.
    """
    local_dir = Path(local_dir)
    framework = detect_framework(local_dir)
    if framework is None:
        return local_dir / "sitemap.xml", None

    for pattern in framework.generated_sitemap_globs:
        for existing in local_dir.glob(pattern):
            if existing.is_file() and not is_forbidden(existing, local_dir):
                return None, (
                    f"{framework.name} already generates a sitemap from "
                    f"{existing.relative_to(local_dir)} — add the missing URLs "
                    f"there. A static sitemap.xml alongside it would either be "
                    f"ignored or shadow the generated one."
                )

    if framework.name == "Hugo":
        return None, (
            "Hugo generates sitemap.xml on every build, so a static one would "
            "be overwritten. If pages are missing from it, they are excluded "
            "in front matter or by a sitemap template override."
        )

    if not framework.static_dir:
        return None, (
            f"could not tell where {framework.name} serves static files from — "
            f"put sitemap.xml wherever this project serves /robots.txt from."
        )

    static_root = local_dir / framework.static_dir
    if not static_root.is_dir():
        return None, (
            f"a {framework.name} project serves static files from "
            f"{framework.static_dir}/, which does not exist here. Create it and "
            f"re-run, or add the sitemap the way this project generates one."
        )
    return static_root / "sitemap.xml", None

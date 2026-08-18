"""Map a live URL to the local source file that produces it.

This is the seam between "audit a live URL" (read-only, needs nothing local) and
"fix the site" (writes files, needs the source tree). Getting it wrong means
writing to the wrong file, so every ambiguous case returns None and becomes a
HUMAN_JUDGMENT finding instead of a guess.
"""

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

"""The write path: turning findings into real file edits.

Every fix is planned first and rendered as a unified diff, then written only on
explicit apply. Three rules run through all of it:

  1. Append, never clobber. An existing canonical tag or JSON-LD block reflects
     a decision someone already made.
  2. Never invent a value. Anything only a human knows stays a TODO placeholder
     and is reported separately.
  3. When the right answer is ambiguous, refuse and say why.
"""

import difflib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
from xml.dom import minidom

from . import pathmap
from .htmldoc import head_insert_offset

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "jsonld-templates"


@dataclass
class FixItem:
    """One planned edit. Nothing is written until write() is called."""

    finding_id: str
    kind: str  # "sitemap" | "canonical" | "jsonld"
    path: Path
    new_content: str
    old_content: str = ""
    summary: str = ""
    created: bool = False  # file did not exist before
    placeholders: List[str] = field(default_factory=list)
    applied: bool = False

    def render_diff(self, context_lines: int = 3) -> str:
        old_lines = self.old_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)
        label = str(self.path)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{label}" + (" (new file)" if self.created else ""),
            tofile=f"b/{label}",
            n=context_lines,
        )
        return "".join(diff)

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.new_content, encoding="utf-8")
        self.applied = True

    def to_dict(self) -> Dict:
        return {
            "finding_id": self.finding_id,
            "kind": self.kind,
            "path": str(self.path),
            "summary": self.summary,
            "created": self.created,
            "applied": self.applied,
            "placeholders": self.placeholders,
            "diff": self.render_diff(),
        }


@dataclass
class FixPlan:
    items: List[FixItem] = field(default_factory=list)
    refusals: List[Dict[str, str]] = field(default_factory=list)
    # Planned-but-unwritten content per file. Several fixes can target the same
    # page (a canonical tag and a JSON-LD block, say); without this each one
    # would be computed against the on-disk text and the last write would
    # silently discard the others.
    pending: Dict[Path, str] = field(default_factory=dict)

    def refuse(self, finding_id: str, reason: str) -> None:
        """Record a fix we declined to make, and why. A refusal is a result."""
        self.refusals.append({"finding_id": finding_id, "reason": reason})

    def current_content(self, path: Path) -> str:
        """The file as the next fix should see it: pending edits, else disk."""
        if path in self.pending:
            return self.pending[path]
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
        return ""

    def stage(self, item: FixItem) -> FixItem:
        self.pending[item.path] = item.new_content
        self.items.append(item)
        return item

    def apply_all(self) -> int:
        """Write each touched file exactly once, with all its edits composed."""
        for path, content in self.pending.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for item in self.items:
            item.applied = True
        return len(self.pending)


# --------------------------------------------------------------------------
# sitemap.xml
# --------------------------------------------------------------------------

def _prettify(root: ET.Element) -> str:
    raw = ET.tostring(root, encoding="unicode")
    parsed = minidom.parseString(raw)
    pretty = parsed.toprettyxml(indent="  ")
    # minidom emits its own declaration plus blank lines; normalize both.
    lines = [line for line in pretty.splitlines() if line.strip()]
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines) + "\n"


def plan_sitemap(
    plan: FixPlan,
    local_dir: Path,
    urls: List[str],
    lastmods: Optional[Dict[str, str]] = None,
    finding_id: str = "A5",
) -> Optional[FixItem]:
    """Create sitemap.xml, or add missing URLs to an existing one.

    Never rewrites an existing sitemap wholesale — only appends entries it does
    not already contain, so hand-tuned priority/changefreq values survive.
    """
    local_dir = Path(local_dir)
    target = local_dir / "sitemap.xml"

    if not urls:
        plan.refuse(finding_id, "no crawlable URLs found to put in a sitemap")
        return None

    today = date.today().isoformat()
    lastmods = lastmods or {}

    existing_content = plan.current_content(target)
    if existing_content:
        old_content = existing_content
        try:
            root = ET.fromstring(old_content.lstrip("﻿ \t\r\n"))
        except ET.ParseError as exc:
            plan.refuse(
                finding_id,
                f"sitemap.xml exists but is not valid XML ({exc}) — fixing it "
                "could destroy entries, so it needs a look by hand",
            )
            return None

        existing = {
            (loc.text or "").strip()
            for loc in root.iter()
            if loc.tag.split("}")[-1] == "loc"
        }
        missing = [u for u in urls if u not in existing]
        if not missing:
            return None  # nothing to do

        for url in missing:
            url_el = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(url_el, f"{{{SITEMAP_NS}}}loc").text = url
            ET.SubElement(url_el, f"{{{SITEMAP_NS}}}lastmod").text = lastmods.get(url, today)

        summary = f"add {len(missing)} missing URL(s) to sitemap.xml"
        created = False
    else:
        old_content = ""
        root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
        for url in urls:
            url_el = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(url_el, f"{{{SITEMAP_NS}}}loc").text = url
            ET.SubElement(url_el, f"{{{SITEMAP_NS}}}lastmod").text = lastmods.get(url, today)
        summary = f"create sitemap.xml with {len(urls)} URL(s)"
        created = True

    ET.register_namespace("", SITEMAP_NS)
    new_content = _prettify(root)

    # Never write XML we can't parse back.
    try:
        ET.fromstring(new_content)
    except ET.ParseError as exc:
        plan.refuse(finding_id, f"generated sitemap failed its own validity check: {exc}")
        return None

    return plan.stage(FixItem(
        finding_id=finding_id,
        kind="sitemap",
        path=target,
        old_content=old_content,
        new_content=new_content,
        summary=summary,
        created=created,
    ))


def _match_indent(html: str, line_start: int) -> str:
    """Indentation to give an injected tag.

    Match the last real element inside head rather than the `</head>` line
    itself — closing tags usually sit at the parent's indent level, so copying
    that would place the new tag a level out from its siblings.
    """
    preceding = html[:line_start].rstrip("\n")
    for line in reversed(preceding.splitlines()):
        if line.strip():
            return line[: len(line) - len(line.lstrip())]
    return "  "


# --------------------------------------------------------------------------
# canonical
# --------------------------------------------------------------------------

def plan_canonical(
    plan: FixPlan,
    local_dir: Path,
    page_url: str,
    canonical_url: str,
    finding_id: str = "A4",
) -> Optional[FixItem]:
    """Insert a self-referencing canonical tag.

    Only ever called for the unambiguous case (no canonical tag at all) — see
    canonical.CanonicalResult.auto_fixable.
    """
    local_dir = Path(local_dir)
    target = pathmap.resolve(local_dir, page_url)
    if target is None:
        plan.refuse(finding_id, pathmap.explain_failure(local_dir, page_url))
        return None

    html = plan.current_content(target)

    if "rel=\"canonical\"" in html.lower().replace("'", '"'):
        plan.refuse(
            finding_id,
            f"{target.name} already contains a canonical tag — not overwriting it",
        )
        return None

    offset = head_insert_offset(html)
    if offset is None:
        plan.refuse(
            finding_id,
            f"{target.name} has no closing head tag, so there is no safe place "
            "to insert the canonical link",
        )
        return None

    line_start = html.rfind("\n", 0, offset) + 1
    indent = _match_indent(html, line_start)

    tag = f'{indent}<link rel="canonical" href="{canonical_url}">\n'
    new_content = html[:line_start] + tag + html[line_start:]

    return plan.stage(FixItem(
        finding_id=finding_id,
        kind="canonical",
        path=target,
        old_content=html,
        new_content=new_content,
        summary=f"add self-referencing canonical -> {canonical_url}",
    ))


# --------------------------------------------------------------------------
# JSON-LD
# --------------------------------------------------------------------------

def _load_template(name: str) -> Optional[dict]:
    path = TEMPLATE_DIR / f"{name}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _fill(node, known: Dict[str, str], placeholders: List[str], trail: str = "",
          depth: int = 0) -> None:
    """Replace TODO placeholders with values we actually know.

    Substitution happens at the top level only. Nested objects reuse generic key
    names — an Article's author and its publisher both have `name` and `url` —
    and filling those from page-level values produces markup that is confidently
    wrong (the author named after the page title, a logo pointing at the page).
    Wrong structured data is worse than absent structured data, so anything
    nested stays a TODO and gets reported for a human to fill.
    """
    if isinstance(node, dict):
        for key, value in list(node.items()):
            path = f"{trail}.{key}" if trail else key
            if isinstance(value, str) and value.startswith("TODO"):
                if depth == 0 and known.get(key):
                    node[key] = known[key]
                else:
                    placeholders.append(path)
            elif isinstance(value, (dict, list)):
                _fill(value, known, placeholders, path, depth + 1)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            path = f"{trail}[{i}]"
            if isinstance(value, str) and value.startswith("TODO"):
                placeholders.append(path)
            elif isinstance(value, (dict, list)):
                _fill(value, known, placeholders, path, depth + 1)


def plan_jsonld(
    plan: FixPlan,
    local_dir: Path,
    page_url: str,
    schema_type: str,
    known: Optional[Dict[str, str]] = None,
    finding_id: str = "C1",
) -> Optional[FixItem]:
    """Inject a JSON-LD block, appending only — existing blocks are untouched."""
    local_dir = Path(local_dir)
    target = pathmap.resolve(local_dir, page_url)
    if target is None:
        plan.refuse(finding_id, pathmap.explain_failure(local_dir, page_url))
        return None

    template = _load_template(schema_type.lower())
    if template is None:
        plan.refuse(finding_id, f"no JSON-LD template available for '{schema_type}'")
        return None

    html = plan.current_content(target)

    offset = head_insert_offset(html)
    if offset is None:
        plan.refuse(
            finding_id,
            f"{target.name} has no closing head tag, so there is no safe place "
            "to insert the JSON-LD block",
        )
        return None

    placeholders: List[str] = []
    _fill(template, known or {}, placeholders)

    body = json.dumps(template, indent=2, ensure_ascii=False)
    line_start = html.rfind("\n", 0, offset) + 1
    indent = _match_indent(html, line_start)
    indented_body = "\n".join(f"{indent}{line}" for line in body.splitlines())

    block = (
        f'{indent}<script type="application/ld+json">\n'
        f"{indented_body}\n"
        f"{indent}</script>\n"
    )
    new_content = html[:line_start] + block + html[line_start:]

    summary = f"add {schema_type} JSON-LD block"
    if placeholders:
        summary += f" ({len(placeholders)} field(s) left as TODO for you to fill)"

    return plan.stage(FixItem(
        finding_id=finding_id,
        kind="jsonld",
        path=target,
        old_content=html,
        new_content=new_content,
        summary=summary,
        placeholders=placeholders,
    ))

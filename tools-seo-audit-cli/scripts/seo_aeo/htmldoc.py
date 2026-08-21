"""Single-pass HTML parsing shared by every check.

Standard library only (html.parser) — bs4/lxml are deliberately not required so
this runs on a bare Python install with no pip step.

Parse each page once into an HtmlDoc; every check reads from that rather than
re-parsing the same markup six times.
"""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

# Tags whose text content is not visible page content.
_NON_CONTENT_TAGS = {"script", "style", "noscript", "template", "svg", "head"}

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


@dataclass
class HtmlDoc:
    title: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)  # name -> content (lowercased name)
    meta_http_equiv: Dict[str, str] = field(default_factory=dict)
    canonical: Optional[str] = None
    lang: Optional[str] = None
    links: List[Tuple[str, str]] = field(default_factory=list)  # (href, anchor text)
    images: List[Dict[str, str]] = field(default_factory=list)  # attrs of each img
    headings: List[Tuple[int, str]] = field(default_factory=list)  # (level, text)
    jsonld_raw: List[str] = field(default_factory=list)
    visible_text: str = ""
    # Same text, but one entry per text node, so checks that care about
    # element boundaries (bidi isolation) do not see two unrelated strings
    # from different elements as one sentence.
    text_runs: List[str] = field(default_factory=list)
    has_main: bool = False
    has_nav: bool = False
    has_viewport: bool = False
    head_end_offset: Optional[int] = None  # byte offset of </head> for injection
    charset: Optional[str] = None
    parse_error: Optional[str] = None

    @property
    def meta_description(self) -> Optional[str]:
        return self.meta.get("description")

    @property
    def meta_robots(self) -> Optional[str]:
        return self.meta.get("robots")

    @property
    def h1s(self) -> List[str]:
        return [text for level, text in self.headings if level == 1]

    def first_words(self, n: int = 150) -> str:
        return " ".join(self.visible_text.split()[:n])


class _DocParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.doc = HtmlDoc()
        self._suppress_depth = 0  # inside script/style/etc.
        self._current_script_type: Optional[str] = None
        self._script_buffer: List[str] = []
        self._text_parts: List[str] = []
        self._heading_level: Optional[int] = None
        self._heading_parts: List[str] = []
        self._in_title = False
        self._title_parts: List[str] = []
        self._link_href: Optional[str] = None
        self._link_parts: List[str] = []

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _attrs_dict(attrs) -> Dict[str, str]:
        return {k.lower(): (v if v is not None else "") for k, v in attrs}

    # -- tag handling ----------------------------------------------------

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = self._attrs_dict(attrs)
        doc = self.doc

        if tag == "html":
            if "lang" in a:
                doc.lang = a["lang"].strip()
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower().strip()
            if name:
                doc.meta[name] = a.get("content", "").strip()
            if "http-equiv" in a:
                doc.meta_http_equiv[a["http-equiv"].lower().strip()] = a.get("content", "").strip()
            if "charset" in a:
                doc.charset = a["charset"].strip()
            if name == "viewport":
                doc.has_viewport = True
        elif tag == "link":
            rels = (a.get("rel") or "").lower().split()
            if "canonical" in rels and a.get("href"):
                # First canonical wins; a second one is a conflict the
                # canonical check reports separately.
                if doc.canonical is None:
                    doc.canonical = a["href"].strip()
                else:
                    doc.meta.setdefault("__multiple_canonical__", "true")
        elif tag == "script":
            stype = (a.get("type") or "").lower().strip()
            self._current_script_type = stype
            self._script_buffer = []
        elif tag == "img":
            doc.images.append(a)
        elif tag == "a" and a.get("href"):
            self._link_href = a["href"].strip()
            self._link_parts = []
        elif tag == "main":
            doc.has_main = True
        elif tag == "nav":
            doc.has_nav = True
        elif tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_level = int(tag[1])
            self._heading_parts = []

        if tag in _NON_CONTENT_TAGS:
            self._suppress_depth += 1

        # Track where </head> is so the fixer knows a safe injection point.
        if tag in _VOID_TAGS:
            return

    def handle_startendtag(self, tag, attrs):
        # Self-closing form: handle attrs, but never open a suppression scope.
        tag_l = tag.lower()
        if tag_l in _NON_CONTENT_TAGS:
            a = self._attrs_dict(attrs)
            if tag_l == "img":
                self.doc.images.append(a)
            return
        self.handle_starttag(tag, attrs)
        if tag_l in _NON_CONTENT_TAGS:
            self._suppress_depth = max(0, self._suppress_depth - 1)

    def handle_endtag(self, tag):
        tag = tag.lower()
        doc = self.doc

        if tag == "script":
            if self._current_script_type == "application/ld+json":
                blob = "".join(self._script_buffer).strip()
                if blob:
                    doc.jsonld_raw.append(blob)
            self._current_script_type = None
            self._script_buffer = []
        elif tag == "title":
            self._in_title = False
            if doc.title is None:
                doc.title = " ".join("".join(self._title_parts).split())
        elif tag == "a":
            if self._link_href is not None:
                anchor = " ".join("".join(self._link_parts).split())
                doc.links.append((self._link_href, anchor))
            self._link_href = None
            self._link_parts = []
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self._heading_level is not None:
                text = " ".join("".join(self._heading_parts).split())
                doc.headings.append((self._heading_level, text))
            self._heading_level = None
            self._heading_parts = []
        elif tag == "head":
            doc.head_end_offset = self.getpos()[0]  # line number; refined later

        if tag in _NON_CONTENT_TAGS:
            self._suppress_depth = max(0, self._suppress_depth - 1)

    def handle_data(self, data):
        if self._current_script_type == "application/ld+json":
            self._script_buffer.append(data)
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        if self._suppress_depth > 0:
            return
        if self._heading_level is not None:
            self._heading_parts.append(data)
        if self._link_href is not None:
            self._link_parts.append(data)
        stripped = data.strip()
        if stripped:
            self._text_parts.append(stripped)

    def finish(self) -> HtmlDoc:
        self.doc.visible_text = " ".join(self._text_parts)
        self.doc.text_runs = list(self._text_parts)
        return self.doc


def parse(html: str) -> HtmlDoc:
    """Parse HTML into an HtmlDoc. Never raises — malformed markup yields a
    partial doc with parse_error set, which is more useful than a crash."""
    parser = _DocParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # html.parser is lenient but not bulletproof
        parser.doc.parse_error = f"{type(exc).__name__}: {exc}"
    return parser.finish()


_HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.IGNORECASE)
_HTML_OPEN_RE = re.compile(r"<html[^>]*>", re.IGNORECASE)


def head_insert_offset(html: str) -> Optional[int]:
    """Character offset just before </head>, for safely injecting tags.

    Returns None when there is no </head> — the caller must then treat the fix
    as needing human attention rather than guessing where to write.
    """
    match = _HEAD_CLOSE_RE.search(html)
    return match.start() if match else None


def has_noindex(doc: HtmlDoc) -> bool:
    """True if any robots-style meta directive contains noindex."""
    for name in ("robots", "googlebot"):
        value = doc.meta.get(name, "")
        if "noindex" in value.lower():
            return True
    return False


def normalize_visible_text(text: str) -> str:
    """Whitespace/case-normalized text for duplicate-content hashing."""
    return " ".join(text.lower().split())

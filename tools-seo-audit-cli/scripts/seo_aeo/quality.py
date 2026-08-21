"""Content-quality, RTL, and site-hygiene checks.

These are the "boring but costly" failures: placeholder text shipped to
production, titles that get truncated in results, anchor text that says
"click here", orphan pages, and bidi bugs that scramble Hebrew pages
containing English or numbers.

Several are accessibility bugs first and SEO bugs second, which is why they
are worth fixing twice over.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .fetch import normalize_url
from .htmldoc import HtmlDoc

# Google truncates around 60 characters; under ~30 usually wastes the slot.
TITLE_MIN, TITLE_IDEAL_MAX, TITLE_HARD_MAX = 30, 60, 65
META_MIN, META_IDEAL_MAX, META_HARD_MAX = 110, 160, 165

# Text that should never reach production.
PLACEHOLDER_PATTERNS = [
    (r"\blorem ipsum\b", "Lorem ipsum"),
    (r"\bTODO\b", "TODO"),
    (r"\bFIXME\b", "FIXME"),
    (r"\bundefined\b", "undefined"),
    (r"\[object Object\]", "[object Object]"),
    (r"\bNaN\b", "NaN"),
    (r"\bplaceholder text\b", "placeholder text"),
    (r"\byour text here\b", "your text here"),
    (r"\blipsum\b", "lipsum"),
]

# Anchor text that tells neither a reader nor a crawler where a link goes.
VAGUE_ANCHORS = {
    "click here", "here", "read more", "more", "link", "this",
    "learn more", "see more", "details", "info", "click",
    "לחץ כאן", "כאן", "קרא עוד", "עוד", "פרטים", "מידע נוסף",
}

RTL_LANGS = ("he", "ar", "fa", "ur", "yi")

_HEBREW_RE = re.compile(r"[֐-׿]")
_ARABIC_RE = re.compile(r"[؀-ۿ]")
_LATIN_RUN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.\-]{2,}")

# Share of letters that must be Hebrew/Arabic before an LTR-declared page is
# treated as RTL content. Set well above what a language picker contributes
# and well below what a genuinely bilingual page carries.
RTL_CONTENT_THRESHOLD = 0.05


@dataclass
class QualityResult:
    title_len: Optional[int] = None
    title_issue: str = ""
    meta_len: Optional[int] = None
    meta_issue: str = ""
    placeholders: List[str] = field(default_factory=list)
    vague_anchors: List[str] = field(default_factory=list)
    images_without_dimensions: List[str] = field(default_factory=list)
    lazy_loaded_early_images: List[str] = field(default_factory=list)
    legacy_image_formats: List[str] = field(default_factory=list)


@dataclass
class RtlResult:
    lang: Optional[str] = None
    dir_attr: Optional[str] = None
    is_rtl_language: bool = False
    dir_missing: bool = False
    dir_mismatch: bool = False
    bidi_risk_samples: List[str] = field(default_factory=list)
    mixed_slug_style: bool = False
    applicable: bool = False
    rtl_char_share: float = 0.0


def check_title(doc: HtmlDoc) -> tuple:
    if not doc.title:
        return None, "no title element — Google will invent one from page content"
    length = len(doc.title)
    if length > TITLE_HARD_MAX:
        return length, f"title is {length} chars; likely truncated past ~{TITLE_IDEAL_MAX}"
    if length < TITLE_MIN:
        return length, f"title is only {length} chars — the slot is being wasted"
    return length, ""


def check_meta_description(doc: HtmlDoc) -> tuple:
    desc = doc.meta_description
    if not desc:
        return None, "no meta description — Google will compose its own snippet"
    length = len(desc)
    if length > META_HARD_MAX:
        return length, f"meta description is {length} chars; truncated past ~{META_IDEAL_MAX}"
    if length < META_MIN:
        return length, (f"meta description is only {length} chars — short for the "
                        "space available, and this is CTR copy, not a ranking factor")
    return length, ""


def find_placeholders(doc: HtmlDoc) -> List[str]:
    """Placeholder text in the visible copy. Checked against visible text only,
    so a TODO in a code sample or comment does not produce a false alarm."""
    text = doc.visible_text
    found = []
    for pattern, label in PLACEHOLDER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 30)
            snippet = text[start:match.end() + 30].strip()
            found.append(f"{label}: ...{snippet}...")
    return found


def find_vague_anchors(doc: HtmlDoc) -> List[str]:
    out = []
    for href, anchor in doc.links:
        normalized = anchor.strip().lower().rstrip(".!?›»>").strip()
        if normalized and normalized in VAGUE_ANCHORS:
            out.append(f"{anchor.strip()!r} -> {href}")
    return out


def check_images(doc: HtmlDoc) -> tuple:
    """Dimension attributes (CLS), lazy-loading the hero (LCP), and formats."""
    missing_dims, lazy_early, legacy = [], [], []
    for index, img in enumerate(doc.images):
        src = img.get("src", "(no src)")
        if not (img.get("width") and img.get("height")):
            missing_dims.append(src)
        # The first couple of images are almost certainly above the fold; lazy
        # loading one of them delays the LCP element it probably is.
        if index < 2 and img.get("loading", "").lower() == "lazy":
            lazy_early.append(src)
        if re.search(r"\.(jpe?g|png)(\?|$)", src, re.IGNORECASE):
            legacy.append(src)
    return missing_dims, lazy_early, legacy


def analyze(doc: HtmlDoc) -> QualityResult:
    result = QualityResult()
    result.title_len, result.title_issue = check_title(doc)
    result.meta_len, result.meta_issue = check_meta_description(doc)
    result.placeholders = find_placeholders(doc)
    result.vague_anchors = find_vague_anchors(doc)
    (result.images_without_dimensions,
     result.lazy_loaded_early_images,
     result.legacy_image_formats) = check_images(doc)
    return result


def analyze_rtl(doc: HtmlDoc, html: str, page_url: str = "") -> RtlResult:
    """RTL correctness. Only meaningful when the page is actually RTL.

    A Hebrew or Arabic page that omits dir="rtl", or that mixes Latin text and
    numbers into RTL runs without isolation, renders in a visibly wrong order —
    a correctness bug before it is ever an SEO one.
    """
    result = RtlResult(lang=doc.lang)

    match = re.search(r"<html[^>]*\bdir\s*=\s*[\"']?([a-zA-Z]+)", html, re.IGNORECASE)
    result.dir_attr = match.group(1).lower() if match else None

    lang_prefix = (doc.lang or "").lower().split("-")[0]
    result.is_rtl_language = lang_prefix in RTL_LANGS

    # A single Hebrew or Arabic word does not make a page RTL. Language pickers
    # label their own options in their own script ("\u05e2\u05d1\u05e8\u05d9\u05ea", "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"), so an
    # entirely English page routinely carries a few RTL characters. Measure the
    # share instead: below the threshold the page is LTR with incidental RTL
    # labels, and running bidi analysis on it only produces noise.
    rtl_chars = len(_HEBREW_RE.findall(doc.visible_text)) + len(_ARABIC_RE.findall(doc.visible_text))
    letters = sum(1 for ch in doc.visible_text if ch.isalpha())
    result.rtl_char_share = (rtl_chars / letters) if letters else 0.0
    has_rtl_script = result.rtl_char_share >= RTL_CONTENT_THRESHOLD

    # Only assess RTL when the page is RTL by declaration or by actual content.
    result.applicable = result.is_rtl_language or has_rtl_script
    if not result.applicable:
        return result

    if result.dir_attr is None:
        result.dir_missing = True
    elif result.is_rtl_language and result.dir_attr != "rtl":
        result.dir_mismatch = True

    # Latin runs inside RTL text are the classic bidi hazard.
    if has_rtl_script and "<bdi" not in html.lower() and 'dir="auto"' not in html.lower():
        # Scan text node by text node. Splitting the flattened page text on
        # ". " would staple a Hebrew menu label to the unrelated English string
        # that happened to follow it in the DOM and report that as a hazard.
        for run in doc.text_runs:
            for line in run.split(". "):
                if _HEBREW_RE.search(line) and _LATIN_RUN_RE.search(line):
                    result.bidi_risk_samples.append(line.strip()[:90])
                    break
            if len(result.bidi_risk_samples) >= 3:
                break

    return result


def find_orphans(sitemap_urls: Set[str], linked_urls: Set[str],
                 limit: int = 10) -> List[str]:
    """URLs a sitemap declares that nothing in the crawl links to.

    An orphan is live and declared but unreachable by following links, so it
    accumulates no internal signal and is easy for a crawler to skip.
    """
    orphans = sorted(normalize_url(u) for u in sitemap_urls
                     if normalize_url(u) not in linked_urls)
    return orphans[:limit]


def find_redirect_chains(chain: List) -> Optional[str]:
    if len(chain) <= 1:
        return None
    hops = " -> ".join(f"{url} ({status})" for url, status in chain)
    return hops

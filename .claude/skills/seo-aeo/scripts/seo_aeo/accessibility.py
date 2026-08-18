"""Accessibility and mobile checks that can be decided from static HTML.

Deliberately narrow. Contrast, keyboard operability, and screen-reader quality
need a rendered page and a human — those are reported as N/A with a pointer,
never guessed at from markup.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from .htmldoc import HtmlDoc


@dataclass
class ImageAltResult:
    total: int = 0
    with_alt: int = 0
    decorative: int = 0  # alt="" — explicitly decorative, which is correct
    missing: List[str] = field(default_factory=list)  # src values lacking alt

    @property
    def ok(self) -> bool:
        return not self.missing


@dataclass
class HeadingResult:
    h1_count: int = 0
    skipped_levels: List[str] = field(default_factory=list)
    first_level: Optional[int] = None

    @property
    def ok(self) -> bool:
        return self.h1_count == 1 and not self.skipped_levels


def check_images(doc: HtmlDoc) -> ImageAltResult:
    result = ImageAltResult(total=len(doc.images))
    for img in doc.images:
        src = img.get("src", "(no src)")
        if "alt" not in img:
            # Presentational roles legitimately don't need alt text.
            if img.get("role", "").lower() in ("presentation", "none"):
                result.decorative += 1
                continue
            result.missing.append(src)
        elif img["alt"].strip() == "":
            result.decorative += 1
        else:
            result.with_alt += 1
    return result


def check_headings(doc: HtmlDoc) -> HeadingResult:
    result = HeadingResult()
    levels = [level for level, _ in doc.headings]
    result.h1_count = levels.count(1)
    if levels:
        result.first_level = levels[0]

    previous = None
    for level, text in doc.headings:
        if previous is not None and level > previous + 1:
            label = text[:40] or "(empty heading)"
            result.skipped_levels.append(f"h{previous} -> h{level} at '{label}'")
        previous = level
    return result


def check_https(url: str) -> bool:
    return urlparse(url).scheme.lower() == "https"


def check_mixed_content(doc: HtmlDoc, page_url: str) -> List[str]:
    """http:// subresources on an https:// page — browsers block these."""
    if not check_https(page_url):
        return []
    insecure = []
    for img in doc.images:
        src = img.get("src", "")
        if src.lower().startswith("http://"):
            insecure.append(src)
    return insecure


def check_semantics(doc: HtmlDoc) -> List[str]:
    """Missing structural landmarks. Warnings, not failures — a valid page can
    legitimately lack <nav>."""
    issues = []
    if not doc.has_main:
        issues.append("no main element (screen readers use it to skip to content)")
    if not doc.has_nav:
        issues.append("no nav element")
    return issues

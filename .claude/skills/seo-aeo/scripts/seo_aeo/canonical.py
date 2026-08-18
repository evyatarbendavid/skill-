"""Canonical tag extraction and consistency checking.

The interesting cases are not "present or absent" but the ambiguous ones, which
this module is careful to classify rather than resolve:

  - no canonical at all, single obvious candidate  -> safely auto-fixable
  - canonical points somewhere else                -> human judgment, never
                                                       silently overwritten
  - two canonical tags                             -> human judgment
"""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

from .fetch import normalize_url, same_host
from .htmldoc import HtmlDoc

# Classification outcomes
MISSING = "missing"
SELF = "self"
OTHER_SAME_SITE = "other_same_site"
CROSS_DOMAIN = "cross_domain"
MULTIPLE = "multiple"
RELATIVE = "relative"


@dataclass
class CanonicalResult:
    present: bool = False
    raw_value: Optional[str] = None
    resolved: Optional[str] = None
    classification: str = MISSING
    is_absolute: bool = False
    detail: str = ""

    @property
    def auto_fixable(self) -> bool:
        """Only the unambiguous case: no tag at all. Anything else means a
        human has already expressed intent we should not overwrite."""
        return self.classification == MISSING

    @property
    def needs_human(self) -> bool:
        return self.classification in (OTHER_SAME_SITE, CROSS_DOMAIN, MULTIPLE)


def check(doc: HtmlDoc, page_url: str) -> CanonicalResult:
    result = CanonicalResult()

    if doc.meta.get("__multiple_canonical__"):
        result.present = True
        result.raw_value = doc.canonical
        result.resolved = urljoin(page_url, doc.canonical) if doc.canonical else None
        result.classification = MULTIPLE
        result.detail = (
            "More than one rel=canonical tag on the page. Google may ignore all "
            "of them. Pick one — which one is a content decision."
        )
        return result

    if not doc.canonical:
        result.classification = MISSING
        result.detail = "No rel=canonical tag found."
        return result

    result.present = True
    result.raw_value = doc.canonical
    result.is_absolute = doc.canonical.lower().startswith(("http://", "https://"))
    resolved = urljoin(page_url, doc.canonical)
    result.resolved = resolved

    if normalize_url(resolved) == normalize_url(page_url):
        result.classification = SELF if result.is_absolute else RELATIVE
        if result.is_absolute:
            result.detail = f"Self-referencing canonical: {resolved}"
        else:
            result.detail = (
                f"Canonical is relative ('{doc.canonical}') and resolves to this "
                "page. Google accepts relative URLs, but absolute is the "
                "documented recommendation and is harder to get wrong."
            )
        return result

    if same_host(resolved, page_url):
        result.classification = OTHER_SAME_SITE
        result.detail = (
            f"Canonical points to a different URL on this site: {resolved}. "
            "That is legitimate for a duplicate page, and wrong if this page is "
            "meant to rank on its own — only you can tell which."
        )
    else:
        result.classification = CROSS_DOMAIN
        result.detail = (
            f"Canonical points to another domain: {resolved}. This tells Google "
            "not to index this page at all. Intentional for syndicated content, "
            "a serious bug otherwise."
        )
    return result

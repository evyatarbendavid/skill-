"""Bounded internal crawl: broken links and duplicate content.

Hard-bounded by page count and depth, respects robots.txt per URL, and sleeps
between requests. An audit tool that hammers someone's site is a bug.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from . import htmldoc
from .fetch import FetchResult, fetch, normalize_url, same_host
from .robots import RobotsResult, agent_allows

DEFAULT_MAX_PAGES = 25
DEFAULT_MAX_DEPTH = 2
DEFAULT_DELAY = 0.3  # seconds between requests

# Non-page links we should never follow or report as broken pages.
_SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "sms:", "#")
_ASSET_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico",
    ".css", ".js", ".pdf", ".zip", ".mp4", ".mp3", ".woff", ".woff2", ".ttf",
)


@dataclass
class PageRecord:
    url: str
    status: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    content_hash: str = ""
    word_count: int = 0
    outlinks: List[str] = field(default_factory=list)
    depth: int = 0


@dataclass
class BrokenLink:
    source: str
    target: str
    status: Optional[int]
    error: Optional[str] = None
    anchor: str = ""


@dataclass
class CrawlResult:
    pages: Dict[str, PageRecord] = field(default_factory=dict)
    broken: List[BrokenLink] = field(default_factory=list)
    duplicate_titles: Dict[str, List[str]] = field(default_factory=dict)
    duplicate_meta: Dict[str, List[str]] = field(default_factory=dict)
    duplicate_content: Dict[str, List[str]] = field(default_factory=dict)
    blocked_by_robots: List[str] = field(default_factory=list)
    limit_reached: bool = False
    checked_links: int = 0

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def inbound_links_to(self, url: str) -> List[str]:
        """Which crawled pages link to `url` — answers 'is this page orphaned?'"""
        target = normalize_url(url)
        return [
            page.url
            for page in self.pages.values()
            if normalize_url(page.url) != target
            and any(normalize_url(link) == target for link in page.outlinks)
        ]


def _is_crawlable_link(href: str) -> bool:
    lowered = href.strip().lower()
    if not lowered or lowered.startswith(_SKIP_SCHEMES):
        return False
    path = urlparse(lowered).path
    return not path.endswith(_ASSET_SUFFIXES)


def _extract_links(doc: htmldoc.HtmlDoc, page_url: str, base_url: str
                   ) -> List[Tuple[str, str]]:
    """Absolute, same-host, crawlable (url, anchor) pairs."""
    out = []
    seen = set()
    for href, anchor in doc.links:
        if not _is_crawlable_link(href):
            continue
        absolute = urljoin(page_url, href.strip())
        if not absolute.lower().startswith(("http://", "https://")):
            continue
        if not same_host(absolute, base_url):
            continue
        key = normalize_url(absolute)
        if key in seen:
            continue
        seen.add(key)
        out.append((absolute, anchor))
    return out


def crawl(
    start_url: str,
    robots: Optional[RobotsResult] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    delay: float = DEFAULT_DELAY,
    timeout: int = 15,
) -> CrawlResult:
    result = CrawlResult()
    frontier: List[Tuple[str, int, Optional[str]]] = [(start_url, 0, None)]
    seen: Set[str] = set()

    while frontier and len(result.pages) < max_pages:
        url, depth, source = frontier.pop(0)
        key = normalize_url(url)
        if key in seen:
            continue
        seen.add(key)

        if robots is not None and not agent_allows(robots, url):
            result.blocked_by_robots.append(url)
            continue

        if len(result.pages) > 0:
            time.sleep(delay)

        fr = fetch(url, timeout=timeout)
        result.checked_links += 1

        if fr.error:
            result.broken.append(
                BrokenLink(source=source or start_url, target=url,
                           status=None, error=fr.error)
            )
            continue
        if not fr.ok:
            # Redirects already resolved by fetch(); a non-2xx here is genuinely
            # broken from a crawler's point of view.
            result.broken.append(
                BrokenLink(source=source or start_url, target=url, status=fr.status)
            )
            continue
        if not fr.is_html:
            continue

        doc = htmldoc.parse(fr.body)
        normalized_text = htmldoc.normalize_visible_text(doc.visible_text)
        links = _extract_links(doc, fr.final_url or url, start_url)

        record = PageRecord(
            url=fr.final_url or url,
            status=fr.status,
            title=doc.title,
            meta_description=doc.meta_description,
            content_hash=hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
            if normalized_text else "",
            word_count=len(normalized_text.split()),
            outlinks=[u for u, _ in links],
            depth=depth,
        )
        result.pages[normalize_url(record.url)] = record

        if depth < max_depth:
            for link_url, _anchor in links:
                if normalize_url(link_url) not in seen:
                    frontier.append((link_url, depth + 1, record.url))

    if frontier:
        result.limit_reached = True

    _find_duplicates(result)
    return result


def _find_duplicates(result: CrawlResult) -> None:
    """Group pages by title, meta description, and content hash separately.

    Kept separate on purpose: duplicate titles are a metadata problem, duplicate
    content is a canonicalization problem, and they need different fixes.
    """
    by_title: Dict[str, List[str]] = {}
    by_meta: Dict[str, List[str]] = {}
    by_hash: Dict[str, List[str]] = {}

    for page in result.pages.values():
        if page.title:
            by_title.setdefault(page.title.strip(), []).append(page.url)
        if page.meta_description:
            by_meta.setdefault(page.meta_description.strip(), []).append(page.url)
        # Ignore near-empty pages: two 5-word pages colliding is noise.
        if page.content_hash and page.word_count >= 50:
            by_hash.setdefault(page.content_hash, []).append(page.url)

    result.duplicate_titles = {k: v for k, v in by_title.items() if len(v) > 1}
    result.duplicate_meta = {k: v for k, v in by_meta.items() if len(v) > 1}
    result.duplicate_content = {k: v for k, v in by_hash.items() if len(v) > 1}

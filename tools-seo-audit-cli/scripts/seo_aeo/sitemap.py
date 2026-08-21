"""XML sitemap discovery, parsing, and membership checking.

Handles both <urlset> and <sitemapindex>, recursing one level into index files
(enough for real sites, bounded so a malicious/looping index can't hang us).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

from .fetch import fetch, normalize_url, origin

MAX_INDEX_CHILDREN = 25  # cap how many child sitemaps we pull from an index
MAX_URLS = 50000  # sitemap spec limit; guards against memory blowups


@dataclass
class SitemapResult:
    checked_urls: List[str] = field(default_factory=list)
    found: List[str] = field(default_factory=list)  # sitemaps that actually exist
    urls: Set[str] = field(default_factory=set)  # normalized loc values
    lastmods: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    truncated: bool = False
    # How much of the index we did and did not read, so a caller can say
    # "not found in the part I could see" instead of "not in the sitemap".
    index_children_total: int = 0
    index_children_read: int = 0

    @property
    def exists(self) -> bool:
        return bool(self.found)

    def lists(self, url: str) -> bool:
        return normalize_url(url) in self.urls


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_xml(body: str):
    """Parse sitemap XML, tolerating a BOM or leading whitespace."""
    return ET.fromstring(body.lstrip("﻿ \t\r\n"))


def _read_sitemap(url: str, result: SitemapResult, timeout: int, depth: int = 0) -> None:
    result.checked_urls.append(url)
    fr = fetch(url, timeout=timeout)

    if fr.error:
        result.errors.append(f"{url}: {fr.error}")
        return
    if not fr.ok:
        # A missing sitemap at a guessed location is not an error worth
        # reporting — only explicitly-declared ones are.
        if depth > 0 or url in result.found:
            result.errors.append(f"{url}: HTTP {fr.status}")
        return

    try:
        root = _parse_xml(fr.body)
    except ET.ParseError as exc:
        result.errors.append(f"{url}: invalid XML ({exc})")
        return

    result.found.append(url)
    root_tag = _strip_ns(root.tag).lower()

    if root_tag == "sitemapindex":
        if depth >= 1:
            result.errors.append(f"{url}: nested sitemap index deeper than one level, skipped")
            return
        children = []
        for node in root:
            if _strip_ns(node.tag).lower() != "sitemap":
                continue
            loc = node.find("{*}loc")
            if loc is None or not (loc.text or "").strip():
                continue
            children.append(loc.text.strip())
        result.index_children_total += len(children)
        if len(children) > MAX_INDEX_CHILDREN:
            result.truncated = True
            children = children[:MAX_INDEX_CHILDREN]
        result.index_children_read += len(children)
        for child in children:
            _read_sitemap(child, result, timeout, depth + 1)
        return

    if root_tag != "urlset":
        result.errors.append(f"{url}: unexpected root element '{root_tag}'")
        return

    for node in root:
        if _strip_ns(node.tag).lower() != "url":
            continue
        loc = node.find("{*}loc")
        if loc is None or not (loc.text or "").strip():
            continue
        raw_loc = loc.text.strip()
        result.urls.add(normalize_url(raw_loc))
        lastmod = node.find("{*}lastmod")
        if lastmod is not None and (lastmod.text or "").strip():
            result.lastmods[normalize_url(raw_loc)] = lastmod.text.strip()
        if len(result.urls) >= MAX_URLS:
            result.truncated = True
            return


def discover_and_read(
    site_url: str,
    declared_sitemaps: Optional[List[str]] = None,
    timeout: int = 15,
) -> SitemapResult:
    """Read sitemaps declared in robots.txt, falling back to /sitemap.xml.

    Declared sitemaps take priority; the conventional locations are only tried
    when robots.txt names none.
    """
    result = SitemapResult()
    base = origin(site_url) + "/"

    candidates = list(declared_sitemaps or [])
    if not candidates:
        candidates = [
            urljoin(base, "sitemap.xml"),
            urljoin(base, "sitemap_index.xml"),
        ]

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        _read_sitemap(candidate, result, timeout)
        # If a conventional guess worked, don't bother with the next guess.
        if result.found and not declared_sitemaps:
            break

    return result


def coverage_note(result: "SitemapResult") -> str:
    """One phrase describing how much of a sitemap we actually read."""
    if not result.truncated:
        return ""
    if result.index_children_total > result.index_children_read:
        return (f"read {result.index_children_read} of "
                f"{result.index_children_total} child sitemaps")
    return f"stopped at the first {len(result.urls)} URLs"

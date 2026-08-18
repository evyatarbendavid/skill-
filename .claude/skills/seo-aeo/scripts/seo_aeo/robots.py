"""robots.txt fetching and interpretation.

Two jobs the stdlib doesn't do in one place:
  1. allow/disallow decisions (RobotFileParser handles this)
  2. extracting `Sitemap:` directives (not exposed consistently across versions,
     so we line-scan for them ourselves)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from .fetch import USER_AGENT, fetch, origin

_SITEMAP_RE = re.compile(r"^\s*sitemap\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)

# Resource types Googlebot must be able to fetch to render the page.
_RENDER_RESOURCE_HINTS = (".css", ".js", "/css/", "/js/", "/static/", "/assets/")


@dataclass
class RobotsResult:
    url: str = ""
    exists: bool = False
    status: Optional[int] = None
    raw: str = ""
    sitemaps: List[str] = field(default_factory=list)
    error: Optional[str] = None
    _parser: Optional[RobotFileParser] = None

    def allows(self, url: str, agent: str = "*") -> bool:
        """True if `url` may be crawled. Missing/unfetchable robots.txt means
        everything is allowed, which matches how crawlers actually behave."""
        if self._parser is None:
            return True
        try:
            return self._parser.can_fetch(agent, url)
        except Exception:
            return True

    def blocks_render_resources(self) -> List[str]:
        """Disallow rules that look like they block CSS/JS Googlebot needs.

        Heuristic and deliberately conservative — reported as a warning, never
        as a hard FAIL, because only the site owner knows what those paths are.
        """
        hits = []
        for line in self.raw.splitlines():
            line = line.strip()
            if not line.lower().startswith("disallow:"):
                continue
            path = line.split(":", 1)[1].strip()
            if not path:
                continue
            lowered = path.lower()
            if any(hint in lowered for hint in _RENDER_RESOURCE_HINTS):
                hits.append(path)
        return hits


def fetch_robots(site_url: str, timeout: int = 10) -> RobotsResult:
    robots_url = urljoin(origin(site_url) + "/", "robots.txt")
    result = RobotsResult(url=robots_url)

    fr = fetch(robots_url, timeout=timeout)
    result.status = fr.status
    if fr.error:
        result.error = fr.error
        return result

    # A 404 robots.txt is normal and means "crawl everything".
    if not fr.ok:
        return result

    result.exists = True
    result.raw = fr.body
    result.sitemaps = [m.strip() for m in _SITEMAP_RE.findall(fr.body)]

    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.parse(fr.body.splitlines())
        result._parser = parser
    except Exception as exc:
        result.error = f"robots.txt parse failed: {type(exc).__name__}: {exc}"
    return result


def agent_allows(robots: RobotsResult, url: str) -> bool:
    """Check both the wildcard agent and our own UA token."""
    return robots.allows(url, "*") and robots.allows(url, USER_AGENT)

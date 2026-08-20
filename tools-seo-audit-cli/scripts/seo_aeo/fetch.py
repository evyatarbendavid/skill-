"""HTTP fetching with an explicit, inspectable redirect chain.

Redirects are followed manually rather than letting urllib do it silently,
because "no needless redirect chain to the final URL" is itself a checklist item
(A1) — we need the whole chain, not just where we landed.
"""

import gzip
import io
import ssl
import time
import zlib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

USER_AGENT = (
    "Mozilla/5.0 (compatible; seo-aeo-audit/1.0; "
    "+https://github.com/anthropics/claude-code) Python-urllib"
)

DEFAULT_TIMEOUT = 15
MAX_BODY_BYTES = 5 * 1024 * 1024  # don't pull huge assets into memory


@dataclass
class FetchResult:
    url: str
    final_url: str = ""
    status: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    redirect_chain: List[Tuple[str, int]] = field(default_factory=list)
    elapsed_ms: int = 0
    error: Optional[str] = None
    content_type: str = ""

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    @property
    def is_html(self) -> bool:
        return "html" in self.content_type.lower()

    def header(self, name: str, default: str = "") -> str:
        """Case-insensitive header lookup."""
        target = name.lower()
        for k, v in self.headers.items():
            if k.lower() == target:
                return v
        return default


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop urllib from following redirects so we can record each hop."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _build_opener(verify_tls: bool = True):
    if verify_tls:
        ctx = ssl.create_default_context()
    else:
        ctx = ssl._create_unverified_context()
    return urllib.request.build_opener(
        _NoRedirect(), urllib.request.HTTPSHandler(context=ctx)
    )


def _header(headers: Dict[str, str], name: str, default: str = "") -> str:
    """Case-insensitive header lookup.

    HTTP header names are case-insensitive and servers really do vary the case,
    so a plain dict .get() silently misses them — which previously meant gzip
    bodies were never decompressed and every content check ran on binary noise.
    """
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return default


def _decode_body(raw: bytes, headers: Dict[str, str]) -> str:
    encoding = _header(headers, "Content-Encoding").lower()
    if "gzip" in encoding or raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        except OSError:
            pass
    elif "deflate" in encoding:
        try:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        except zlib.error:
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                pass

    charset = "utf-8"
    ctype = _header(headers, "Content-Type")
    if "charset=" in ctype.lower():
        charset = ctype.lower().split("charset=", 1)[1].split(";")[0].strip()
    for candidate in (charset, "utf-8", "latin-1"):
        try:
            return raw.decode(candidate, errors="replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def fetch(
    url: str,
    method: str = "GET",
    max_redirects: int = 10,
    timeout: int = DEFAULT_TIMEOUT,
    verify_tls: bool = True,
) -> FetchResult:
    """Fetch a URL, recording every redirect hop.

    Never raises for HTTP-level problems — errors land in FetchResult.error so a
    single bad URL degrades one check instead of killing the whole audit.
    """
    result = FetchResult(url=url)
    opener = _build_opener(verify_tls)
    current = url
    started = time.time()

    for _ in range(max_redirects + 1):
        req = urllib.request.Request(
            current,
            method=method,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip",
            },
        )
        try:
            with opener.open(req, timeout=timeout) as resp:
                status = resp.status
                headers = dict(resp.headers.items())
                raw = resp.read(MAX_BODY_BYTES)
        except urllib.error.HTTPError as exc:
            # HTTPError *is* the response for 3xx/4xx/5xx — use it, don't fail.
            status = exc.code
            headers = dict(exc.headers.items()) if exc.headers else {}
            try:
                raw = exc.read(MAX_BODY_BYTES)
            except Exception:
                raw = b""
        except urllib.error.URLError as exc:
            result.error = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
            result.elapsed_ms = int((time.time() - started) * 1000)
            result.final_url = current
            return result
        except Exception as exc:  # socket timeouts, malformed URLs, bad TLS
            result.error = f"{type(exc).__name__}: {exc}"
            result.elapsed_ms = int((time.time() - started) * 1000)
            result.final_url = current
            return result

        result.redirect_chain.append((current, status))

        if status in (301, 302, 303, 307, 308):
            location = headers.get("Location") or headers.get("location")
            if not location:
                break
            current = urljoin(current, location)
            continue
        break
    else:
        result.error = f"Exceeded {max_redirects} redirects"

    result.status = status
    result.headers = headers
    result.final_url = current
    result.content_type = _header(headers, "Content-Type")
    result.elapsed_ms = int((time.time() - started) * 1000)
    if raw and (result.is_html or not result.content_type or "xml" in result.content_type
                or "text" in result.content_type or "json" in result.content_type):
        result.body = _decode_body(raw, headers)
    return result


def normalize_url(url: str) -> str:
    """Canonicalize for comparison: drop fragment, drop trailing '?',
    lowercase scheme/host, and treat '' and '/' paths as the same."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            "",  # fragment never matters for identity
        )
    )


def same_host(a: str, b: str) -> bool:
    ha, hb = urlparse(a).netloc.lower(), urlparse(b).netloc.lower()
    # Treat www and bare host as the same site for crawl purposes.
    return ha.removeprefix("www.") == hb.removeprefix("www.")


def origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

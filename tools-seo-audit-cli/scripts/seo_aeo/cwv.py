"""Core Web Vitals via the PageSpeed Insights API (field / CrUX data).

Thresholds live here as overridable constants, not baked into comparisons, so
that when Google changes them the fix is one number — and so the skill can tell
the user exactly which values it judged against.

Verified current 2026-08-17 against web.dev/articles/vitals. There is active
misinformation online claiming different numbers; see
references/seo-aeo-reference.md section 4.
"""

import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Optional

from .fetch import fetch

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

THRESHOLDS_LAST_VERIFIED = "2026-08-17"

# metric -> (good_max, needs_improvement_max). Lower is better for all three.
THRESHOLDS: Dict[str, tuple] = {
    "LCP": (2500, 4000),  # milliseconds
    "INP": (200, 500),    # milliseconds
    "CLS": (0.1, 0.25),   # unitless
}

# PSI's CrUX metric keys.
_PSI_KEYS = {
    "LCP": "LARGEST_CONTENTFUL_PAINT_MS",
    "INP": "INTERACTION_TO_NEXT_PAINT",
    "CLS": "CUMULATIVE_LAYOUT_SHIFT_SCORE",
}


@dataclass
class MetricResult:
    name: str
    p75: Optional[float] = None
    good_max: Optional[float] = None
    passes: Optional[bool] = None
    category: str = ""  # FAST / AVERAGE / SLOW as reported by CrUX

    @property
    def display(self) -> str:
        if self.p75 is None:
            return "no data"
        if self.name == "CLS":
            return f"{self.p75:.3f}"
        return f"{self.p75:.0f} ms"


@dataclass
class CWVResult:
    strategy: str = "mobile"
    has_field_data: bool = False
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    overall_category: str = ""
    error: Optional[str] = None
    origin_fallback: bool = False  # data is origin-level, not URL-level

    @property
    def passes(self) -> Optional[bool]:
        """True only if every metric with data passes. None if no data at all."""
        if not self.has_field_data:
            return None
        judged = [m for m in self.metrics.values() if m.passes is not None]
        if not judged:
            return None
        return all(m.passes for m in judged)

    def summary(self) -> str:
        if not self.has_field_data:
            return "no field data"
        return ", ".join(
            f"{name} {m.display}{'' if m.passes is None else (' ✓' if m.passes else ' ✗')}"
            for name, m in self.metrics.items()
        )


def _normalize(metric: str, raw: float) -> float:
    # PSI reports CLS as an integer scaled by 100 (e.g. 8 means 0.08).
    return raw / 100.0 if metric == "CLS" else float(raw)


def fetch_cwv(
    url: str,
    strategy: str = "mobile",
    api_key: Optional[str] = None,
    timeout: int = 60,
) -> CWVResult:
    """Fetch field CWV data. Missing data is N/A, never a failure.

    A brand-new or low-traffic page genuinely has no CrUX data — that is not a
    performance problem, and reporting it as one would be wrong.
    """
    result = CWVResult(strategy=strategy)

    params = {"url": url, "strategy": strategy, "category": "performance"}
    if api_key:
        params["key"] = api_key
    request_url = f"{PSI_ENDPOINT}?{urllib.parse.urlencode(params)}"

    fr = fetch(request_url, timeout=timeout)
    if fr.error:
        result.error = f"PageSpeed Insights request failed: {fr.error}"
        return result
    if not fr.ok:
        hint = ""
        if fr.status == 429:
            hint = " (rate limited — set PAGESPEED_API_KEY for a higher quota)"
        result.error = f"PageSpeed Insights returned HTTP {fr.status}{hint}"
        return result

    try:
        data = json.loads(fr.body)
    except json.JSONDecodeError as exc:
        result.error = f"PageSpeed Insights returned unparsable JSON: {exc}"
        return result

    if "error" in data:
        message = data["error"].get("message", "unknown error")
        result.error = f"PageSpeed Insights: {message}"
        return result

    experience = data.get("loadingExperience") or {}
    metrics_raw = experience.get("metrics") or {}

    # Fall back to origin-level data when the specific URL has too little
    # traffic — flagged, because it describes the site, not this page.
    if not metrics_raw:
        origin_experience = data.get("originLoadingExperience") or {}
        metrics_raw = origin_experience.get("metrics") or {}
        if metrics_raw:
            result.origin_fallback = True
            experience = origin_experience

    if not metrics_raw:
        result.error = "no CrUX field data for this URL or origin"
        return result

    result.has_field_data = True
    result.overall_category = experience.get("overall_category", "")

    for name, psi_key in _PSI_KEYS.items():
        good_max = THRESHOLDS[name][0]
        entry = metrics_raw.get(psi_key)
        if not entry or "percentile" not in entry:
            result.metrics[name] = MetricResult(name=name, good_max=good_max)
            continue
        value = _normalize(name, entry["percentile"])
        result.metrics[name] = MetricResult(
            name=name,
            p75=value,
            good_max=good_max,
            passes=value <= good_max,
            category=entry.get("category", ""),
        )

    return result

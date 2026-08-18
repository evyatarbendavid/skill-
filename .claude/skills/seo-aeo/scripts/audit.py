#!/usr/bin/env python3
"""SEO + AEO audit and fix tool.

Runs real diagnostics against a live URL and maps every result onto the
checklist in references/audit-checklist.md. With --fix and a local source tree,
writes the fixes that are safely unambiguous.

    python3 audit.py https://example.com/
    python3 audit.py https://example.com/ --local-dir ./site --fix --apply

Standard library only. No pip install required.
"""

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seo_aeo import accessibility, aeo, canonical, crawler, cwv, fixers, htmldoc, report, robots, sitemap, structured_data  # noqa: E402
from seo_aeo.fetch import fetch, normalize_url, origin  # noqa: E402
from seo_aeo.models import (  # noqa: E402
    FAIL,
    HUMAN_JUDGMENT,
    NA,
    PASS,
    WARN,
    AuditResult,
    Finding,
)


class Context:
    """Everything the section runners share, fetched once."""

    def __init__(self, args):
        self.args = args
        self.url = args.url
        self.page = None          # FetchResult for the target page
        self.doc = None           # parsed HtmlDoc
        self.robots = None
        self.sitemap = None
        self.crawl = None
        self.structured = None
        self.canonical = None
        self.local_dir: Optional[Path] = (
            Path(args.local_dir).resolve() if args.local_dir else None
        )


def guard(result: AuditResult, finding_id: str, title: str):
    """Decorator-ish helper: run a check, turn any exception into N/A.

    One flaky network call must never take down the whole audit.
    """

    def wrapper(fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - deliberate catch-all
            result.add(
                Finding(
                    id=finding_id,
                    title=title,
                    status=NA,
                    reason=f"check failed: {type(exc).__name__}: {exc}",
                )
            )
            result.errors.append(f"{finding_id}: {type(exc).__name__}: {exc}")
            if os.environ.get("SEO_AEO_DEBUG"):
                traceback.print_exc()
            return None

    return wrapper


# ---------------------------------------------------------------------------
# Section A - Crawlability & Indexing (GATE)
# ---------------------------------------------------------------------------

def run_section_a(ctx: Context, result: AuditResult) -> None:
    page = ctx.page

    # A1 - HTTP 200, no redirect chain
    hops = page.redirect_chain
    if page.error:
        result.add(Finding("A1", "Returns HTTP 200", FAIL,
                           detail=f"request failed: {page.error}"))
    elif page.ok and len(hops) <= 1:
        result.add(Finding("A1", "Returns HTTP 200", PASS,
                           detail=f"HTTP {page.status}, no redirects"))
    elif page.ok:
        chain = " -> ".join(f"{u} ({s})" for u, s in hops)
        result.add(Finding(
            "A1", "Returns HTTP 200", WARN,
            detail=f"reached 200 through {len(hops) - 1} redirect(s): {chain}. "
                   "Link to the final URL directly; every hop costs crawl budget.",
            evidence={"chain": chain},
        ))
    else:
        result.add(Finding("A1", "Returns HTTP 200", FAIL,
                           detail=f"HTTP {page.status} — only 200 pages get indexed"))

    if not page.ok:
        # Everything downstream needs a real page; say so once, clearly.
        for fid, title in (("A3", "Indexable directives"),
                           ("A4", "Self-referencing canonical"),
                           ("A8", "Content present in rendered DOM")):
            result.add(Finding(fid, title, NA, reason="page did not return 200"))
        return

    # A2 - robots.txt
    rb = ctx.robots
    if rb is None or rb.error:
        result.add(Finding("A2", "Not blocked in robots.txt", NA,
                           reason=(rb.error if rb else "robots.txt not checked")))
    elif not rb.exists:
        result.add(Finding("A2", "Not blocked in robots.txt", PASS,
                           detail="no robots.txt (everything is crawlable)"))
    elif not robots.agent_allows(rb, page.final_url):
        result.add(Finding(
            "A2", "Not blocked in robots.txt", FAIL,
            detail="robots.txt disallows this URL. Note a blocked page can still "
                   "appear as a bare URL, and Googlebot will never see a noindex "
                   "tag on it — use noindex, not disallow, to keep it out.",
        ))
    else:
        blocked = rb.blocks_render_resources()
        if blocked:
            result.add(Finding(
                "A2", "Not blocked in robots.txt", WARN,
                detail="URL is crawlable, but these rules may block CSS/JS "
                       f"Googlebot needs to render the page: {', '.join(blocked[:5])}",
            ))
        else:
            result.add(Finding("A2", "Not blocked in robots.txt", PASS,
                               detail="crawl allowed"))

    # A3 - noindex directives (meta and header both count)
    header_robots = page.header("X-Robots-Tag")
    meta_noindex = htmldoc.has_noindex(ctx.doc)
    header_noindex = "noindex" in header_robots.lower()
    if meta_noindex or header_noindex:
        source = "meta robots" if meta_noindex else "X-Robots-Tag header"
        result.add(Finding("A3", "Indexable directives", FAIL,
                           detail=f"noindex found via {source} — this page is "
                                  "explicitly excluded from the index"))
    else:
        result.add(Finding("A3", "Indexable directives", PASS,
                           detail="no noindex in meta or headers"))

    # A4 - canonical
    can = ctx.canonical
    if can.classification == canonical.MISSING:
        result.add(Finding("A4", "Self-referencing canonical", FAIL,
                           detail=can.detail, fixable=True))
    elif can.classification == canonical.SELF:
        result.add(Finding("A4", "Self-referencing canonical", PASS, detail=can.detail))
    elif can.classification == canonical.RELATIVE:
        result.add(Finding("A4", "Self-referencing canonical", WARN, detail=can.detail))
    else:
        result.add(Finding("A4", "Self-referencing canonical", HUMAN_JUDGMENT,
                           detail=can.detail,
                           reason="canonical points elsewhere; only you know if "
                                  "that is intended"))

    # A5 - in a sitemap
    sm = ctx.sitemap
    if sm is None:
        result.add(Finding("A5", "Listed in an XML sitemap", NA,
                           reason="sitemap check did not run"))
    elif not sm.exists:
        result.add(Finding(
            "A5", "Listed in an XML sitemap", FAIL,
            detail="no sitemap found at /sitemap.xml or declared in robots.txt",
            fixable=True,
        ))
    elif sm.lists(page.final_url):
        result.add(Finding("A5", "Listed in an XML sitemap", PASS,
                           detail=f"listed in {sm.found[0]} ({len(sm.urls)} URLs total)"))
    else:
        result.add(Finding(
            "A5", "Listed in an XML sitemap", FAIL,
            detail=f"sitemap exists ({sm.found[0]}, {len(sm.urls)} URLs) but does "
                   "not list this URL",
            fixable=True,
        ))

    # A6 - actually indexed: only Search Console can answer this
    result.add(Finding(
        "A6", "Actually indexed", NA,
        reason="requires Google Search Console access — check URL Inspection for "
               "'URL is on Google'. No tool can determine this from outside.",
    ))

    # A7 - reachable by internal links
    if ctx.crawl is None:
        result.add(Finding("A7", "Reachable by internal links", NA,
                           reason="crawl did not run"))
    else:
        inbound = ctx.crawl.inbound_links_to(page.final_url)
        if inbound:
            result.add(Finding("A7", "Reachable by internal links", PASS,
                               detail=f"linked from {len(inbound)} crawled page(s)"))
        elif ctx.crawl.page_count <= 1:
            result.add(Finding("A7", "Reachable by internal links", NA,
                               reason="only one page crawled — nothing to link from"))
        else:
            result.add(Finding(
                "A7", "Reachable by internal links", WARN,
                detail=f"no inbound links found among {ctx.crawl.page_count} crawled "
                       "pages. May be orphaned, or may just be outside the crawl depth.",
            ))

    # A8 - content in the raw DOM (JS-dependent content is a real risk)
    words = len(ctx.doc.visible_text.split())
    if words >= 100:
        result.add(Finding("A8", "Content present in rendered DOM", PASS,
                           detail=f"{words} words of text in the served HTML"))
    elif words >= 20:
        result.add(Finding(
            "A8", "Content present in rendered DOM", WARN,
            detail=f"only {words} words in the served HTML. If the real content is "
                   "rendered client-side, verify with Search Console's rendered HTML.",
        ))
    else:
        result.add(Finding(
            "A8", "Content present in rendered DOM", FAIL,
            detail=f"almost no text ({words} words) in the served HTML — content "
                   "likely depends on JavaScript, which Google renders in a second, "
                   "deferred pass that can lag or fail",
        ))


# ---------------------------------------------------------------------------
# Section B - Content & Search Intent
# ---------------------------------------------------------------------------

def run_section_b(ctx: Context, result: AuditResult) -> None:
    doc = ctx.doc

    for fid, title, why in (
        ("B1", "One primary topic per page", "needs a human read of the content"),
        ("B2", "Intent matches what already ranks",
         "requires searching the target query and comparing the top results"),
        ("B3", "Answer-first structure",
         "a machine can see structure but not whether the answer is good — "
         "see F2 for the structural signals"),
        ("B5", "Original value / first-hand experience", "needs a human read"),
        ("B7", "Complete — reader does not need to search again", "needs a human read"),
        ("B10", "Accurate and current", "needs subject-matter review"),
    ):
        result.add(Finding(fid, title, NA, reason=why))

    # B4 - heading hierarchy
    headings = accessibility.check_headings(doc)
    if headings.h1_count == 1 and not headings.skipped_levels:
        result.add(Finding("B4", "Heading hierarchy", PASS,
                           detail=f"one h1, {len(doc.headings)} headings, no skipped levels"))
    else:
        problems = []
        if headings.h1_count == 0:
            problems.append("no h1")
        elif headings.h1_count > 1:
            problems.append(f"{headings.h1_count} h1 elements (should be exactly one)")
        problems.extend(headings.skipped_levels[:3])
        result.add(Finding("B4", "Heading hierarchy", FAIL, detail="; ".join(problems)))

    # B6 - author and dates: presence only; credibility is a human call
    has_author = bool(doc.meta.get("author"))
    if ctx.structured:
        has_author = has_author or ctx.structured.has_type("Person")
    result.add(Finding(
        "B6", "Named, credible author", HUMAN_JUDGMENT if has_author else WARN,
        detail=("author signal found in markup" if has_author
                else "no author meta tag or Person markup found"),
        reason="whether the author is credible, and whether to publish a real name, "
               "is a human decision",
    ))

    # B8 - title and meta description
    title_issues = []
    if not doc.title:
        title_issues.append("no title element")
    elif len(doc.title) > 65:
        title_issues.append(f"title is {len(doc.title)} chars — likely truncated in results")
    if not doc.meta_description:
        title_issues.append("no meta description (Google will invent a snippet)")

    duplicates = []
    if ctx.crawl:
        for value, urls in ctx.crawl.duplicate_titles.items():
            if any(normalize_url(u) == normalize_url(ctx.page.final_url) for u in urls):
                duplicates.append(f"title '{value[:40]}' shared with {len(urls) - 1} other page(s)")
        for value, urls in ctx.crawl.duplicate_meta.items():
            if any(normalize_url(u) == normalize_url(ctx.page.final_url) for u in urls):
                duplicates.append(f"meta description shared with {len(urls) - 1} other page(s)")

    if not title_issues and not duplicates:
        result.add(Finding("B8", "Unique, descriptive title and description", PASS,
                           detail=f"title: {doc.title!r}"))
    else:
        result.add(Finding("B8", "Unique, descriptive title and description",
                           FAIL if title_issues else WARN,
                           detail="; ".join(title_issues + duplicates)))

    # B9 - URL slug
    from urllib.parse import urlparse
    parsed = urlparse(ctx.page.final_url)
    slug_issues = []
    if parsed.query:
        slug_issues.append(f"URL has query parameters ({parsed.query})")
    if "_" in parsed.path:
        slug_issues.append("underscores in path (hyphens are the convention)")
    if any(c.isupper() for c in parsed.path):
        slug_issues.append("uppercase characters in path")
    result.add(Finding("B9", "Descriptive URL slug", WARN if slug_issues else PASS,
                       detail="; ".join(slug_issues) or f"clean path: {parsed.path}"))

    # Duplicate content across the crawl is a canonicalization problem, not a
    # metadata one, so it is reported separately from B8.
    if ctx.crawl and ctx.crawl.duplicate_content:
        groups = list(ctx.crawl.duplicate_content.values())
        detail = "; ".join(
            f"{len(g)} pages with identical content: {', '.join(g[:3])}"
            for g in groups[:3]
        )
        result.add(Finding(
            "B1", "Duplicate content across crawled pages", HUMAN_JUDGMENT,
            detail=detail,
            reason="pick one canonical URL per duplicate group — which one is the "
                   "original is your call",
        ))


# ---------------------------------------------------------------------------
# Section C - Structured Data
# ---------------------------------------------------------------------------

def run_section_c(ctx: Context, result: AuditResult) -> None:
    sd = ctx.structured

    if sd is None:
        for fid in ("C1", "C2", "C3", "C4", "C5", "C7"):
            result.add(Finding(fid, "Structured data", NA, reason="not analyzed"))
        return

    # C1 - any JSON-LD at all
    if sd.has_any:
        result.add(Finding("C1", "JSON-LD present", PASS,
                           detail=f"{sd.raw_count} block(s), types: {', '.join(sd.types_present)}"))
    else:
        result.add(Finding("C1", "JSON-LD present", FAIL,
                           detail="no JSON-LD found", fixable=True))

    # C2 - required properties present
    if not sd.has_any:
        result.add(Finding("C2", "Validates with zero errors", NA,
                           reason="no structured data to validate"))
    elif sd.parse_errors:
        result.add(Finding(
            "C2", "Validates with zero errors", FAIL,
            detail="; ".join(sd.parse_errors) + " — unparsable JSON-LD is invisible to Google",
        ))
    elif sd.all_valid:
        notes = [n for b in sd.blocks for n in b.notes]
        result.add(Finding(
            "C2", "Validates with zero errors", PASS,
            detail="all required properties present. Confirm in the Rich Results "
                   "Test — it is the authority, this is a property-level check."
                   + (f" Notes: {notes[0]}" if notes else ""),
        ))
    else:
        result.add(Finding("C2", "Validates with zero errors", FAIL,
                           detail="; ".join(sd.missing_summary())))

    # C3 - Article family
    if sd.has_article():
        result.add(Finding("C3", "Article/BlogPosting markup", PASS,
                           detail=f"types: {', '.join(sd.types_present)}"))
    else:
        result.add(Finding(
            "C3", "Article/BlogPosting markup", WARN,
            detail="no Article/BlogPosting markup. Expected on content pages; "
                   "not applicable to a homepage or landing page.",
            fixable=True,
        ))

    # C4 - site identity
    if sd.has_type("Organization", "Person"):
        result.add(Finding("C4", "Organization or Person identity", PASS,
                           detail="site identity markup present"))
    else:
        result.add(Finding("C4", "Organization or Person identity", FAIL,
                           detail="no Organization or Person markup — this feeds "
                                  "Google's entity understanding",
                           fixable=True))

    # C5 - breadcrumbs
    if sd.has_type("BreadcrumbList"):
        result.add(Finding("C5", "BreadcrumbList", PASS, detail="present"))
    else:
        result.add(Finding("C5", "BreadcrumbList", WARN,
                           detail="no BreadcrumbList markup",
                           fixable=True))

    # C6 - markup mirrors visible content: cannot be machine-verified
    result.add(Finding(
        "C6", "Markup mirrors visible content only", NA,
        reason="comparing markup claims against what a reader actually sees needs "
               "a human. Fabricated markup is a spam-policy violation.",
    ))

    # C7 - dead rich-result types
    dead = [t for t in sd.types_present if t in structured_data.DEAD_RICH_RESULT_TYPES]
    if dead:
        details = "; ".join(f"{t} ({structured_data.DEAD_RICH_RESULT_TYPES[t]})" for t in dead)
        result.add(Finding(
            "C7", "No reliance on dead rich-result types", WARN,
            detail=f"{details}. Harmless to keep, but it will not produce a rich "
                   "result — do not count it as a ranking or citation lever.",
        ))
    else:
        result.add(Finding("C7", "No reliance on dead rich-result types", PASS,
                           detail="no deprecated rich-result types in use"))


# ---------------------------------------------------------------------------
# Section D - Core Web Vitals (GATE)
# ---------------------------------------------------------------------------

def run_section_d(ctx: Context, result: AuditResult) -> None:
    if ctx.args.skip_cwv:
        for fid, name in (("D1", "LCP"), ("D2", "INP"), ("D3", "CLS")):
            result.add(Finding(fid, f"{name} at 75th percentile", NA,
                               reason="skipped via --skip-cwv"))
        result.add(Finding("D4", "Passes on mobile and desktop", NA,
                           reason="skipped via --skip-cwv"))
        return

    key = ctx.args.pagespeed_key or os.environ.get("PAGESPEED_API_KEY")
    mobile = cwv.fetch_cwv(ctx.page.final_url, strategy="mobile", api_key=key)
    desktop = cwv.fetch_cwv(ctx.page.final_url, strategy="desktop", api_key=key)

    thresholds_note = (
        f"thresholds verified {cwv.THRESHOLDS_LAST_VERIFIED}; re-check web.dev "
        "before quoting them as current"
    )

    for fid, metric in (("D1", "LCP"), ("D2", "INP"), ("D3", "CLS")):
        good = cwv.THRESHOLDS[metric][0]
        unit = "" if metric == "CLS" else " ms"
        title = f"{metric} <= {good}{unit} (field, p75)"

        if not mobile.has_field_data:
            result.add(Finding(
                fid, title, NA,
                reason=mobile.error or "no CrUX field data. Normal for a new or "
                       "low-traffic page — it is not a performance failure.",
            ))
            continue

        m = mobile.metrics.get(metric)
        if m is None or m.p75 is None:
            result.add(Finding(fid, title, NA, reason=f"no field data for {metric}"))
        elif m.passes:
            result.add(Finding(fid, title, PASS,
                               detail=f"mobile {m.display} ({thresholds_note})"))
        else:
            result.add(Finding(fid, title, FAIL,
                               detail=f"mobile {m.display}, needs <= {good}{unit} "
                                      f"({thresholds_note})"))

    # D4 - both form factors
    if not mobile.has_field_data and not desktop.has_field_data:
        result.add(Finding("D4", "Passes on mobile and desktop", NA,
                           reason="no field data for either form factor"))
    else:
        parts = []
        if mobile.has_field_data:
            parts.append(f"mobile: {mobile.summary()}")
        if desktop.has_field_data:
            parts.append(f"desktop: {desktop.summary()}")
        both_pass = (mobile.passes is not False) and (desktop.passes is not False)
        fallback = " (origin-level data, not this URL)" if mobile.origin_fallback else ""
        result.add(Finding("D4", "Passes on mobile and desktop",
                           PASS if both_pass else FAIL,
                           detail="; ".join(parts) + fallback))

    for fid, title in (
        ("D5", "LCP image optimized"),
        ("D6", "No layout shift sources"),
        ("D7", "Minimal blocking JS"),
        ("D8", "Lighthouse used only to diagnose D1-D3"),
    ):
        result.add(Finding(fid, title, NA,
                           reason="diagnostic — use PageSpeed Insights / Lighthouse "
                                  "on the failing metric above"))


# ---------------------------------------------------------------------------
# Section E - Accessibility & Mobile
# ---------------------------------------------------------------------------

def run_section_e(ctx: Context, result: AuditResult) -> None:
    doc, page = ctx.doc, ctx.page

    result.add(Finding(
        "E1", "Mobile parity with desktop", NA,
        reason="requires fetching as Googlebot Smartphone and diffing — mobile-first "
               "indexing makes the mobile version the source of truth",
    ))

    if doc.has_viewport:
        result.add(Finding("E2", "Responsive viewport", PASS,
                           detail=f"viewport: {doc.meta.get('viewport')}"))
    else:
        result.add(Finding("E2", "Responsive viewport", FAIL,
                           detail="no viewport meta tag — the page will not render "
                                  "correctly on mobile"))

    if accessibility.check_https(page.final_url):
        mixed = accessibility.check_mixed_content(doc, page.final_url)
        if mixed:
            result.add(Finding("E3", "HTTPS without mixed content", FAIL,
                               detail=f"{len(mixed)} insecure subresource(s): {mixed[0]}"))
        else:
            result.add(Finding("E3", "HTTPS without mixed content", PASS,
                               detail="served over HTTPS, no http:// subresources found"))
    else:
        result.add(Finding("E3", "HTTPS without mixed content", FAIL,
                           detail="page is not served over HTTPS"))

    semantic_issues = accessibility.check_semantics(doc)
    result.add(Finding("E4", "Semantic HTML and landmarks",
                       WARN if semantic_issues else PASS,
                       detail="; ".join(semantic_issues) or "main and nav landmarks present"))

    images = accessibility.check_images(doc)
    if images.total == 0:
        result.add(Finding("E5", "Images have meaningful alt text", NA,
                           reason="no images on the page"))
    elif images.ok:
        result.add(Finding("E5", "Images have meaningful alt text", PASS,
                           detail=f"{images.with_alt} with alt, {images.decorative} "
                                  f"marked decorative, of {images.total}"))
    else:
        result.add(Finding(
            "E5", "Images have meaningful alt text", FAIL,
            detail=f"{len(images.missing)} of {images.total} images have no alt "
                   f"attribute (e.g. {images.missing[0]})",
        ))

    for fid, title in (
        ("E6", "Keyboard operable"),
        ("E7", "Sufficient color contrast"),
        ("E8", "Accessible names / ARIA / form labels"),
        ("E10", "Screen-reader spot check"),
    ):
        result.add(Finding(fid, title, NA,
                           reason="needs a rendered page and a human — static HTML "
                                  "cannot settle it"))

    if doc.lang:
        result.add(Finding("E9", "lang attribute set", PASS, detail=f'lang="{doc.lang}"'))
    else:
        result.add(Finding("E9", "lang attribute set", FAIL,
                           detail="no lang attribute on the html element"))


# ---------------------------------------------------------------------------
# Section F - AEO readiness
# ---------------------------------------------------------------------------

def run_section_f(ctx: Context, result: AuditResult) -> None:
    # F1 - retrievability is Section A, restated as the AEO prerequisite.
    # Only the failures that genuinely make a page unretrievable count here:
    # a 4xx/5xx, a robots block, a noindex, or no content in the served HTML.
    # Missing from a sitemap (A5) or weak internal linking (A7) hurt discovery
    # but do not stop an engine that has the URL from fetching and citing it.
    BLOCKING = {"A1", "A2", "A3", "A8"}
    blocking_fails = [f for f in result.findings
                      if f.id in BLOCKING and f.status == FAIL]
    discovery_fails = [f for f in result.findings
                       if f.section == "A" and f.status == FAIL
                       and f.id not in BLOCKING]

    if blocking_fails:
        result.add(Finding(
            "F1", "Retrievable by AI engines", FAIL,
            detail=f"blocked by {', '.join(f.id for f in blocking_fails)}. An AI "
                   "cannot cite a page it cannot retrieve — for Google's AI "
                   "features this is the whole official requirement.",
        ))
    elif discovery_fails:
        result.add(Finding(
            "F1", "Retrievable by AI engines", WARN,
            detail="retrievable, but discovery is weakened by "
                   f"{', '.join(f.id for f in discovery_fails)}. An engine that "
                   "has the URL can fetch it; fewer will find it in the first place.",
        ))
    else:
        result.add(Finding("F1", "Retrievable by AI engines", PASS,
                           detail="crawlable and indexable — the prerequisite is met"))

    shape = aeo.analyze_answer_shape(ctx.doc)
    raw = aeo.analyze_raw_structure(ctx.page.body)

    # F2 - extractable chunks
    chunk_signals = []
    if raw["list_items"] >= 3:
        chunk_signals.append(f"{raw['list_items']} list items")
    if raw["tables"]:
        chunk_signals.append(f"{raw['tables']} table(s)")
    if shape.total_headings >= 2:
        chunk_signals.append(f"{shape.total_headings} subheadings")

    if chunk_signals:
        result.add(Finding(
            "F2", "Extractable answer chunks", PASS,
            detail="structural signals present: " + ", ".join(chunk_signals)
                   + ". Whether the answers themselves are self-contained is a human read.",
        ))
    else:
        result.add(Finding(
            "F2", "Extractable answer chunks", WARN,
            detail="few structural signals (headings, lists, tables). Retrieval "
                   "systems extract these shapes most cleanly.",
        ))

    result.add(Finding(
        "F3", "One clear claim per passage with specifics", NA,
        reason="needs a human read — a machine cannot tell a groundable claim from "
               "vague prose",
    ))

    # F4 - question-phrased headings
    if shape.question_headings:
        result.add(Finding(
            "F4", "Question-phrased content", PASS,
            detail=f"{len(shape.question_headings)} of {shape.total_headings} "
                   f"subheadings are question-shaped (e.g. {shape.question_headings[0]!r})",
        ))
    elif shape.total_headings:
        result.add(Finding(
            "F4", "Question-phrased content", WARN,
            detail=f"none of {shape.total_headings} subheadings are phrased as "
                   "questions. Query fan-out matches passages against sub-questions.",
        ))
    else:
        result.add(Finding("F4", "Question-phrased content", NA,
                           reason="no subheadings to assess"))

    result.add(Finding(
        "F5", "Trust signals present", HUMAN_JUDGMENT,
        detail="named author, credentials, primary sources, and a visible "
               "last-updated date",
        reason="see B6 — presence can be detected, credibility cannot",
    ))

    result.add(Finding(
        "F6", "External corroboration", NA,
        reason="requires off-site research into who references this content. A new "
               "site starts with none — expect AI citation to lag any ranking.",
    ))

    # F7 - unproven levers
    llms = None
    try:
        llms = aeo.check_llms_txt(ctx.page.final_url)
    except Exception:
        pass
    if llms and llms.present:
        detail = ("/llms.txt is present. Harmless, but as of 2026-08 no major AI "
                  "provider has confirmed reading it for citation, and adoption is "
                  "~10% of domains. Do not count it as a lever.")
    else:
        detail = ("no /llms.txt — that is fine. No major AI provider has confirmed "
                  "reading it for web citation.")
    result.add(Finding("F7", "Not relying on unproven levers", PASS, detail=detail))


# ---------------------------------------------------------------------------
# Section P - proof artifacts
# ---------------------------------------------------------------------------

def run_section_p(ctx: Context, result: AuditResult) -> None:
    result.add(Finding("P1", "First-page ranking screenshot", NA,
                       reason="Search Console -> Performance, filtered to the target "
                              "query, average position <= ~10"))
    result.add(Finding("P2", "AI citation screenshot", NA,
                       reason="capture a ChatGPT / Perplexity / AI Overview answer "
                              "linking to the page. Not guaranteed, and typically "
                              "lags the ranking."))
    result.add(Finding("P3", "Technical health evidence", NA,
                       reason="Rich Results Test valid + CWV green on both form "
                              "factors + indexed with zero manual actions"))


# ---------------------------------------------------------------------------
# Fix planning
# ---------------------------------------------------------------------------

def plan_fixes(ctx: Context, result: AuditResult) -> None:
    plan = fixers.FixPlan()
    local = ctx.local_dir

    # A5 - sitemap
    a5 = result.get("A5")
    if a5 and a5.status == FAIL:
        urls = sorted({p.url for p in ctx.crawl.pages.values()}) if ctx.crawl else []
        if ctx.page.final_url not in urls:
            urls.append(ctx.page.final_url)
        item = fixers.plan_sitemap(plan, local, urls, finding_id="A5")
        if item:
            a5.fixable = True

    # A4 - canonical, only when there is no tag at all
    a4 = result.get("A4")
    if a4 and a4.status == FAIL and ctx.canonical.auto_fixable:
        fixers.plan_canonical(plan, local, ctx.page.final_url, ctx.page.final_url,
                              finding_id="A4")

    # C1/C4 - JSON-LD identity, and C3 Article
    known = {
        "url": ctx.page.final_url,
        "headline": ctx.doc.title or "",
        "name": ctx.doc.title or "",
    }
    c4 = result.get("C4")
    if c4 and c4.status == FAIL:
        fixers.plan_jsonld(plan, local, ctx.page.final_url, "organization",
                           known=known, finding_id="C4")
    c3 = result.get("C3")
    if c3 and c3.status == WARN and ctx.structured and not ctx.structured.has_article():
        fixers.plan_jsonld(plan, local, ctx.page.final_url, "article",
                           known=known, finding_id="C3")

    if ctx.args.apply:
        plan.apply_all()

    result.fixes = [item.to_dict() for item in plan.items]
    result.meta["fix_refusals"] = plan.refusals
    result.meta["fixes_applied"] = bool(ctx.args.apply)

    for item in plan.items:
        finding = result.get(item.finding_id)
        if finding and item.applied:
            finding.fixed = True


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_audit(args) -> AuditResult:
    ctx = Context(args)
    result = AuditResult(url=args.url)

    ctx.page = fetch(args.url, timeout=args.timeout)
    result.final_url = ctx.page.final_url

    if ctx.page.error and not ctx.page.status:
        result.add(Finding("A1", "Returns HTTP 200", FAIL,
                           detail=f"could not reach the URL: {ctx.page.error}"))
        result.errors.append(f"fetch failed: {ctx.page.error}")
        return result

    ctx.doc = htmldoc.parse(ctx.page.body or "")
    if ctx.doc.parse_error:
        result.errors.append(f"HTML parse warning: {ctx.doc.parse_error}")

    guard(result, "A2", "Not blocked in robots.txt")(
        lambda: setattr(ctx, "robots", robots.fetch_robots(args.url, timeout=args.timeout))
    )
    guard(result, "A5", "Listed in an XML sitemap")(
        lambda: setattr(ctx, "sitemap", sitemap.discover_and_read(
            args.url,
            declared_sitemaps=ctx.robots.sitemaps if ctx.robots else None,
            timeout=args.timeout,
        ))
    )
    guard(result, "C1", "JSON-LD present")(
        lambda: setattr(ctx, "structured", structured_data.analyze(ctx.doc.jsonld_raw))
    )
    ctx.canonical = canonical.check(ctx.doc, ctx.page.final_url)

    if args.max_pages > 0:
        guard(result, "A7", "Reachable by internal links")(
            lambda: setattr(ctx, "crawl", crawler.crawl(
                ctx.page.final_url,
                robots=ctx.robots,
                max_pages=args.max_pages,
                max_depth=args.max_depth,
                timeout=args.timeout,
            ))
        )

    for runner in (run_section_a, run_section_b, run_section_c,
                   run_section_d, run_section_e, run_section_f, run_section_p):
        try:
            runner(ctx, result)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{runner.__name__}: {type(exc).__name__}: {exc}")
            if os.environ.get("SEO_AEO_DEBUG"):
                traceback.print_exc()

    # Broken links are reported, never fixed: where a link should point is a
    # content decision.
    if ctx.crawl and ctx.crawl.broken:
        for broken in ctx.crawl.broken[:10]:
            status = broken.status or broken.error
            result.add(Finding(
                "A7", "Broken internal link", HUMAN_JUDGMENT,
                detail=f"{broken.source} -> {broken.target} ({status})",
                reason="where this link should point is a content decision",
            ))

    if args.fix:
        try:
            plan_fixes(ctx, result)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"fix planning failed: {type(exc).__name__}: {exc}")
            if os.environ.get("SEO_AEO_DEBUG"):
                traceback.print_exc()

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit.py",
        description="SEO + AEO audit and fix tool (standard library only).",
        epilog="Auditing is read-only. Fixing writes to --local-dir and requires --apply.",
    )
    parser.add_argument("url", help="URL to audit")
    parser.add_argument("--local-dir", help="site source root; required for --fix")
    parser.add_argument("--fix", action="store_true",
                        help="plan safe auto-fixes (dry-run unless --apply)")
    parser.add_argument("--apply", action="store_true",
                        help="actually write the planned fixes")
    parser.add_argument("--max-pages", type=int, default=25,
                        help="crawl page limit (default 25; 0 disables the crawl)")
    parser.add_argument("--max-depth", type=int, default=2,
                        help="crawl depth limit (default 2)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--diffs", action="store_true",
                        help="print full unified diffs for planned fixes")
    parser.add_argument("--skip-cwv", action="store_true",
                        help="skip the PageSpeed Insights call")
    parser.add_argument("--pagespeed-key", help="or set PAGESPEED_API_KEY")
    parser.add_argument("--timeout", type=int, default=15, help="per-request timeout")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if not args.url.lower().startswith(("http://", "https://")):
        args.url = "https://" + args.url

    # Writing without an explicit target, or applying without planning, are the
    # two ways this tool could damage something. Refuse both up front.
    if args.fix and not args.local_dir:
        print("error: --fix needs --local-dir pointing at the site's source tree.\n"
              "Fixes are file writes; a live URL is not enough.", file=sys.stderr)
        return 2
    if args.apply and not args.fix:
        print("error: --apply only makes sense together with --fix.", file=sys.stderr)
        return 2
    if args.local_dir and not Path(args.local_dir).is_dir():
        print(f"error: --local-dir '{args.local_dir}' is not a directory.", file=sys.stderr)
        return 2

    result = run_audit(args)

    if args.json:
        print(report.render_json(result))
    else:
        print(report.render_text(result))
        if args.diffs:
            diffs = report.render_diffs(result)
            if diffs:
                print(diffs)

    return 1 if result.gate_failed() else 0


if __name__ == "__main__":
    sys.exit(main())

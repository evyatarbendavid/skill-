# Live verification map

A skill file cannot update itself. This document is the mechanism that keeps the
skill honest instead: it says exactly **which facts to re-check before asserting
them**, and how.

## The rule

> Before you state a volatile fact as current, verify it live. Then **say which
> facts you verified and which you took from the static reference.**

## Stable vs. volatile

| Fact category | Status | Why |
|---|---|---|
| Crawl → index → serve three-stage model | **Stable** | Structural. Unchanged for years. |
| HTTP 200 requirement for indexing | **Stable** | Structural. |
| `robots.txt` controls crawling, `noindex` controls indexing | **Stable** | Structural; the classic misconfiguration is timeless. |
| How `rel="canonical"` works mechanically | **Stable** | Structural. |
| Sitemap format and purpose | **Stable** | XML sitemap spec is not moving. |
| JSON-LD syntax; Schema.org vocabulary basics | **Stable** | Vocabulary is additive. |
| Mobile-first indexing | **Stable** | Fully rolled out. |
| E-E-A-T as a framework; "who/how/why" | **Stable** | Conceptual. |
| Answer-first structure helping extraction | **Stable** | [CONSENSUS], but not date-bound. |
| **CWV metric set and numeric thresholds** | **VOLATILE** | Metrics changed in 2024 (FID→INP); thresholds are actively misreported online. |
| **Which structured-data types yield rich results** | **VOLATILE** | Google prunes types regularly (2023, 2025, 2026). |
| **How AI Overviews / AI Mode select and cite** | **HIGHLY VOLATILE** | Changed materially in 2025 and again in July 2026. |
| **Whether AI answers are the default Search surface** | **HIGHLY VOLATILE** | The July-2026 default rollout is the single least-stable claim in this skill. |
| **`llms.txt` adoption / whether any provider reads it** | **VOLATILE** | Could change with one vendor announcement. |
| **Core update cadence and recent updates** | **VOLATILE** | By definition ongoing. |
| **Perplexity / ChatGPT Search crawler and retrieval behavior** | **VOLATILE** | Vendor-controlled, undocumented, changes quietly. |

## Authoritative sources, in priority order

1. `developers.google.com/search` — Search Central docs and blog. **Ground truth
   for anything Google.**
2. `web.dev` — Core Web Vitals definitions and thresholds. **Ground truth for CWV.**
3. `schema.org` — vocabulary itself (note: Schema.org defining a type says
   nothing about whether Google renders a rich result for it).
4. `status.search.google.com` — ranking/indexing incidents.
5. Reputable SEO trade press for *very recent* rollouts, when primary docs lag:
   Search Engine Land, Search Engine Roundtable, Search Engine Journal.

**Prefer sources published in the last ~90 days for any "current state" claim,
and note the publish date in your answer.** A 2024 blog post confidently
describing "how AI Overviews work" is not evidence about today.

## Ready-made queries

```
"Core Web Vitals" thresholds site:web.dev
Core Web Vitals new metric 2026
structured data deprecated OR retired site:developers.google.com
"rich results" removed 2026 site:developers.google.com
"AI Overviews" OR "AI Mode" how it works site:developers.google.com
Google AI Mode default search results rollout
llms.txt adoption OR support 2026
Google core update site:developers.google.com/search/blog
```

## Traps

- **A search result agreeing with a wrong number is not confirmation.** SEO
  content farms copy each other. There is currently false information
  circulating about CWV thresholds (fake 0.08 CLS, a fake FCP Core Web Vital,
  a fake January 2026 deadline). Only `web.dev` and Google's own docs settle it.
- **Absence of a Google blog post does not mean nothing changed.** The May 2026
  FAQPage removal was shipped as a quiet documentation label update with no
  announcement. Check the docs page itself, not just the blog.
- **Vendor marketing about AI citation is not evidence.** Treat any "we got
  clients cited" claim as [UNCERTAIN].
- **Do not let the static reference override a live finding.** If a live check
  from a primary source contradicts `seo-aeo-reference.md`, the live source
  wins — tell the user, and flag that the reference needs updating.

## When the reference goes stale

`seo-aeo-reference.md` carries a `Last verified` date at the top. If it is more
than ~90 days old:

1. Re-verify every VOLATILE row above before using any of it.
2. Tell the user the reference is past its verification window.
3. Offer to update the reference file with what you found — including bumping
   the `Last verified` date. That is how this skill actually stays current.

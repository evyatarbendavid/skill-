# SEO & AEO Standards for This Project

> Drop this file as `CLAUDE.md` in the project root. If a `CLAUDE.md`
> already exists, paste this in as a section instead of overwriting it.
> Claude Code loads this automatically every session — no install step.

This project must satisfy two layers of search visibility, always
together, never one instead of the other:

1. **SEO** — classic technical + on-page optimization so Google/Bing can
   crawl, index, and rank pages.
2. **AEO/GEO** (Answer/Generative Engine Optimization) — structuring
   content so AI answer engines (Google AI Overviews, ChatGPT, Perplexity,
   Copilot, Gemini, Claude) can extract, trust, and cite it.

Whenever you build, edit, or review a page on this project — even if not
explicitly asked to "do SEO" — hold it to the standard below before
calling it done. Treat this as equally binding as any other coding
convention in this file.

---

## 0. Refresh before you rely on any number below

Search-engine and AI-answer-engine behavior shifts every few months —
faster than this file gets manually updated. **Before a real audit (not
every tiny edit), run 3–5 web searches**, e.g.:

- "Google Search Central ranking update [current month year]"
- "Core Web Vitals thresholds [current year]" — confirm the LCP/INP/CLS
  numbers in section 3 haven't moved
- "[AI platform] AI Overviews citation best practices [current year]"
- "schema.org structured data changes [current year]"

If you find something that supersedes a detail here, **edit this file in
place** and add `Verified: [date] — [what changed]` under that section.
That's what keeps this file actually current instead of frozen at
whatever it said when it was written (mid-2026).

---

## 1. Crawlability & Indexing

- `robots.txt` exists, returns 200, and doesn't block pages that should
  be indexed.
- `sitemap.xml` exists, is valid, referenced from `robots.txt`, and lists
  every canonical page — no noindex'd or redirected URLs inside it.
- Every indexable page has a **self-referencing canonical tag**. Genuine
  duplicates (filter/sort variants, print views) canonicalize to the
  primary version instead.
- No conflicting signals (a page that's both `noindex` and present in the
  sitemap).
- URLs: lowercase, hyphens not underscores, no unnecessary query params,
  stable over time.
- Redirects: single-hop only — collapse chains (A→B→C becomes A→C).
- If client-side rendered, confirm content that matters for ranking is in
  the initial HTML a crawler sees, not only injected after hydration —
  the single most common technical-SEO failure on modern React/Next.js
  sites.
- HTTPS everywhere, no mixed content, one canonical host (http→https,
  www↔non-www redirect, don't just dual-serve).

## 2. On-Page Fundamentals

- Unique `<title>` per page, ~50–60 chars, no duplication across pages.
- Unique meta description per page, ~140–160 chars — written like ad copy
  for CTR, not a keyword dump (doesn't directly affect ranking).
- Exactly one `<h1>` per page, matching real page intent.
- Logical heading hierarchy, H1→H2→H3, no skipped levels, never used
  purely for visual styling.
- Internal link anchor text describes the destination, not "click here."
- `alt` text: descriptive and specific, not keyword-stuffed. Decorative
  images get `alt=""` (empty, not missing).
- Images: modern formats (WebP/AVIF), responsive `srcset`, explicit
  `width`/`height` (prevents layout shift), lazy-load only below the
  fold — never lazy-load the LCP hero image.

## 3. Core Web Vitals

Measured at the 75th percentile over a rolling 28-day window of real
user data, not a single lab run:

| Metric | Measures | Good |
|---|---|---|
| LCP (Largest Contentful Paint) | Loading speed | < 2.5s |
| INP (Interaction to Next Paint) | Responsiveness, every interaction in the session | < 200ms |
| CLS (Cumulative Layout Shift) | Visual stability | < 0.1 |

All three need to be "good" at p75 — two good and one "needs improvement"
still fails overall.

- **LCP**: preload hero image/font, don't lazy-load above-the-fold
  content, minimize render-blocking CSS/JS.
- **INP**: the one that trips up heavy client-side interactivity — 3D
  effects, animated component libraries, sticky headers, faceted
  filtering. Break up long JS tasks (>50ms), defer non-critical scripts,
  don't run expensive animation work on the main thread during input.
- **CLS**: explicit `width`/`height`/`aspect-ratio` on every image and
  embed, reserve space for dynamic content, watch web-font swap behavior.

*(There's 2026 SEO-blog noise claiming Google tightened LCP to 2.0s —
that does not match Google's own documentation. 2.5s/200ms/0.1 is
correct as of this writing; re-verify per section 0.)*

## 4. Structured Data (Schema.org / JSON-LD)

- Match schema type to what's actually on the page: `Organization`/
  `WebSite` sitewide, `BreadcrumbList` for nav, then content-specific —
  `Product`, `Article`, `LocalBusiness`.
- **`FAQPage` and `HowTo` no longer produce rich results.** HowTo was
  deprecated Aug/Sep 2023; FAQ rich results were restricted in Aug 2023
  and **fully removed for all sites on 7 May 2026** — including the
  government/health sites that kept them after 2023. Google also retired
  seven more types in June 2025 (Book Actions, Course Info, Claim Review,
  Estimated Salary, Learning Video, Special Announcement, Vehicle
  Listing). The markup stays valid Schema.org and Google may still read it
  for page understanding, so existing markup is harmless — but do not add
  it expecting SERP real estate, and never let it substitute for real
  visible Q&A content. Assume the pruning continues; re-verify any type
  before recommending it for its rich result.
  `Verified: 2026-08-18 — FAQPage fully removed May 2026; HowTo since 2023.`
- **Never mark up content that isn't visibly on the page.** Mismatched
  schema (e.g. FAQPage schema for questions rendered nowhere a user can
  see) reads as a manipulation signal to Google and undermines trust for
  AI extraction too. This is the most common self-inflicted schema bug.
- Validate JSON-LD is syntactically valid — one typo breaks the block
  silently, with no visible error to a user.

## 5. AEO/GEO — Getting Cited by AI Answer Engines

AEO is a layer on top of solid SEO, not a replacement for it — Google's
AI Overviews mostly pull from pages that already rank top-10 organically.
Fix sections 1–4 first.

- **The unit that gets cited is a passage, not the page** — a definition,
  stat, comparison, step, or recommendation. Audit at section level.
- Open every answerable section with a **direct, self-contained answer in
  ~40–60 words** before supporting detail or story.
- **Sequential heading hierarchy** (H2→H3→H4) mirroring the real question
  flow, not visual design choices.
- Prefer **lists, tables, comparisons** over prose wherever content is
  inherently comparative or sequential.
- FAQ sections mapped to **real questions people actually ask** (People
  Also Ask, forums, real support questions) — not invented ones that
  exist only to hang FAQ schema on.
- Cover a topic as a **cluster of related sub-questions** — Google's AI
  systems run "query fan-out" (related searches) before composing an
  answer, so comprehensive neighborhood coverage beats one deep answer to
  a single query.
- **E-E-A-T**: real author bios with actual credentials (not generic
  "Team" bylines), original data or genuine expert commentary, and
  third-party validation (reviews/profiles on relevant platforms) all
  raise the odds of being the cited source over a content-farm summary.
- **Freshness matters more for AEO than classic SEO**: for
  commercial/evaluation-intent content, the large majority of AI
  citations go to pages updated within the past year, a majority within
  six months. Give pricing/program/comparison pages a real "last updated"
  habit, not just a static date stamp.
- Platform notes (verify before trusting — this shifts fast): Google AI
  Overviews leans on top-10 organic + snippable structure; Perplexity
  rewards freshness/authority/multi-channel presence; Copilot leans on
  LinkedIn for B2B; Claude prefers long-form comprehensive guides; Gemini
  factors in multimodal content.
- **llms.txt**: low priority. As of 2026, adoption is low, no major AI
  provider has committed to using it for citations, and most AI search
  crawlers skip it and crawl HTML directly. It *does* have real, observed
  use by coding agents/IDE tools (Claude Code, Cursor, etc.) fetching
  `/llms.txt` on documentation sites — relevant if this project is
  docs-heavy, low priority otherwise. Cheap to add (~1 hour); don't treat
  it as a citation hack or let it displace time better spent above.

## 6. Hebrew / RTL Specifics (skip if not applicable)

- `<html lang="he" dir="rtl">` at root — check nested components too;
  some LTR-authored component libraries hardcode their own internal
  `dir`. Each language version of a multilingual site needs its own
  correct `lang`/`dir` pair.
- **Bidi bugs**: numbers, English brand names, or embedded LTR content
  inside Hebrew text can render in the wrong visual order. Wrap in
  `<bdi>` or set `dir="auto"` on mixed-content/user-generated fields.
- URL slugs: pick Latin (`/programs/beginner-calisthenics/`) or Hebrew
  slugs and stay consistent site-wide — don't mix.
- Write titles/meta descriptions in **natural Hebrew** the way an
  Israeli user actually searches, not a translated English SEO template.
  JSON-LD `name`/`description` should match the page's actual displayed
  language.
- Local search: `LocalBusiness` schema with Israeli address/phone format
  if relevant, `hreflang="he-IL"` if targeting Israel specifically vs.
  Hebrew speakers generally, and verify rankings from an
  Israel-geolocated search, not a global default.
- **A real opportunity, not just a constraint**: AI answer engines have
  far less well-structured Hebrew training/citation data than English. A
  Hebrew page that actually follows section 5 above is competing against
  a much thinner field of well-optimized Hebrew competitors than the same
  content would face in English.

## 7. Content Quality & Bugs (the "boring but costly" category)

- **Duplicate content at scale**: the biggest risk on any
  programmatically-generated set of pages (e.g. a large library of
  workout/exercise pages built from a template). If two pages differ only
  by a swapped noun/number and share 90%+ of their text, search engines
  may index only one. Give each templated page genuinely unique value —
  specific instructions, unique media, real FAQ variation — not a
  find-and-replace of the name. Spot-check a random sample rather than
  reading every page.
- **URL-level duplicates**: http/https, www/non-www, trailing-slash
  variants should 301-redirect to one canonical URL, not independently
  render the same content.
- **Broken/orphan links**: broken internal links, redirect chains
  reintroduced during content reorganization, and orphan pages (live but
  unreachable from any nav/sitemap/internal link — cross-check the
  sitemap against actual link structure to find these).
- **Navigation/transition consistency**: nav items or footer structure
  that differ page-to-page without reason, broken breadcrumb trails,
  dead-end pages with no next action, animation/route-transition state
  leaking between pages (relevant with 3D/animated component libraries),
  and RTL/LTR mixing bugs on dynamically injected components (modals,
  toasts) that don't inherit the page's `dir`.
- **Data validation at scale**: no leaked placeholder content (`Lorem
  ipsum`, `TODO`, `undefined`, untranslated strings on a Hebrew page), no
  broken image paths, no accidental duplicate IDs/slugs (a UX bug and a
  duplicate-content SEO issue at once), consistent field formatting
  across generated content.
- Several of the above are accessibility bugs first, SEO/AEO bugs
  second — fixing them is a two-for-one.

---

## Workflow When Asked to Audit or Fix SEO/AEO

1. Refresh (section 0) if it's a real audit, not a one-line edit.
2. Scope: live URL or local build? Which language(s)?
3. Check sections 1–7 above.
4. Report as a severity-ranked punch list (Critical / High / Medium /
   Low), each item with *why it matters* (ranking vs. AI-citation vs.
   UX), not a flat dump.
5. Offer to implement fixes directly in code; confirm before any
   multi-file bulk change (find/replace across templates, URL
   restructuring).
6. After fixing, re-check the specific items — don't just assume the fix
   worked.

---
name: seo-aeo
description: Apply Google's actual ranking rules and AI answer-engine citation principles to any website work. Use whenever building, writing, reviewing, or fixing a web page or site — and whenever the user mentions SEO, AEO, GEO, ranking, Google, search visibility, being cited by AI, Core Web Vitals, LCP, INP, CLS, schema markup, structured data, JSON-LD, sitemaps, canonical URLs, robots.txt, meta descriptions, crawling, or indexing. Also use when someone asks why a page is not ranking, not indexed, or not appearing in AI answers, when they paste a URL or page code and ask for a review, and when writing content meant to be found in search or quoted by ChatGPT, Perplexity, or Google AI Overviews.
---

# SEO + AEO

Two things every page needs, together, never one instead of the other:

- **SEO** — Google and Bing can crawl it, index it, and rank it.
- **AEO/GEO** — AI answer engines (Google AI Overviews and AI Mode, ChatGPT,
  Perplexity, Copilot, Gemini, Claude) can extract, trust, and cite it.

Apply this whenever you touch a page, even if nobody said the words "SEO."
A page that ships without it is a page that has to be fixed later.

## Two things this skill never claims

1. **Google does not guarantee crawling, indexing, or ranking** — its own
   words, and true even for a page that follows every rule here.
2. **Nothing forces an AI engine to cite you.** Retrieval is
   non-deterministic and proprietary. Everything below raises the odds;
   nothing sets them to 1.

What you can do is remove every technical reason to be excluded. Say it
that way. Anyone promising a position by a date is selling certainty that
doesn't exist.

## Before quoting any number

Search behavior shifts every few months — faster than this file updates.
Some facts here are stable; some are not. Before you state a **volatile**
fact as current, verify it:

| Stable — trust this file | Volatile — verify before asserting |
|---|---|
| Crawl → index → serve model | Core Web Vitals thresholds |
| Only HTTP 200 gets indexed | Which schema types still yield rich results |
| robots.txt controls crawling, not indexing | How AI Overviews select and cite |
| How canonical / sitemaps work | Anything about `llms.txt` |
| JSON-LD syntax, what E-E-A-T means | The current core-update situation |

Check `developers.google.com/search` and `web.dev` first — they settle it.
Say which facts you verified live and which came from this file.

Queries that get there fast:

```
"Core Web Vitals" thresholds site:web.dev
structured data deprecated OR retired site:developers.google.com
"AI Overviews" OR "AI Mode" how it works site:developers.google.com
Google core update site:developers.google.com/search/blog
```

Two traps. **A search result agreeing with a number is not confirmation** —
SEO content farms copy each other, so a wrong figure propagates across a
hundred pages that all look like independent sources. Only the primary docs
settle it. And **no announcement does not mean no change**: the May 2026
FAQPage removal shipped as a quiet documentation edit with no blog post, so
check the docs page itself, not just the blog.

**Baseline verified 2026-08-18.** Past ~90 days, treat every volatile row as
unconfirmed.

> **Known false claims circulating in SEO blogs — do not repeat:** that
> Google tightened LCP to 2.0s, cut CLS to 0.08, added an "FCP" Core Web
> Vital, or set a January 2026 compliance deadline. None of these appear in
> Google's documentation.

## The gates — nothing else matters until these pass

A page failing any of these cannot rank, no matter how good the content is.

1. **Returns HTTP 200.** Only 200 gets indexed. Not 3xx, 4xx, 5xx, and not
   a "soft 404" (a 200 page that says "not found").
2. **Not blocked in `robots.txt`** — and neither are the CSS/JS files
   needed to render it.
3. **No `noindex`** in meta robots or the `X-Robots-Tag` header.
4. **Content is in the served HTML.** The single most common failure on
   React/Next.js sites: content that only appears after hydration. Google
   renders JS, but on a second deferred pass that can lag or fail. Use SSR
   or static generation. To check, fetch the raw URL and look for the real
   headings and text in what comes back.
5. **Core Web Vitals pass** — all three, at the 75th percentile of real
   users, on mobile and desktop separately.

`robots.txt` controls **crawling**, not indexing. A blocked URL can still
appear in results as a bare link — and because Googlebot never fetched it,
it will never see a `noindex` on that page. To keep a page out of the
index: allow crawling, use `noindex`.

## Core Web Vitals

| Metric | Measures | Good |
|---|---|---|
| **LCP** | Loading — when the largest element renders | ≤ 2.5s |
| **INP** | Responsiveness — every interaction, not just the first | ≤ 200ms |
| **CLS** | Visual stability — unexpected layout shift | ≤ 0.1 |

All three must be good. Two good and one "needs improvement" fails overall.

Judged on **field data** — real Chrome users over a rolling 28 days — not a
lab run. A green Lighthouse score is not the same as passing.

- **LCP**: preload the hero image and font, never lazy-load anything above
  the fold, cut render-blocking CSS/JS. If LCP is bad on a page that looks
  lean, check **TTFB** — it's usually slow hosting, not front-end code.
- **INP**: the one heavy client-side interactivity breaks — 3D effects,
  animation libraries, sticky headers, faceted filtering. Break up JS tasks
  over 50ms. Third-party scripts (analytics, chat widgets, tag managers)
  are the quiet killer.
- **CLS**: explicit `width`/`height` or `aspect-ratio` on every image and
  embed, reserved space for anything injected, `font-display: swap`.

To measure a live URL, fetch:
```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&strategy=mobile
```
Free, no key needed for occasional checks. Read `loadingExperience.metrics`
for field data; fall back to `lighthouseResult.audits` if the page has too
little traffic for real-user data yet. Mobile first — Google indexes
mobile-first.

## Crawlability and indexing

- Self-referencing `<link rel="canonical">` on every indexable page. Real
  duplicates (filter/sort variants, print views) canonicalize to the
  primary instead.
- `sitemap.xml` exists, is valid, referenced from `robots.txt`, and lists
  only canonical indexable URLs — no `noindex`ed or redirecting ones.
- No conflicting signals: a page that is both `noindex` and in the sitemap.
- URLs lowercase, hyphens not underscores, no junk query params, stable.
- Redirects single-hop. Collapse A→B→C into A→C and link to the final URL.
- HTTPS everywhere, no mixed content, one canonical host — http→https and
  www↔non-www should **redirect**, not both serve the same content.
- **Pagination**: each page self-canonicalizes. `rel=prev/next` is
  deprecated and ignored.
- **Faceted navigation**: filter combinations explode into thousands of
  URLs and eat crawl budget. Filters that don't change content meaningfully
  should be `noindex,follow` and out of the sitemap.
- **hreflang**, if multilingual: every version lists every other version
  *including itself*, plus one `x-default`. One-directional hreflang is a
  common silently-broken pattern — check both directions.

## On-page

- **`<title>`** unique per page, ~50–60 chars, primary query near the front.
- **Meta description** unique, ~140–160 chars, written as click-through
  copy. It does not affect ranking — it affects whether anyone clicks.
- **Exactly one `<h1>`**, matching real page intent.
- **Heading hierarchy** H1→H2→H3 with no skipped levels. Never chosen for
  visual size.
- **Anchor text** describes the destination. Never "click here" / "לחץ כאן"
  — it's a ranking signal and a screen-reader cue at once.
- **`alt` text** descriptive and specific. Decorative images get `alt=""`
  — empty, not missing.
- **Images**: WebP/AVIF, responsive `srcset`, explicit dimensions, lazy-load
  below the fold only.
- **Social preview tags** — skipped constantly, trivial to add, visible
  impact: `og:title`, `og:description`, `og:image` (1200×630), `og:url`,
  `og:type`, `twitter:card`. Without them a shared link renders blank on
  WhatsApp and LinkedIn. That's a real bug, not a nitpick.
- **Custom 404** that helps — search or links back in, not a blank error.

## Structured data (JSON-LD)

Google's recommended format. Use `<script type="application/ld+json">` with
Schema.org vocabulary. It does **not** boost ranking directly — it makes you
*eligible* for rich results and helps machines understand the page.

Worth implementing: `Organization` or `Person` sitewide, `WebSite`,
`BreadcrumbList`, and then whatever actually applies — `Article`,
`Product`, `LocalBusiness`, `Event`, `VideoObject`, `Review` (only if the
reviews are real and displayed).

Two firm rules:
1. **Only mark up content that is visibly on the page.** Invisible or
   fabricated markup is a spam-policy violation and it undermines
   AI-citation trust. This is the most common self-inflicted schema bug.
2. Supply every **required** property, and keep the JSON valid — one typo
   kills the whole block silently, with nothing visible on the page.

**Dead for rich results — do not add these expecting SERP real estate:**
`FAQPage` (restricted Aug 2023, removed entirely 7 May 2026) and `HowTo`
(deprecated Aug/Sep 2023). Google also retired seven more types in June
2025 — Book Actions, Course Info, Claim Review, Estimated Salary, Learning
Video, Special Announcement, Vehicle Listing. Existing markup is harmless to
keep; adding it as a *strategy* is not. Assume the pruning continues and
re-verify any type before recommending it for its rich result.

**Schema does not drive AI citation — don't imply it does.** A controlled
study comparing ~1,900 pages that added JSON-LD against matched controls
found no citation gain and a small decline. The widely-repeated "2.5x more
likely to be cited" claims come from studies without control groups, where
the likely real driver is that sites sophisticated enough to add schema were
already authoritative. Recommend schema for what it actually does — rich
result eligibility and machine-readable clarity — and stop there.

`Speakable` is narrower than it's usually presented: limited release,
US English, news-like content, surfacing on Assistant devices. Worth
mentioning to a news publisher; not a general AEO lever.

## AEO — getting cited by AI answer engines

**This is no longer a bonus channel.** Since a July 2026 rollout, Gemini-
powered AI answers are the default output for most Google queries, not an
opt-in tab. Zero-click searches reached ~68% of US queries; when an AI
Overview appears, clicks to normal results drop around 60%. Optimizing only
for a blue link optimizes for a shrinking surface.

*(That framing is the most volatile claim in this file — verify it.)*

The prerequisite is unchanged: **you cannot be cited from a page the engine
can't retrieve.** Google states there are no special requirements and no
special markup for AI features — a page needs to be indexed and eligible to
show with a snippet.

But "rank top-10 and citation follows" no longer holds the way it did. One
large study of AI Overview citations found the share coming from pages
ranking in the top 10 organically fell from roughly **76% to 38%** over
about a year, with the rest split fairly evenly between pages ranking
11–100 and pages ranking beyond 100. *(Industry research, not Google
documentation — direction is well corroborated, treat the exact figures as
approximate.)*

What that changes: classic SEO is still the **entry ticket**, because
retrieval requires indexing. It is no longer a good **predictor**. A page
that ranks 40th can be cited, and a page that ranks 3rd often isn't. So
don't tell someone their AEO problem will be solved by ranking better — the
passage-level work below is doing most of the lifting.

What actually raises the odds:

- **The unit that gets cited is a passage, not the page.** Open every
  answerable section with a direct, self-contained answer in ~40–60 words,
  *before* the background and caveats. Buried answers get passed over.
  `references/examples.md` has a before/after of exactly this edit — it is
  the highest-leverage change on most pages, and the easiest to agree with
  in principle while still getting wrong.
- **Question-shaped headings** matching how people actually ask. AI systems
  run "query fan-out" — several related sub-queries — before composing an
  answer, so a cluster of related sub-questions beats one narrow answer.
- **One clear claim per passage**, with concrete specifics — numbers,
  dates, named entities. Vague prose can't be grounded, so it isn't quoted.
- **Lists and tables** wherever content is comparative or sequential.
  Retrieval systems extract those cleanly.
- **E-E-A-T**: a real named author with real credentials — not a "Team"
  byline — original data or genuine first-hand experience, primary sources
  cited, and a visible "last updated" date. Trust is the load-bearing part.
- **Freshness matters more for AEO than for classic SEO.** Most AI
  citations go to pages updated within the year. Stale pricing and
  comparison pages get filtered out.
- **Corroboration off-site.** Being referenced consistently elsewhere
  correlates with being surfaced. A brand-new site starts with none —
  expect AI citation to lag any ranking.
- **Put the answer high on the page, not just early in the section.** One
  citation study found roughly **55% of AI Overview citations came from the
  top third of the page**, and only about 21% from the bottom 40%. The
  intro-fluff-then-answer pattern costs citations twice: once within the
  section, once across the page.
- **Pre-answer the next question.** Fan-out retrieves passages for
  *adjacent* sub-questions — comparisons, pricing, steps, specs — not only
  the literal query. A page that answers "which one should I buy" and stops
  loses the retrievals for "how much does it cost" and "how do I set it up"
  to somebody else's page.

### The platforms don't agree with each other

Only about **12% of cited sources overlap across platforms** for the same
query. "Optimize for AI citation" is not one target:

| Engine | What it favors |
|---|---|
| **Google AI Overviews** | Strongest preference for recognized brands and established domains. Most clickable citations of any engine. |
| **ChatGPT** | Older domains — a large share of what it cites is 15+ years old. Prefers claims corroborated across several sources over a single assertion. |
| **Perplexity** | Searches the live web on nearly every query, so freshness counts most here. Leans hardest on community sources; an institutional tone underperforms a well-sourced practitioner answer. |
| **Copilot** | Cites markedly younger domains than the others — the most realistic target for a new site. |

*(Citation-tracking research, not vendor documentation. Directionally
consistent across trackers; specific percentages vary by study.)*

**Where the citations actually go.** A handful of domains — Reddit,
Wikipedia, YouTube, LinkedIn — capture a large majority of all AI citations
across engines, with Reddit alone a substantial share. For a typical
business site, competing head-on with a Reddit thread on a general query is
not a winnable goal. The realistic target is the remainder: specific,
technical, branded, or niche queries where no such thread exists. Say that
plainly rather than promising visibility on head terms.

**`llms.txt` is not a citation lever.** Google has explicitly said Search
does not use it, and its AI-features guidance states no special
machine-readable file is needed. Adoption sits near 10% of domains after
18 months, and one study found the overwhelming majority of published files
receive no AI requests at all. It does have real use by **coding agents**
reading documentation — a developer-tooling case, worth framing separately.
Never present it as a search or citation tactic.

**Whether AI crawlers can reach the site at all** is upstream of everything
here, and it's where people accidentally lock themselves out — blocking
`GPTBot` does not remove you from ChatGPT's answers, but blocking
`OAI-SearchBot` does. See `references/ai-crawlers.md`.

## Hebrew and RTL

- `<html lang="he" dir="rtl">` at the root — and check nested components,
  since LTR-authored component libraries often hardcode their own `dir`.
- **Bidi bugs**: English brand names, numbers, or Latin text inside Hebrew
  renders in the wrong visual order. Wrap in `<bdi>` or set `dir="auto"` on
  mixed-content and user-generated fields. This is a correctness bug before
  it is an SEO one.
- URL slugs: pick Latin or Hebrew and stay consistent site-wide.
- Write titles and descriptions in **natural Hebrew**, the way an Israeli
  actually searches — not a translated English template. JSON-LD
  `name`/`description` should match the displayed language.
- `LocalBusiness` schema with Israeli address and phone format if relevant;
  `hreflang="he-IL"` when targeting Israel specifically.

**A real opportunity, not just a constraint:** AI engines have far less
well-structured Hebrew data than English. A Hebrew page that genuinely
follows the AEO section competes against a much thinner field.

## Quality bugs — boring and expensive

- **Duplicate content at scale.** The biggest risk on templated pages. If
  two pages share 90%+ of their text and differ by a swapped noun, search
  engines may index only one. Each templated page needs genuinely unique
  value, not find-and-replace.
- **Placeholder text shipped to production** — `Lorem ipsum`, `TODO`,
  `undefined`, `[object Object]`, `NaN`, untranslated strings on a Hebrew
  page.
- **Broken and orphan links.** Broken internal links, redirect chains
  reintroduced during reorganization, and pages that are live but
  unreachable from any nav, sitemap, or internal link.
- **Navigation and transition consistency.** Nav or footer differing
  page-to-page without reason, broken breadcrumbs, dead-end pages with no
  next action, route-transition state leaking between pages, and modals or
  toasts that don't inherit the page's `dir`.
- **Every button and CTA**: does it go where its label promises?

Several of these are accessibility bugs first and SEO bugs second — fixing
them pays twice.

## Mobile and accessibility

Google indexes mobile-first, and a screen reader and an AI crawler fail on
many of the same things.

- Mobile and desktop must serve the **same content, links, and meta robots**.
  A `noindex` that appears only on mobile drops the page.
- `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Tap targets ≥ 44×44px with spacing; base font ≥ 16px on mobile, or the
  browser auto-zooms on input focus.
- Contrast ≥ 4.5:1 for body text (WCAG AA), checked against the actual
  background.
- Keyboard-operable everything, with visible focus indicators. Never
  `outline: none` without a replacement.
- Real landmarks (`nav`, `main`, `footer`), labelled form inputs, correct
  ARIA state on custom dropdowns and accordions.

## How to work

**First, establish what you can actually touch.** It changes what you can
promise:

| What you were given | What's possible |
|---|---|
| A live URL only | Diagnose everything. Fix nothing — you can't write to their server. Say so up front rather than ending an audit with fixes you can't apply. |
| A local project or repo | The full loop: find, fix, verify. |
| Pasted code with no context | Review that file. Ask which route it serves before judging anything site-wide — canonical, sitemap, and internal linking are meaningless without it. |
| Nothing yet, page being written | Build mode. Use these sections as the spec while writing, not as an audit afterwards. |

If someone asks to "make my site rank" with nothing attached, ask for the
URL or the project path — one question, then proceed. Don't stall on
details you can infer.

**Reviewing an existing page or site:** work the gates first, then
everything else. Report findings ranked **Critical / High / Medium / Low**,
each naming the exact element or line and *why it matters* — ranking,
AI-citation, or UX. Not a flat dump. "Missing alt text" is useless;
"`img.hero-banner` missing alt (Hero.jsx line 14)" is actionable.

**Writing a new page:** use these same sections as a build spec. Getting it
right in the first draft costs nothing; retrofitting costs a rewrite.

**Fixing:** make the smallest correct change per issue. For anything shared
across pages, fix the shared component once rather than patching every
instance — and say so, because it affects more pages than were reported.
Confirm before bulk changes across many files or anything touching URL
structure. After fixing, re-check that specific item; don't assume the edit
worked.

**Don't guess.** Some things need a human: which URL should be canonical
when several are plausible, whether to publish a real author name, where a
broken link *should* point, rewriting copy that carries business meaning.
Report those as decisions needed, with the tradeoff named.

### Auditing a whole site

Work page by page rather than trying to hold the site in your head at once.

If you can dispatch subagents (Claude Code), two ship alongside this skill
and make a full-site pass practical:

- **`seo-page-auditor`** — read-only, one page at a time, in parallel. It
  carries this same checklist, so it can't change code while reviewing it.
- **`seo-fixer`** — has edit access, runs only on findings you've confirmed.

Enumerate pages from `sitemap.xml`, or by crawling same-domain links, or
from route files in a local project. On a site of 100+ pages, don't audit
every one — cluster by template, audit a representative of each, then fix
at the shared source. Say you sampled and how; never sample silently.

If subagents aren't available (Claude Desktop, claude.ai), everything above
still works — do the same passes yourself, one page per turn, and keep a
running findings list. The checklist is the same either way.

After fixing, re-check the specific items. Loop until a pass finds nothing
left, or until returns flatten — and say which one happened rather than
quietly stopping.

## References

Load on demand — don't read them up front.

| File | When |
|---|---|
| `references/ai-crawlers.md` | Any question about blocking AI bots, `robots.txt` and AI, or why a site isn't appearing in an AI engine |
| `references/examples.md` | Showing someone what a fix looks like — before/after for answer-first passages, titles, JSON-LD, RTL, and how to report a finding |
| `references/audit-checklist.md` | Running a formal audit — every item as PASS/FAIL/N/A |
| `references/sources.md` | Citing a claim, or checking whether something is official vs. practitioner consensus vs. contested |

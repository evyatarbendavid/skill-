---
name: seo-aeo
description: Apply Google's actual ranking rules and AI answer-engine citation principles to any website work. Use whenever building, writing, reviewing, or fixing a web page or website, and whenever someone mentions SEO, AEO, GEO, search ranking, search visibility, Google Search, being cited by AI, Core Web Vitals, LCP, INP, CLS, schema markup, structured data, JSON-LD, sitemaps, canonical URLs, robots.txt, meta descriptions, or how search engines crawl and index pages. Also use when someone asks why a page is not ranking in search, not indexed by Google, or not appearing in AI answers, when they paste a page URL or HTML and ask for a review, and when writing web content meant to be found in search or quoted by ChatGPT, Perplexity, or Google AI Overviews. Do not use for ranking or sorting unrelated things, database indexes, or crawling APIs for data — those share the words and nothing else.
---

# SEO + AEO

Two things every page needs, together, never one instead of the other:

- **SEO** — Google and Bing can crawl it, index it, and rank it.
- **AEO/GEO** — AI answer engines (Google AI Overviews and AI Mode, ChatGPT,
  Perplexity, Copilot, Gemini, Claude) can extract, trust, and cite it.

Apply this whenever you touch a page, even if nobody said the words "SEO."
A page that ships without it is a page that has to be fixed later.

## Work within what you can actually do

This skill runs in different places with different capabilities —
sometimes with web access, a shell, and subagents, sometimes with none of
them. Check what you have rather than assuming. Where a step needs
something you lack, say so and give the person the exact thing to run or
open, then work from what they bring back.

**Never simulate a measurement you couldn't take.** Core Web Vitals are
field data from real visits; a number inferred from reading the code isn't
a rougher measurement, it's not a measurement — and it will be acted on as
though it were. Search Console items need the owner's login and always
will. An item you couldn't check is reported as unchecked, never as passed.

That now includes AI visibility. Search Console's **Search Generative AI
performance reports** (launched June 2026) are the only first-party numbers
for appearing in AI Overviews and AI Mode. Ask the owner to look rather
than estimating — and know the three limits before they do: impressions
only with no click data, data starting May 2026 with no backfill, and a
rollout that began with a subset of UK sites. An empty report far more
often means "not available to this property yet" than "never cited."

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

Two traps. **Agreement is not confirmation** — SEO content farms copy each
other, so one wrong figure spreads across a hundred pages that each look
independent; only the primary docs settle it. And **silence is not
stability** — the May 2026 FAQPage removal shipped as a documentation edit
with no announcement, so read the docs page, not just the blog.

**Baseline verified 2026-08-21.** Past ~90 days, treat every volatile row as
unconfirmed.

> **Known false claims circulating in SEO blogs — do not repeat:**
>
> - That Google tightened LCP to 2.0s, cut CLS to 0.08, added an "FCP" Core
>   Web Vital, or set a January 2026 compliance deadline. None of these
>   appear in Google's documentation.
> - **"Google penalizes AI-written content."** It doesn't. The spam policy
>   targets mass-produced unreviewed content made to game rankings —
>   regardless of how it was written. A human with real expertise directing,
>   verifying, and owning the result is the line that matters, not the tool.
> - **"Schema markup makes you 2.5x more likely to be cited by AI."** Traces
>   to studies with no control group. See the structured-data section.
> - **"You need an `llms.txt` to appear in ChatGPT or AI search."** Google
>   has said the opposite outright. The same goes for `llms-author.txt`,
>   the newer variant pitched as an authorship or E-E-A-T signal — Google
>   has said it uses neither file.
> - **"Domain Authority / Domain Rating is a Google ranking factor."** Those
>   are third-party metrics invented by SEO tool vendors. Google has never
>   used them. Useful as a rough competitive comparison; not a thing to
>   optimize.
> - **"A page needs at least 300 words to rank."** No such threshold exists.
>   Thin content is a judgment about whether the page answers the question,
>   not a word count.
> - **"FAQ and HowTo rich results still work if you format the schema
>   correctly."** They were switched off at the platform level. No markup
>   change brings them back.
> - **"AI answers are now the default result for most Google searches."**
>   Measurement says a large minority — AI Overviews on somewhat over 20%
>   of searches, AI Mode under 1% in the most recent study window. The
>   effect where they appear is real and large; the reach is routinely
>   overstated. This file carried the overstated version itself until it
>   was checked, which is how easily it spreads.

## Where the honest answer is "it's contested"

Say so, rather than picking a side and sounding confident.

**Do clicks and dwell time affect ranking?** Google's spokespeople have
denied it repeatedly and bluntly. Antitrust disclosures describe an internal
system that does use click and session behavior as a re-ranking input. Both
of those are true at once, and the resolution is probably that there is no
simple "dwell time signal" while aggregated satisfaction signals are used
somewhere in the stack. Practical upshot: don't sell "optimize for dwell
time" as a lever — it isn't directly controllable — but don't claim user
behavior is irrelevant either.

**Does structured data help AI citation?** Vendor studies say yes; the one
controlled study says no. Weight the controlled one, and say the evidence
is thin either way.

**Should a site block AI crawlers?** Blocking has a measured traffic cost
and frequently fails to prevent citation anyway. That makes it a business
and legal decision rather than an optimization. See
`references/ai-crawlers.md`.

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
   headings and text in what comes back — that's close to what a crawler
   sees. Without fetch, ask them for `view-source:` output rather than
   judging from the rendered page, which shows you the post-hydration DOM
   and hides the entire problem.

   **The sharper version of this bug:** `canonical`, `meta robots`, and
   `hreflang` injected by client-side JS. The first crawl pass reads the raw
   HTML and can act on it — decide indexing, pick a canonical — before the
   render pass ever runs. Head tags that only exist after hydration may
   simply never be seen in time. Those three must be in the server response,
   whatever else is client-rendered.
5. **Core Web Vitals pass** — all three, at the 75th percentile of real
   users, on mobile and desktop separately.

**Read HTML by parsing it, not by pattern-matching it.** Production HTML is
minified, and minifiers drop optional quotes: `<html lang=en>`,
`name=viewport`, `rel=canonical`. A search for `name="viewport"` finds
nothing on such a page and you conclude the tag is missing. Checked against
one real documentation page, that mistake reported a missing canonical, a
missing viewport, a missing meta description, and missing Open Graph tags —
all four were present, all four unquoted.

The failure is one-directional and that's what makes it dangerous: it never
invents a tag, it only loses one, so every error lands as a confident false
finding in your report. If you have a shell, parse the HTML (Python's
`html.parser` handles this correctly). If you're reading it by eye, allow
for unquoted, single-quoted, and double-quoted forms, and for attributes in
any order. If you are not certain a tag is absent, say you couldn't confirm
it rather than reporting it missing.

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

**Single-page app route changes are now measurable — but be careful what
you claim follows from that.** Core Web Vitals have historically been
collected only on hard page loads, so an SPA whose first load was fast and
whose every subsequent route change was slow had that second half invisible
to field data. Chrome's Soft Navigations API changes the measurement:
shipped unflagged in **Chrome 151, stable 28 July 2026** (Edge 151 too),
adding `soft-navigation` entries to the Performance Timeline, with
`web-vitals` support alongside it.

What that does **not** yet establish is that those numbers count for
ranking. How soft navigations will be reported in CrUX — the field dataset
Google's Core Web Vitals assessment actually reads — is still undetermined,
and it is not a given they'll be weighted like hard navigations. So:
instrument route transitions and fix the slow ones, because they are a real
user experience and you can finally see them. Don't tell someone their
route changes are now a ranking factor. **[the API is OFFICIAL and shipped;
its CrUX treatment is UNCERTAIN — re-verify, this one is moving]**

**If you can fetch a URL**, measure rather than guess:
```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&strategy=mobile
```
Free, no key needed for occasional checks. Read `loadingExperience.metrics`
for field data; fall back to `lighthouseResult.audits` if the page has too
little traffic for real-user data yet. Mobile first — Google indexes
mobile-first.

**If you can't**, hand them `https://pagespeed.web.dev/analysis?url=<URL>`
and read the numbers they paste back. Don't estimate these from the code —
see above.

**If the request succeeds but returns an error instead of data**, that is
its own branch, and the common one. Without a key the quota is shared
across everyone using it unkeyed, so `429 Quota exceeded` is routine rather
than exceptional; you can also get `400` for a URL the API can't fetch.
Read the JSON: a `429` needs `&key=` or a retry later, while a `400` is
usually telling you the page is unreachable, which is a finding in itself.

What must not happen either way is the Core Web Vitals gate quietly
vanishing from the report. It is one of the five gates. An unanswered gate
is reported as unanswered, with the reason and the link for them to run it
themselves — never omitted, and never softened into "performance looks
fine."

## Crawlability and indexing

- Self-referencing `<link rel="canonical">` on every indexable page. Real
  duplicates (filter/sort variants, print views) canonicalize to the
  primary instead.
- **A canonical that points elsewhere is not automatically a finding.**
  Before flagging one, fetch the target: if it returns 200 and appears in
  the sitemap, this is deliberate consolidation working correctly. The
  common legitimate case is locale-prefixed URLs pointing at a
  locale-neutral one — `/en/learn/x` canonicalizing to `/learn/x`, with
  `/learn/x` being what the sitemap lists. Reporting that as a bug wastes
  the reader's time and costs you their trust in the rest of the report.
  A canonical worth flagging is one whose target 404s, redirects, is
  `noindex`, or contradicts the sitemap.
- `sitemap.xml` exists, is valid, referenced from `robots.txt`, and lists
  only canonical indexable URLs — no `noindex`ed or redirecting ones.
- **Check the sitemap actually contains the homepage.** A populated,
  perfectly valid sitemap that omits `/` is common and invisible to any
  check that stops at "sitemap: present". Google found the homepage long
  ago by other means; an AI retrieval system meeting the site for the
  first time has less to go on.
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
  *Unique* is the word doing the work: a global fallback description
  rendering on every page passes a "has a description" check on all of
  them and fails at the only job a description has. You can only catch it
  by comparing pages to each other, so collect descriptions across the
  site rather than judging one page alone.
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

Sitewide entity identity is the piece most often missing entirely, on
sites that have every other basic covered. Check for it early — it is
cheap to add and there is frequently nothing there at all.

Schema.org types form a hierarchy, so read subtypes as what they are: a
`Corporation`, `Restaurant`, `NGO`, or `OnlineStore` block *is*
`Organization` markup. Don't report a site that used a precise subtype as
having no entity markup.

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

**This is no longer a bonus channel** — but be precise about the size of it,
because the loose version of this claim is everywhere and it is wrong.

What the measurements actually say, as of early 2026:

- **~68% of US searches end without a click** at all (Similarweb
  clickstream via SparkToro), up from roughly 60% two years earlier.
- **AI Overviews appear on something over 20% of searches**, and when one
  appears, clicks to normal results fall by around 60%.
- **AI Mode is far more extreme and far smaller**: about 93% of AI Mode
  searches produce no click, but AI Mode was only ~0.34% of searches in a
  January–April 2026 study window. Google said at I/O 2026 that it had
  passed a billion monthly users with query volume more than doubling each
  quarter, so the share is small and moving fast.

So: AI answers are not yet the default output for most Google queries.
They are on a large minority of them, they take most of the clicks where
they appear, and the trend is one direction. That is enough reason to stop
optimizing only for a blue link — and it is not a reason to repeat "Google
is now an answer engine, organic traffic is over." Someone whose traffic is
holding up is not wrong about their own data.

*(These are the most volatile numbers in this file, and every one is
industry measurement rather than Google documentation. Re-verify before
quoting them to anyone making a decision — and expect the AI Mode share in
particular to be out of date.)*

The prerequisite is unchanged: **you cannot be cited from a page the engine
can't retrieve.** Google states there are no special requirements and no
special markup for AI features — a page needs to be indexed and eligible to
show with a snippet.

But "rank top-10 and citation follows" no longer holds the way it did. An
Ahrefs study across ~863,000 keywords and ~4 million AI Overview URLs found
the share of cited pages that also ranked in the organic top 10 fell from
roughly **76% (July 2025) to 38% (March 2026)** — about half, in eight
months — with the rest spread across pages ranking 11–100 and beyond 100.

Measurements from different firms put that overlap anywhere from **17% to
38%**, because they count differently. Which is the point: don't quote a
single figure as precise. The finding that survives every methodology is
the direction, and it is not subtle. *(Industry research, not Google
documentation.)*

What that changes: classic SEO is still the **entry ticket**, because
retrieval requires indexing. It is no longer a good **predictor**. A page
that ranks 40th can be cited, and a page that ranks 3rd often isn't. So
don't tell someone their AEO problem will be solved by ranking better — the
passage-level work below is doing most of the lifting.

**Audit the pages that answer questions, not the homepage.** A homepage is
a gateway — marketing copy that introduces a product. It was never going to
be the passage an engine lifts, and grading it on answer-shape produces a
wall of failures that says nothing about the site. For an AEO assessment,
look at docs, guides, articles, and support pages, and name which pages you
looked at. If the homepage is genuinely all you were given, report
answer-shape gaps as expected for the page type and say where a real
assessment would need to look.

What actually raises the odds:

- **The unit that gets cited is a passage, not the page.** Open every
  answerable section with a direct, self-contained answer in ~40–60 words,
  *before* the background and caveats. Buried answers get passed over.
  `references/examples.md` has a before/after of exactly this edit — it is
  the highest-leverage change on most pages, and the easiest to agree with
  in principle while still getting wrong.
- **Question-shaped headings, covering the neighbourhood.** Before
  composing an answer, these systems run "query fan-out" — decomposing the
  question into several related sub-queries and retrieving passages for
  each. So headings should match how people actually ask, *and* the page
  should pre-answer what they'd ask next: the comparison, the price, the
  setup steps. A page that answers "which one should I buy" and stops
  hands the adjacent retrievals to somebody else's page.

  **The title counts as one.** A short page titled "How much JavaScript do
  you need to know to use Node.js?" that answers it in the first paragraph
  is already well shaped, with two headings and no more. Don't push someone
  to manufacture question-headings on a page whose title asks the question
  and whose body answers it — you'd be adding structure to a page that
  doesn't need it. The gap worth reporting is a page that answers several
  distinct questions with nothing in the markup separating them.
- **One clear claim per passage**, with concrete specifics — numbers,
  dates, named entities. Vague prose can't be grounded, so it isn't quoted.
- **Lists and tables** wherever content is comparative or sequential.
  Retrieval systems extract those cleanly.
- **E-E-A-T**: a real named author with real credentials — not a "Team"
  byline — original data or genuine first-hand experience, primary sources
  cited, and a visible "last updated" date. Trust is the load-bearing part.
- **There is now a spam policy naming this.** Google's spam policies were
  rewritten in 2026 to name manipulating the generative-AI answers in
  Search as an offense in its own right. Everything above is about being
  genuinely the best source for a passage; anything that is instead about
  gaming which passage gets picked has moved from ineffective to
  sanctionable. *(Re-verify the current wording before quoting it — this
  is a recent change.)*
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

### "Optimize for AI citation" is four different targets

Only about **12% of cited sources overlap across platforms** for the same
query, and the engines' preferences genuinely conflict — one favours
established brands, another old domains, another freshness and a
practitioner voice. Don't promise all four at once; pick the one matching
where the audience already is. `references/platforms.md` has each profile,
the caveats, and how to choose.

The ceiling worth stating out loud: on general consumer queries a handful
of platforms — Reddit, Wikipedia, YouTube — take most citations. A business
site will not displace a popular forum thread on a head term. The winnable
ground is specific, technical, branded, or niche questions where no such
thread exists.

### Two things upstream of all of it

**Can the AI crawlers reach the site?** This is where people lock
themselves out by accident: blocking `GPTBot` does not remove you from
ChatGPT's answers, but blocking `OAI-SearchBot` does. Check before
diagnosing anything else — `references/ai-crawlers.md`.

**Keeping content out of AI answers is a page-level control, not a
robots.txt one.** This is the part most "should we block AI" discussions
miss. Google's robots meta directives — `nosnippet`, `data-nosnippet` around
a specific passage, and `max-snippet:[n]` — apply to AI Overviews and AI
Mode as well as to ordinary results, and `max-snippet:0` makes a page
ineligible for AI Overviews outright. Unlike `robots.txt` with AI crawlers,
these are honored, because Google is the one reading them.

The tradeoff is the whole story, so say it before anyone reaches for it:
**the same directives remove your normal search snippet.** You are trading
a result that shows what the page says for one that shows a bare title. For
most sites that costs more than the AI citation was costing them. Where it
genuinely fits is narrower — a paywalled excerpt, licensed text, a passage
that must not be quoted out of context — and `data-nosnippet` around that
passage alone is usually the right size of the tool, rather than
`nosnippet` on the whole page.

**`llms.txt` is not a citation lever.** Google has said Search does not use
it, and its AI-features guidance states no special machine-readable file is
needed. Adoption sits near 10% of domains after 18 months, and one study
found the large majority of published files receive no AI requests at all.
It does have real use by **coding agents** reading documentation — frame
that separately. Never present it as a search or citation tactic.

## Hebrew and RTL

- `<html lang="he" dir="rtl">` at the root — and check nested components,
  since LTR-authored component libraries often hardcode their own `dir`.
- **Bidi bugs**: English brand names, numbers, or Latin text inside Hebrew
  renders in the wrong visual order. Wrap in `<bdi>` or set `dir="auto"` on
  mixed-content and user-generated fields. This is a correctness bug before
  it is an SEO one.
- **Anything rendered outside the RTL container inherits the wrong
  direction.** Modals, toasts, tooltips, dropdowns and date pickers are
  routinely portaled to `document.body`, which escapes the `dir="rtl"` on
  your app root. The page reads correctly and every overlay on it reads
  backwards. Set `dir` on the portal root, not only on the app root — and
  test by opening each overlay, since nothing in the static HTML shows it.
- **Directional icons must mirror.** A "next" arrow pointing right is
  pointing backwards in Hebrew. Same for back buttons, carousel chevrons,
  breadcrumb separators, and progress indicators. `transform: scaleX(-1)`
  under `[dir="rtl"]`, or a mirrored asset.
- **Physical CSS properties are what make an RTL layout subtly wrong
  everywhere.** `margin-left`, `padding-right`, `text-align: left`,
  `float: left` all stay put when the direction flips. The logical
  equivalents — `margin-inline-start`, `padding-inline-end`,
  `text-align: start`, `float: inline-start` — follow it. On a site that
  serves both directions this is the single highest-leverage change.
- **Fields that hold LTR data need `dir="ltr"` even on an RTL page** —
  email, URL, phone, credit card, code. Their placeholder alignment should
  match. A phone number typed into a `dir="rtl"` input is a classic
  reversed-digits bug report.
- URL slugs: pick Latin or Hebrew and stay consistent site-wide.
- Write titles and descriptions in **natural Hebrew**, the way an Israeli
  actually searches — not a translated English template. JSON-LD
  `name`/`description` should match the displayed language.
- `LocalBusiness` schema with Israeli address and phone format if relevant;
  `hreflang="he-IL"` when targeting Israel specifically.

**A real opportunity, not just a constraint:** AI engines have far less
well-structured Hebrew data than English. A Hebrew page that genuinely
follows the AEO section competes against a much thinner field.

## What this skill can't fix: off-page authority

Links from other sites remain a real ranking input, and nothing in a
codebase changes them. Say that plainly rather than letting flawless
on-page work imply it is sufficient — a new site with perfect technical
SEO and no one referencing it will lose to a worse page on an established
domain, and someone should hear that from you before they spend three
months wondering why.

What is worth stating, because most of what circulates about links is
wrong:

- **Domain Authority / Domain Rating are not Google metrics.** They are
  vendor inventions, useful for rough competitive comparison and not a
  thing to optimize. Google has never used them.
- **Buying links violates the spam policies**, and the exchange schemes
  sold as safe alternatives are the same thing with extra steps.
- **The version that works is slow**: being genuinely worth referencing,
  and being referenced by places that would have linked to you anyway.
  Digital PR, original data, and being the primary source on something.
- **For AEO, the equivalent is corroboration** — being mentioned
  consistently across sites the engines already read. Same input, and a
  brand-new site starts with none of it, which is why AI citation lags
  ranking on a young domain.

This section exists so the skill doesn't quietly overpromise. Everything
else here is inside your control; this isn't, and pretending otherwise is
how a technically perfect site becomes a disappointed client.

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
  unreachable from any nav, sitemap, or internal link. Orphan pages get a
  fraction of the traffic of equivalent linked pages, and may never be
  discovered independently of the sitemap. Find them by crawling the site
  and filtering to pages with zero internal inbound links — the ones you
  forgot exist are exactly the ones nothing links to.
- **Internal links are how authority moves around a site.** Pages that make
  money — pricing, key categories, conversion pages — should sit within
  about three clicks of the homepage and be linked from the pages that
  already have the most authority, not survive on a single footer link. A
  strong internal link from an established page often does more for a
  page's indexing priority than a weak external one.
- **Navigation and transition consistency.** Nav or footer differing
  page-to-page without reason, broken breadcrumbs, dead-end pages with no
  next action, route-transition state leaking between pages, and modals or
  toasts that don't inherit the page's `dir`.
- **Every button and CTA**: does it go where its label promises?

Several of these are accessibility bugs first and SEO bugs second — fixing
them pays twice.

## Mobile and accessibility

**Intrusive interstitials are a documented mobile demotion** and one of the
few things on this page that is a penalty rather than a missed opportunity.
It applies to a popup covering the main content immediately on arrival from
search, a standalone interstitial you must dismiss to reach anything, and a
layout whose above-the-fold area looks like one with the real content
pushed below it.

What is exempt is as worth knowing as what isn't: cookie and age-gate
notices required by law, login dialogs on content that isn't publicly
indexable, and banners using a reasonable strip of the screen that dismiss
easily. So the fix is almost never "remove the newsletter prompt" — it is
make it a dismissible banner, or delay it past the first interaction. It
also only bites on the page arrived at from search, so the same modal
deeper in a flow is not the issue.

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

**Establish what you can actually touch.** It changes what you can promise:

| What you were given | What's possible |
|---|---|
| A live URL only | Diagnose everything. Fix nothing — you can't write to their server. Say so up front rather than ending an audit with fixes you can't apply. |
| A local project or repo | The full loop: find, fix, verify. |
| Pasted code with no context | Review that file. Ask which route it serves before judging anything site-wide — canonical, sitemap, and internal linking are meaningless without it. See below for what *is* judgeable from one component. |
| Nothing yet, page being written | Build mode. Use these sections as the spec while writing, not as an audit afterwards. |

If someone asks to "make my site rank" with nothing attached, ask for the
URL or the project path — one question, then proceed. Don't stall on
details you can infer.

**Ask how the page gets its visitors before you rank the fixes.** Not every
page is reached from search. Documentation entry points, install pages, and
anything people arrive at from a link in a README or an email are doing fine
without a canonical tag, and a report that opens with one has misjudged the
page. What does *not* get discounted along with it: `lang`, viewport, alt
text, contrast, keyboard access. Those serve every visitor no matter how
they arrived. Sorting a page's findings into "matters for search here" and
"matters regardless" is most of the value you add; listing everything at
equal weight is most of the noise.

**Reviewing an existing page or site:** work the gates first, then
everything else. Report findings ranked **Critical / High / Medium / Low**,
each naming the exact element or line and *why it matters* — ranking,
AI-citation, or UX. Not a flat dump. "Missing alt text" is useless;
"`img.hero-banner` missing alt (Hero.jsx line 14)" is actionable.

`references/examples.md` §6 is a complete report for one page — gates as a
table up front, findings ranked with the ranking justified, the decision
asked in the owner's language, and an explicit list of what couldn't be
checked. Copy that shape.

**Writing a new page:** use these same sections as a build spec. Getting it
right in the first draft costs nothing; retrofitting costs a rewrite.

**Fixing:** make the smallest correct change per issue. For anything shared
across pages, fix the shared component once rather than patching every
instance — and say so, because it affects more pages than were reported.
Confirm before bulk changes across many files or anything touching URL
structure. After fixing, re-check that specific item; don't assume the edit
worked.

**Working in a codebase** — a pasted component, a framework project, a
local repo — has its own rules, and two of them prevent real damage: a
clickable `<div onClick>` is a link no crawler can follow, and a URL taken
from a dev server must never be written into a source file. The rest, plus
where each framework keeps its head tags and its sitemap, is in
`references/working-in-code.md`. Read it whenever you have code in front of
you.


**Don't guess.** Some things need a human: which URL should be canonical
when several are plausible, whether to publish a real author name, where a
broken link *should* point, rewriting copy that carries business meaning.
Report those as decisions needed, with the tradeoff named.

**Write the decision so the person can actually make it.** Whoever asked
may run a bakery, not a CDN. "Your canonical URL is ambiguous" hands them a
term and no way forward. Ask the question in their language, give the
options, and say what each one costs:

> Two addresses show the same page — `yoursite.com/challah` and
> `yoursite.com/breads/challah`. Google will pick one to show and ignore
> the other. Which should people land on? Whichever you pick, I'll point
> the other one at it, so no one hits a dead end.

Same content, answerable by someone with no technical background. Keep the
precise term in the finding for anyone who wants it — just don't make it
the whole message.

**Ask who is going to make the change.** This decides the shape of the
whole report and it is one question. "Add `width` and `height` to the
`<img>`" is the right instruction for a developer and useless to someone
whose site is on Wix — where the same fix is a setting, or does not exist,
or needs the person who built it for them. If they have a developer, write
findings the developer can act on and give the owner the summary. If they
don't, say which fixes their platform can do, which need someone hired,
and roughly in what order — and don't hand a non-technical owner a list of
code edits with no route to getting them made.

Whether to translate the vocabulary at all: default to plain language, and
drop the translation once they use the terms back at you. If you are
unsure, one sentence asking is cheaper than guessing wrong in either
direction — jargon at someone who doesn't have it stalls them, and
over-explaining to a developer reads as condescension.

### Auditing a whole site

Work page by page rather than trying to hold the site in your head at once.

If you can dispatch subagents (Claude Code), two ship alongside this skill
and make a full-site pass practical:

- **`seo-page-auditor`** — read-only, one page at a time, in parallel. It
  carries this same checklist, so it can't change code while reviewing it.
- **`seo-fixer`** — has edit access, runs only on findings you've confirmed.

Enumerate pages from `sitemap.xml`, by crawling same-domain links, or from
route files in a local project. Past about 100 pages, don't audit every one
— sample, and sample in a way you can describe. The procedure is in
`references/situations.md` under *A large site*: how to group, how many per
group, which pages never get sampled, and what to do when the sample
disagrees with itself. Say what you sampled and how; never sample silently.

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
| `references/platforms.md` | Someone asks about a specific AI engine, or why they're cited in one and not another |
| `references/situations.md` | The site is large, e-commerce, multilingual, full of thin pages, mid-migration, or chasing entity recognition — depth that only applies in those cases |
| `references/ai-crawlers.md` | Any question about blocking AI bots, `robots.txt` and AI, or why a site isn't appearing in an AI engine |
| `references/examples.md` | Showing someone what a fix looks like — before/after for answer-first passages, titles, JSON-LD, RTL — plus how to write one finding (§5) and a complete page report (§6) |
| `references/audit-checklist.md` | Running a formal audit — every item as PASS/FAIL/N/A |
| `references/working-in-code.md` | There is code in front of you — a pasted component, a local repo, a framework project. Route-file mapping, where each framework keeps head tags and sitemaps, and the two rules that prevent real damage |
| `references/field-notes.md` | Deciding what to look at first — what actually turned up broken on real production sites, with the sample size stated |
| `references/sources.md` | Citing a claim, or checking whether something is official vs. practitioner consensus vs. contested |

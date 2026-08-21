# SEO + AEO reference

> **Last verified: 2026-08-21.**
> If more than ~90 days have passed, treat every claim about Core Web Vitals
> thresholds, rich-result availability, and AI-answer surfaces as **unconfirmed**
> until re-checked. The stable-vs-volatile table in SKILL.md says which claims those are.

This is a topic-agnostic reference: every principle applies to any content site.

## How to read the source labels

Every non-obvious claim is tagged:

- **[OFFICIAL]** — stated by Google, Schema.org, or web.dev in their own
  documentation. Treat as ground truth.
- **[CONSENSUS]** — not an official rule, but well-established agreement among
  serious practitioners and repeatedly observed. Reliable, but not a guarantee.
- **[UNCERTAIN]** — genuinely unprovable or contested. Do not build a plan that
  *depends* on it.

**These labels are load-bearing. Never restate a [CONSENSUS] or [UNCERTAIN]
claim as fact.**

> **The single most important honesty caveat, up front.** Google states plainly
> that following its guidance does **not** guarantee crawling, indexing, or
> ranking: *"Google doesn't guarantee that it will crawl, index, or serve your
> page, even if your page follows the Google Search Essentials."* **[OFFICIAL]**
> ([Search Essentials](https://developers.google.com/search/docs/essentials)).
> And there is **no guaranteed formula that forces an AI engine to cite you.**
> Anyone who promises a specific keyword ranking or a guaranteed AI citation by
> a date is selling certainty that does not exist. What we *can* do is remove
> every technical reason to be excluded, and maximize the odds — which on a
> low-competition long-tail term is genuinely good.

---

## 1. Crawl / Index fundamentals (הבסיס)

Google Search works in three stages, and a page must clear all three before it
can rank **[OFFICIAL]**
([How Search Works](https://developers.google.com/search/docs/fundamentals/how-search-works)):

1. **Crawling (סריקה)** — Googlebot discovers URLs (from links, sitemaps, and
   previously known pages) and downloads text, images, and video. Google does
   not accept payment to crawl more often. **[OFFICIAL]**
2. **Indexing (אינדוקס)** — Google analyzes the downloaded content, processes
   the page (including running its JavaScript, see §3), and stores it in the
   index. During indexing Google groups duplicate/near-duplicate pages and
   picks one **canonical** version to represent the cluster. **[OFFICIAL]**
3. **Serving / Ranking (דירוג)** — for a given query, Google returns what its
   ranking systems judge the most relevant, highest-quality results for that
   user, location, device, and language. **[OFFICIAL]**

**Hard technical gate:** Google only indexes pages served with an **HTTP 200
(success)** status code. Client-error (4xx) and server-error (5xx) pages are
not indexed. **[OFFICIAL]**
([Technical requirements](https://developers.google.com/search/docs/essentials/technical))

**Practical implications:**

- If a page is not crawled → it cannot be indexed → it cannot rank. Crawl is the
  foundation; fix crawl problems before touching content.
- `robots.txt` controls **crawling**, not indexing. A URL blocked in
  `robots.txt` can still appear in Search (as a bare URL with no snippet) if
  other pages link to it — and because Googlebot never fetched it, it will
  **never see a `noindex` tag on that page.** To keep a page out of the index,
  allow crawling and use a `noindex` meta robots tag (or `X-Robots-Tag`
  header), **not** a `robots.txt` disallow. **[OFFICIAL]**
  ([Block indexing with noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing);
  [robots.txt intro](https://developers.google.com/search/docs/crawling-indexing/robots/intro))
- Google dropped support for a `noindex:` directive *inside* robots.txt back in
  September 2019. People still try it; it does nothing. **[OFFICIAL]**

---

## 2. On-page & content — E-E-A-T, search intent, answer-first structure

### 2.1 People-first, helpful content

Google's ranking systems aim to reward **original, high-quality, people-first**
content and to demote content made primarily to manipulate rankings. The
"helpful content" approach began in 2022 as a standalone signal and was folded
into Google's **core ranking systems in the March 2024 core update** — there is
no separate "Helpful Content System" today. **[OFFICIAL]**
([Creating helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))

**Core update cadence is now near-continuous, not quarterly.** Plan for
ongoing volatility rather than discrete quarterly events, and don't attribute
a traffic change to a specific named update without checking the dates.

*(An earlier revision of this file listed four updates and then claimed five
confirmed in a window that excluded one of them. The count did not survive a
re-check and has been removed rather than corrected to a different number:
the cadence is the durable point, and a precise tally of a moving target is
exactly the kind of figure this file should not be carrying. Look up the
current list when it matters.)* **[CONSENSUS on the cadence; the count was
not corroborated]**
([Core updates](https://developers.google.com/search/docs/appearance/core-updates))

Google publishes **self-assessment questions** to judge your own content
**[OFFICIAL]**:

- Does the content provide original information, reporting, research, or
  analysis — not just rehash what other sites already say?
- Is it written by, or does it clearly demonstrate, **first-hand expertise or
  experience**?
- After reading, will someone feel they learned enough to accomplish their
  goal, or do they need to search again?
- Would you trust this content for a decision that matters (money, health,
  safety)?
- Is it free of obvious errors, and does it read like it was made for people
  rather than to hit a keyword?

### 2.2 E-E-A-T (Experience, Expertise, Authoritativeness, Trust)

E-E-A-T is **not a single direct ranking score** — it is the *framework* Google's
quality raters and systems use to judge whether content is reliable.
**[OFFICIAL]** Google states: *"Trust is the most important member of the
E-E-A-T family... the other members of E-E-A-T contribute to trust, but content
isn't always trustworthy if it shows those aspects."*
([Helpful content page](https://developers.google.com/search/docs/fundamentals/creating-helpful-content);
[Search Quality Rater Guidelines PDF](https://static.googleusercontent.com/media/guidelines.raterhub.com/en//searchqualityevaluatorguidelines.pdf))

The **"who / how / why"** test Google recommends **[OFFICIAL]**:

- **Who** created the content — is there a real, credited author with a bio and
  credentials?
- **How** it was created — disclose method, and any AI involvement where it
  would matter to the reader.
- **Why** it exists — to help people, not primarily to rank or to serve ads.

**On AI-generated content:** Google does **not** ban AI content. Its stance is
that it rewards high-quality content *however it is produced*, but that using
automation to generate content *primarily to manipulate rankings* violates spam
policies. **[OFFICIAL]**
([Google Search's guidance about AI-generated content](https://developers.google.com/search/blog/2023/02/google-search-and-ai-content))
Practical rule: AI can draft and assist, but a human with real expertise must
direct, verify, and own the result.

*Note: an author with genuine first-hand experience of the topic is a real,
hard-to-fake E-E-A-T advantage. Where the site owner has lived experience in
the subject, make the author identity explicit — subject to their own privacy
choice, which is theirs to make, not yours to assume.*

### 2.3 Search intent (כוונת החיפוש)

Ranking is intent-matching, not keyword-matching. A page ranks when it satisfies
the *task behind the query* better than alternatives. **[CONSENSUS]** The four
classic intent types: **informational, navigational, commercial, transactional.**
Before writing, look at what already ranks for the target query — the current
page-1 results reveal the intent Google has decided the query has. Match that
format (guide vs. list vs. definition vs. tool). **[CONSENSUS]**

### 2.4 Answer-first structure (מבנה "תשובה קודם")

Structure that helps both human skimmers and AI extractors **[CONSENSUS]**:

- Put a **direct, self-contained answer in the first 1–3 sentences** under each
  heading — before the background and caveats. AI answer engines and Google's
  featured snippets pull short, standalone answer passages; buried answers get
  passed over.
- Use a **clear heading hierarchy** (one `h1`, descriptive `h2`/`h3`) that
  mirrors the questions a reader would ask. Phrase headings as the actual
  questions where natural.
- Prefer **short paragraphs, lists, and tables** for facts, steps, and
  comparisons — these are the chunks retrieval systems extract cleanly.
- One primary topic per page (**topical focus**). Don't dilute a page across
  unrelated subjects.
- Include the **question and its key entities in the visible text**, not only in
  a title tag.

---

## 3. Technical SEO

| Area | What to do | Source |
|---|---|---|
| **HTTPS** | Serve the whole site over HTTPS with a valid certificate; HTTPS is a lightweight ranking signal and a baseline expectation. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/https) |
| **Status codes** | Only 200 pages get indexed. Use 301 for permanent redirects, 404/410 for gone pages, avoid 5xx and "soft 404s" (a 200 page that says "not found"). | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/http-network-errors) |
| **Canonical** | When the same/near-same content lives at multiple URLs, pick one canonical and mark it with `rel="canonical"`. Google treats it as a strong hint, not a command; keep signals consistent (canonical, internal links, sitemap, redirects all pointing the same way). | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/canonicalization) |
| **XML sitemap** | Publish a sitemap listing your canonical, indexable URLs; reference it in `robots.txt` and submit it in Search Console. Helps discovery, especially for new sites with few backlinks. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview) |
| **robots.txt** | Use to manage crawl, **never** as an indexing control (see §1). Do **not** block CSS/JS/image resources Googlebot needs to render the page. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/robots/intro) |
| **Mobile** | Google indexes with **mobile-first** crawling — Googlebot Smartphone is the source of truth. Content, links, and meta robots tags must be **identical** on mobile and desktop; a `noindex`/`nofollow` that appears only on mobile can drop the page. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-first-indexing-best-practices) |
| **JS rendering** | Google renders pages by executing JS in an **evergreen Chromium** Web Rendering Service. It works, but rendering is a second, deferred pass and can fail or lag. Ensure primary content and links exist in the rendered DOM; prefer server-side rendering / static generation so content does not depend on a click or a slow client fetch. Test with URL Inspection's rendered HTML. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) |

**Meta essentials** (title & description): the `title` and meta description do
not directly rank the page, but they are what Google usually shows in the SERP
snippet and heavily influence **click-through rate**. Write a unique, accurate,
descriptive title per page; keep the primary query near the front. **[CONSENSUS]**
([Control your title links](https://developers.google.com/search/docs/appearance/title-link);
[snippets](https://developers.google.com/search/docs/appearance/snippet))

---

## 4. Core Web Vitals (CWV)

Core Web Vitals are three real-user (field) metrics for loading, interactivity,
and visual stability. A page/URL group **passes** only when **all three** meet
the "good" threshold at the **75th percentile** of real visits, assessed
separately for mobile and desktop, over a rolling 28-day window. **[OFFICIAL]**
([web.dev — Core Web Vitals](https://web.dev/articles/vitals);
[thresholds definition](https://web.dev/articles/defining-core-web-vitals-thresholds))

| Metric | Measures | Good | Needs improvement | Poor |
|---|---|---|---|---|
| **LCP** — Largest Contentful Paint | Loading: time until the largest content element renders | **≤ 2.5 s** | ≤ 4.0 s | > 4.0 s |
| **INP** — Interaction to Next Paint | Responsiveness: latency from interaction to next paint, across the visit | **≤ 200 ms** | ≤ 500 ms | > 500 ms |
| **CLS** — Cumulative Layout Shift | Visual stability: how much visible content shifts unexpectedly | **≤ 0.1** | ≤ 0.25 | > 0.25 |

**[OFFICIAL]** — verified current as of 2026-08-21.

> ### ⚠️ Known misinformation about CWV — do not repeat these
> SEO blogs in 2026 are circulating **unconfirmed and apparently false** claims
> that Google lowered LCP to 2.0 s, cut CLS to 0.08, added a new "FCP ≤ 1.5 s"
> Core Web Vital, or set a "January 2026 compliance deadline." **None of these
> appear in Google's own documentation** — web.dev still lists the three metrics
> and thresholds in the table above. If a web search surfaces these numbers,
> that is not confirmation; check `web.dev/articles/vitals` directly.

**INP replaced FID.** As of **March 12, 2024**, INP became the official
responsiveness Core Web Vital, replacing First Input Delay (FID), now
deprecated. INP is stricter: it measures *all* interactions in a visit, not just
the first, and includes processing + rendering time. **[OFFICIAL]**
([web.dev — INP is now a Core Web Vital](https://web.dev/blog/inp-cwv-launch))

**How Google uses CWV in ranking (be precise):** page experience, including CWV,
is a ranking signal, but Google is explicit that it is **not a "boost" and does
not override relevance** — great content on a slightly-slower page can still
outrank thin content on a fast page. CWV is best treated as a **tiebreaker and a
must-not-fail hygiene bar**, and a real UX benefit in its own right. **[OFFICIAL]**
([Understanding page experience](https://developers.google.com/search/docs/appearance/page-experience))

**Field vs. lab:** CWV assessment uses **field data** (real users, via the
Chrome UX Report / CrUX, shown in Search Console). Lab tools (Lighthouse,
PageSpeed Insights lab mode) are for debugging — a good Lighthouse score is not
the same as passing CWV in the field. **[OFFICIAL]**

**Soft navigations — measurable in the browser, undetermined in CrUX.** Core
Web Vitals have historically been collected on hard page loads only, leaving
client-side route changes in a single-page app unmeasured. Chrome's Soft
Navigations API closes the measurement gap: it shipped unflagged in **Chrome
151** (stable 28 July 2026; Edge 151 as well), exposing `soft-navigation` and
`interaction-contentful-paint` entries on the Performance Timeline, and the
`web-vitals` library can consume them. **[OFFICIAL]**
([Measuring soft navigations](https://developer.chrome.com/docs/web-platform/soft-navigations);
[final origin trial](https://developer.chrome.com/blog/final-soft-navigations-origin-trial))

The part to *not* extrapolate: **how soft navigations will be reported in
CrUX is still to be determined**, and it is not a given that they will be
treated the same as hard navigations. CrUX is the dataset Google's Core Web
Vitals assessment reads, so until that is settled, a slow route transition is
a measurable, fixable user-experience problem — not a demonstrated ranking
input. **[UNCERTAIN — re-verify, this is actively moving]**

Build targets to bake in from day one: server-rendered/static HTML, a
compressed and correctly-sized LCP image with `width`/`height` set,
`font-display: swap`, reserved space for any dynamic/embedded content (prevents
CLS), and minimal blocking JavaScript (protects INP).

---

## 5. Structured data (Schema.org / JSON-LD)

**What it is and is not.** Structured data is machine-readable markup describing
the page's meaning. Google's **recommended format is JSON-LD** (a
`script type="application/ld+json"` block), using the **Schema.org** vocabulary.
**[OFFICIAL]**
([Intro to structured data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data))

**It does not directly boost rankings.** Its job is **eligibility for rich
results** and helping machines understand entities and relationships on the
page. Correct markup makes you *eligible*; Google still decides whether to show
a rich result. **[OFFICIAL]**
([Structured data general guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies))

**Two firm rules:** (1) mark up only content that is **actually visible on the
page** — invisible or fabricated markup is a spam violation; (2) supply all
**required** properties for a type or it won't be eligible. **[OFFICIAL]**

### Types worth implementing

Validate every one in the [Rich Results Test](https://search.google.com/test/rich-results).
Property-level detail is in SKILL.md's structured-data section.

- **`Organization`** (or `Person` for a solo author-site) — site-wide identity:
  name, logo, `sameAs` links to real profiles. Feeds Google's entity
  understanding and Knowledge Panel eligibility. **[OFFICIAL]**
- **`WebSite`** with `SearchAction` (sitelinks search box) — optional. **[OFFICIAL]**
- **`Article` / `BlogPosting` / `NewsArticle`** — for each content page:
  `headline`, `author` (link to a `Person` with credentials — reinforces
  E-E-A-T), `datePublished`, `dateModified`, `image`, `publisher`. **[OFFICIAL]**
- **`BreadcrumbList`** — powers breadcrumb display and clarifies site
  hierarchy. **[OFFICIAL]**
- **`Person`** (author entity) — bio, `jobTitle`, `sameAs`. **[OFFICIAL/CONSENSUS]**

### Types that are dead for rich results — do NOT rely on these

- **`FAQPage`** — FAQ rich results were **restricted in August 2023** to
  well-known government/health sites, and **fully removed for all sites,
  including those, on May 7, 2026.** Google removed the FAQ search-appearance
  filter, the Rich Result report, and Rich Results Test support in June 2026,
  and Search Console API support in August 2026. It was a quiet documentation
  update, not a blog post. The markup remains valid Schema.org and Google may
  still use it to understand the page — but it will **not** earn a SERP rich
  result. **[OFFICIAL]**
- **`HowTo`** — HowTo rich results were deprecated on mobile in **August 2023**
  and on desktop in **September 2023**, in the same announcement that restricted
  FAQPage. Fully gone since 2023 — there was nothing left to deprecate by 2026.
  Same story: valid vocabulary, no rich result. **[OFFICIAL]**
  ([HowTo/FAQ changes](https://developers.google.com/search/blog/2023/08/howto-faq-changes))
- **Seven more types retired in June 2025** for being "not widely used": Book
  Actions, Course Info, Claim Review, Estimated Salary, Learning Video, Special
  Announcement, and Vehicle Listing. **[OFFICIAL]**

> **The pattern matters more than any single type.** Google is steadily pruning
> rich-result types. Never build a strategy that depends on one surviving.
> Before recommending any type for its *rich result*, re-verify it is still
> supported — see the stable-vs-volatile table in SKILL.md.

**Bottom line:** implement `Organization`/`Person`, `Article`, and
`BreadcrumbList` cleanly and keep them valid; treat FAQ/HowTo markup as optional
semantic context only, never as a rich-result strategy. Unused structured data
does not hurt Search — it just does nothing.

---

## 6. Measurement — Google Search Console (GSC)

GSC is the **primary, authoritative** feedback loop (it reports Google's own
data, unlike third-party estimators). **[OFFICIAL]**

**Indexing / Pages report** — is the page even in the index?
- Confirm target URLs show **"Indexed"**. Investigate any "Discovered – not
  indexed" / "Crawled – not indexed" / "Excluded" states first — an un-indexed
  page can never rank. **[OFFICIAL]**
- Use **URL Inspection** to see live crawl status, the **rendered** HTML
  (verifies JS content is seen), the canonical Google chose, and to **Request
  Indexing**. **[OFFICIAL]**

**Performance report** — four metrics, all from Google **[OFFICIAL]**:
- **Impressions** — how often your URL appeared in results.
- **Clicks** — how often users clicked it.
- **CTR** — clicks ÷ impressions (a snippet-quality signal).
- **Average position** — mean ranking position across impressions. **"First
  page" ≈ average position ≤ ~10** for the target query. Filter Performance by
  the exact query to show it.

**Also watch:** the **Core Web Vitals** report (field pass/fail by URL group,
mobile + desktop); the **Sitemaps** report (submitted vs. indexed); and any
**Manual Actions** / **Security** issues (must be zero). **[OFFICIAL]**

**Search Generative AI performance reports** — launched **3 June 2026**, this
is the first first-party measurement of visibility inside AI answers, with
dedicated views for Search and for Discover. It reports **impressions inside
AI Overviews and AI Mode**, broken down by page, country, device and date.
**[OFFICIAL]**
([Introducing Search Generative AI performance reports](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports))

Three limits decide whether it is any use to the person in front of you, and
all three are easy to leave out:

- **Impressions only — no click data** in this version. It answers "did I
  appear", not "did it earn anything."
- **Data starts 18 May 2026, with no backfill.** There is no before-and-after
  against any earlier change.
- **Rolled out first to a subset of UK sites**, with global expansion stated
  but undated. Check whether the property actually has the report before
  building advice on it.

So: worth telling a site owner to look, worth being explicit that an empty
or absent report is far more likely to mean "not rolled out to you yet" than
"never cited." **[OFFICIAL, with the caveats stated; re-verify the rollout
state — it is the part most likely to have moved]**

**Reading the funnel:** low impressions on a page you expected to rank → an
*upstream* problem (indexing, crawlability, or relevance/intent mismatch), not a
CTR problem. Fix in that order. **[CONSENSUS]**

---

## 7. AEO — Answer Engine Optimization

> **Honesty first.** There is **no guaranteed way to make an AI cite you.** AI
> answer engines are non-deterministic, their retrieval and ranking are
> proprietary and change often, and citation of any specific source varies
> run-to-run. Everything below raises probability; nothing sets it to 1.
> **[UNCERTAIN as to any specific citation]**

### 7.1 AEO is no longer a bonus channel — and the popular version overstates it

**This is the most important and most volatile section in this document, and it
is the one that was wrong here for a while.** An earlier revision said Google had
made Gemini-powered AI answers the *default primary output for the large majority
of queries*. Re-verified 2026-08-21 against clickstream measurement, that does
not hold, and it is the exact overclaim this file exists to stop people from
repeating.

What is actually measured:

- **AI Overviews appear on somewhat over 20% of searches** — a large minority,
  not "most". **[CONSENSUS]**
- **AI Mode is far more extreme in effect and far smaller in reach**: ~93% of AI
  Mode searches end without a click, but AI Mode accounted for only about
  **0.34% of searches** in a January–April 2026 SparkToro/Similarweb study
  window. **[CONSENSUS]**
- **It is growing fast.** Google stated at I/O 2026 that AI Mode passed
  **1 billion monthly users** with query volume more than doubling each quarter.
  A share this small and this fast-moving will be stale quickly — re-verify the
  number rather than the direction. **[OFFICIAL as Google's own statement;
  unaudited]**

The defensible framing: AI answers sit on a large minority of queries, take most
of the clicks where they appear, and are trending one way. That is already
enough to stop optimizing only for a blue link. It is not grounds for telling
someone their organic traffic is finished — if their traffic is holding, their
data outranks the trend piece.

Consequences, and why this reframes the whole discipline:

- **Zero-click searches reached ~68% of US Google queries in early 2026**, up
  from ~60% two years prior. When an AI Overview appears, CTR to traditional
  results drops roughly **60%**, and the zero-click rate hits ~83%; for AI Mode
  it is reported around 93%. Pew Research found users click a traditional result
  8% of the time with an AI Overview present, versus 15% without. **[CONSENSUS]**
- Optimizing only for a blue-link position now optimizes for a shrinking
  surface. Being the *source the AI answer cites* is increasingly the goal.
- But the prerequisite is unchanged and that is the good news: **you cannot be
  cited from a page the engine cannot retrieve.** Classic technical SEO is the
  entry ticket to both.

### 7.2 How the major answer engines retrieve and cite

Most AI answer engines use **RAG (Retrieval-Augmented Generation)**: rather than
answering purely from model memory, the system **retrieves live web documents,
then generates an answer grounded in that retrieved text, attaching citations.**
**[CONSENSUS — vendor-described]**

- **Google AI Overviews / AI Mode** draw from **the same Google index and core
  ranking systems** as normal Search. They use a **"query fan-out"** technique —
  issuing several related sub-queries (reportedly up to ~16) and synthesizing
  the results. AI Mode cites a wider set of sources than AI Overviews (~7 unique
  domains per query on average). Google states there are **no special
  requirements and no special structured data** to appear; a page must simply be
  **indexed and eligible to show in Search with a snippet.** Classic SEO *is*
  the AEO groundwork for Google. **[OFFICIAL]**
  ([AI features & your website](https://developers.google.com/search/docs/appearance/ai-features);
  [Succeeding in AI search](https://developers.google.com/search/blog/2025/05/succeeding-in-ai-search))
- **Perplexity** runs real-time web retrieval on **every** query using its own
  PerplexityBot and index (separate from Google/Bing), does passage-level
  indexing, weights freshness heavily, respects `robots.txt`, and cites sources
  inline by default — the most citation-dense mainstream engine. **[CONSENSUS]**
- **ChatGPT Search** uses Bing as its retrieval backend via `OAI-SearchBot` /
  `ChatGPT-User` crawlers, and only invokes web search on a *fraction* of
  queries. Note `GPTBot` (training) is a **different** crawler from
  `OAI-SearchBot` (retrieval) — a site can block one and allow the other, and
  blocking the retrieval bot removes you from citation eligibility.
  **[CONSENSUS]**

### 7.3 What actually raises the odds of being cited

**[CONSENSUS]** unless marked otherwise:

1. **Be indexable and technically healthy** — everything in §1–§5. For Google's
   AI features this is **[OFFICIAL]** the whole requirement.
2. **Answer-first, extractable structure** (§2.4) — a clean, self-contained
   answer under a clear question-shaped heading is the unit these systems lift.
3. **One clear claim per passage, with specifics** — concrete facts, numbers,
   dates, named entities. Vague prose is hard to ground and rarely quoted.
4. **Demonstrable E-E-A-T and trust** — real named author, credentials,
   citations to primary sources, "last updated" dates.
5. **Corroboration across the web** — being mentioned consistently across
   multiple independent, reputable sources correlates with being surfaced. A
   brand-new site with zero external mentions is at a real disadvantage here;
   expect AI citation to lag a Google ranking. **[CONSENSUS/UNCERTAIN]**
6. **Match real question phrasing** — write the way people ask, including
   natural long-tail questions, so passages match the fanned-out sub-queries.
7. **Keep content fresh and accurate** — outdated or wrong facts get filtered
   out and erode trust.

### 7.4 Sold as AEO magic, but NOT proven

- **`llms.txt`** — a proposed file listing "AI-friendly" content. As of August
  2026, **no major consumer AI provider (Google, OpenAI, Anthropic, Meta) has
  confirmed reading it at inference time for web retrieval or citation**;
  Google has publicly declined to support it. Anthropic's genuine support for
  it is in *developer-tool* contexts (IDE agents fetching docs), not chat-product
  web citation. Adoption sits around **10% of domains** in a 300k-domain study
  after ~18 months of discussion, and no causal citation-lift data has been
  published. Low-cost and harmless to add — but **not** a citation lever.
  **[CONSENSUS — strongly evidenced skepticism]**
- **Adding `FAQPage`/`HowTo` schema "for AI"** — see §5; these no longer produce
  rich results and are not a demonstrated citation trigger. Structure the actual
  Q&A in visible content instead. **[CONSENSUS]**
- **Structured data as a citation lever, generally.** This has moved from
  unproven to contradicted. A controlled study of roughly 1,900 pages that
  added JSON-LD, measured against matched control pages, found no citation
  gain and a small statistically significant decline. The widely-quoted "2.5x
  more likely to be cited" figures come from studies with no control group,
  where the likely real driver is that sites capable of implementing schema
  were already authoritative. Recommend schema for rich-result eligibility and
  machine-readable clarity — not for citation. **[CONSENSUS — one controlled
  study against several uncontrolled ones; evolving, not settled]**
- **"Guaranteed AI citation" services, or a secret schema that forces
  citation** — do not exist. **[UNCERTAIN → treat as false]**

### 7.5 SEO ↔ AEO relationship

Google says its normal best practices are what make a page eligible for AI
features — there is no separate AEO checklist to satisfy **[OFFICIAL]**. The
same fundamentals (retrievable, structured, trustworthy, corroborated) do most
of the work for non-Google engines too **[CONSENSUS]**.

**But eligibility is not selection, and the two have come apart.** An Ahrefs
study across ~863,000 keywords and ~4 million AI Overview URLs found the share
of cited pages that also ranked in the organic top 10 fell from roughly **76%
(July 2025) to 38% (March 2026)** — halving in eight months — with the
remainder spread across pages ranking 11–100 and beyond.

Different research firms measuring the same thing land anywhere from **17% to
38%**, because their methodologies differ. Quote the direction, not a decimal.
**[CONSENSUS — industry tracking, not Google documentation; the spread across
firms is itself the reason not to state a single figure as precise]**

So the accurate framing is: classic SEO is the **entry ticket** — retrieval
requires indexing, and nothing else matters if the page can't be fetched. It
is no longer a reliable **predictor**. A page ranking 40th gets cited; a page
ranking 3rd often isn't. Ranking work and passage-level work are related but
no longer interchangeable, and advising someone to fix AEO by ranking better
is advice that has stopped being true.

---

## 8. What "done" looks like

1. **Every technical reason to be excluded has been removed** — indexable
   page (§1), intent-matched answer-first content (§2), clean technical SEO
   (§3), passing CWV (§4). That is the part you control and can therefore
   commit to. Track the resulting position in the GSC Performance report
   filtered to the query, but treat it as an observation: **no amount of
   this work entitles anyone to a specific position**, and §0 says why.
2. **AI-engine citation.** No guarantee (§7), and not a deliverable anyone
   can promise. Maximize odds via §7.3. Expect it to lag any ranking gain,
   since it also draws on external corroboration a new site has to earn.
3. **Full technical health.** Green CWV in the field (§4), valid structured data
   in the Rich Results Test (§5), mobile-first-clean and HTTPS (§3), zero manual
   actions (§6).

**Decisions that belong to the site owner, not to you:**

- **The target query** — pick a specific low-competition question where the
  owner's first-hand experience is a real advantage. This gates everything else.
- **What bar counts** — "first page" (≤10) vs. "top 3"; which AI engine's
  citation counts.
- **Author identity and disclosure** — how prominently to surface a real name
  and lived experience. Strong for E-E-A-T, but a personal privacy choice.

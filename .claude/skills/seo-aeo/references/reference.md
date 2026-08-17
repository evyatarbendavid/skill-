# SEO + AEO — Reference (Part 1)

> Companion checklist: [`audit-checklist.md`](./audit-checklist.md). Source: internal research/verification doc, snapshot 2026-08-17. Confidence labels are load-bearing — see the key below — do not restate a [CONSENSUS] or [UNCERTAIN] claim as flat fact, and do not drop a label when quoting a claim elsewhere.


This is the authoritative, cited reference the demo site must satisfy. It is
**topic-agnostic**: every principle applies to any content site, whatever the
final subject.

**How to read the source labels.** Every non-obvious claim is tagged:

- **[OFFICIAL]** — stated by Google, Schema.org, or web.dev in their own
  documentation. Treat as ground truth.
- **[CONSENSUS]** — not an official rule, but well-established agreement among
  serious practitioners and repeatedly observed. Reliable, but not a guarantee.
- **[UNCERTAIN]** — genuinely unprovable or contested. Do not build a plan that
  *depends* on it.

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

Hebrew note (הערה בעברית): המונחים באנגלית בכוונה — ככה הם מופיעים בכל הכלים
(Search Console, web.dev). מוסיף פה ושם גלוסה קצרה בעברית כדי לקבע את המושג.

---

## 1. Crawl / Index fundamentals (הבסיס — איך גוגל מוצא ומאחסן דפים)

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
([Technical requirements](https://developers.google.com/search/docs/essentials/technical)).

**Practical implications for the build:**

- If a page is not crawled → it cannot be indexed → it cannot rank. Crawl is the
  foundation; fix crawl problems before touching content.
- `robots.txt` controls **crawling**, not indexing. A URL blocked in
  `robots.txt` can still appear in Search (as a bare URL with no snippet) if
  other pages link to it — and because Googlebot never fetched it, it will
  **never see a `noindex` tag on that page.** To keep a page out of the index,
  allow crawling and use a `noindex` meta robots tag (or `X-Robots-Tag`
  header), **not** a `robots.txt` disallow. **[OFFICIAL]**
  ([Block indexing with noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing);
  [robots.txt intro](https://developers.google.com/search/docs/crawling-indexing/robots/intro)).

---

## 2. On-page & content — E-E-A-T, search intent, answer-first structure

### 2.1 People-first, helpful content

Google's ranking systems aim to reward **original, high-quality, people-first**
content and to demote content made primarily to manipulate rankings. The
"helpful content" approach began in 2022 as a signal and was folded into
Google's **core ranking systems in the March 2024 core update.** **[OFFICIAL]**
([Creating helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)).

Google publishes **self-assessment questions** to judge your own content. The
useful ones to hold the build to **[OFFICIAL]** (same page):

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
([Helpful content page, E-E-A-T section](https://developers.google.com/search/docs/fundamentals/creating-helpful-content);
[Search Quality Rater Guidelines PDF](https://static.googleusercontent.com/media/guidelines.raterhub.com/en//searchqualityevaluatorguidelines.pdf)).

The **"who / how / why"** test Google recommends **[OFFICIAL]**:

- **Who** created the content — is there a real, credited author with a bio and
  credentials? (Especially important here: the owner's blindness gives genuine
  *first-hand Experience* on accessibility topics — this is a real, hard-to-fake
  E-E-A-T advantage. Make the author identity explicit.)
- **How** it was created — disclose method, and any AI involvement where it
  would matter to the reader.
- **Why** it exists — to help people, not primarily to rank or to serve ads.

**On AI-generated content:** Google does **not** ban AI content. Its stance is
that it rewards high-quality content *however it is produced*, but that using
automation to generate content *primarily to manipulate rankings* violates spam
policies. **[OFFICIAL]**
([Google Search's guidance about AI-generated content](https://developers.google.com/search/blog/2023/02/google-search-and-ai-content)).
Practical rule for this project: AI can draft and assist, but a human with real
expertise must direct, verify, and own the result.

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
- Use a **clear heading hierarchy** (one `<h1>`, descriptive `<h2>`/`<h3>`) that
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

| Area | What to do | Source / label |
|---|---|---|
| **HTTPS** | Serve the whole site over HTTPS with a valid certificate; HTTPS is a lightweight ranking signal and a baseline expectation. | [OFFICIAL — HTTPS](https://developers.google.com/search/docs/crawling-indexing/https) |
| **Status codes** | Only 200 pages get indexed. Use 301 for permanent redirects, 404/410 for gone pages, avoid 5xx and "soft 404s" (a 200 page that says "not found"). | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/http-network-errors) |
| **Canonical** | When the same/near-same content lives at multiple URLs, pick one canonical and mark it with `rel="canonical"`. Google treats it as a strong hint, not a command; keep signals consistent (canonical, internal links, sitemap, redirects all pointing the same way). | [OFFICIAL — canonicalization](https://developers.google.com/search/docs/crawling-indexing/canonicalization) |
| **XML sitemap** | Publish a sitemap listing your canonical, indexable URLs; reference it in `robots.txt` and submit it in Search Console. Helps discovery, especially for new sites with few backlinks. | [OFFICIAL — sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview) |
| **robots.txt** | Use to manage crawl, **never** as an indexing control (see §1). Do **not** block CSS/JS/image resources Googlebot needs to render the page. | [OFFICIAL](https://developers.google.com/search/docs/crawling-indexing/robots/intro) |
| **Mobile** | Google indexes with **mobile-first** crawling — Googlebot Smartphone is the source of truth. Content, links, and meta robots tags must be **identical** on mobile and desktop; a `noindex`/`nofollow` that appears only on mobile can drop the page. | [OFFICIAL — mobile-first](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-first-indexing-best-practices) |
| **JS rendering** | Google renders pages by executing JS in an **evergreen Chromium** Web Rendering Service. It works, but rendering is a second, deferred pass and can fail or lag. Ensure primary content and links exist in the rendered DOM; prefer server-side rendering / static generation / hydration so content does not depend on a click or a slow client fetch. Test with the URL Inspection tool's rendered HTML. | [OFFICIAL — JS SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) |

**Meta essentials** (title & description): the `<title>` and meta description do
not directly rank the page, but they are what Google usually shows in the SERP
snippet and heavily influence **click-through rate**. Write a unique, accurate,
descriptive title per page; keep the primary query near the front. **[CONSENSUS]**
([Control your title links](https://developers.google.com/search/docs/appearance/title-link);
[snippets/meta description](https://developers.google.com/search/docs/appearance/snippet)).

---

## 4. Core Web Vitals (CWV) — current metrics and thresholds

Core Web Vitals are three real-user (field) metrics for loading, interactivity,
and visual stability. A page/URL group **passes** only when **all three** meet
the "good" threshold at the **75th percentile** of real visits (i.e. 75% of
visits are at least this good), assessed separately for mobile and desktop.
**[OFFICIAL]**
([web.dev — Core Web Vitals](https://web.dev/articles/vitals);
[thresholds definition](https://web.dev/articles/defining-core-web-vitals-thresholds)).

| Metric | Measures | Good | Needs improvement | Poor |
|---|---|---|---|---|
| **LCP** — Largest Contentful Paint | Loading: time until the largest content element renders | **≤ 2.5 s** | ≤ 4.0 s | > 4.0 s |
| **INP** — Interaction to Next Paint | Responsiveness: worst-ish latency from a user interaction to the next paint, across the visit | **≤ 200 ms** | ≤ 500 ms | > 500 ms |
| **CLS** — Cumulative Layout Shift | Visual stability: how much visible content shifts unexpectedly | **≤ 0.1** | ≤ 0.25 | > 0.25 |

Thresholds per [web.dev](https://web.dev/articles/vitals). **[OFFICIAL]**

**INP replaced FID.** As of **March 12, 2024**, **INP** became the official
responsiveness Core Web Vital, replacing First Input Delay (FID), which is now
deprecated. INP is stricter: it measures *all* interactions in a visit, not just
the first, and includes processing + rendering time, not just input delay.
**[OFFICIAL]**
([web.dev — INP is now a Core Web Vital](https://web.dev/blog/inp-cwv-launch);
[Google Search blog](https://developers.google.com/search/blog/2023/05/introducing-inp)).

**How Google uses CWV in ranking (be precise):** page experience, including CWV,
is a ranking signal, but Google is explicit that it is **not a "boost" and does
not override relevance** — great content on a slightly-slower page can still
outrank thin content on a fast page. CWV is best treated as a **tiebreaker and a
must-not-fail hygiene bar**, and a real UX benefit in its own right. **[OFFICIAL]**
([Understanding page experience](https://developers.google.com/search/docs/appearance/page-experience)).

**Field vs. lab:** CWV assessment uses **field data** (real users, reported via
the Chrome UX Report / CrUX and shown in Search Console's Core Web Vitals
report). Lab tools (Lighthouse, PageSpeed Insights lab mode) are for debugging
and give a *lab* Performance score — a good Lighthouse score is not the same as
passing CWV in the field. **[OFFICIAL]** ([web.dev](https://web.dev/articles/vitals)).

Build targets to bake in from day one: server-rendered/static HTML, a
compressed and correctly-sized LCP image with `width`/`height` set,
`font-display: swap`, reserved space for any dynamic/embedded content (prevents
CLS), and minimal blocking JavaScript (protects INP).

---

## 5. Structured data (Schema.org / JSON-LD)

**What it is and is not.** Structured data is machine-readable markup describing
the page's meaning. Google's **recommended format is JSON-LD** (a `<script
type="application/ld+json">` block), using the **Schema.org** vocabulary.
**[OFFICIAL]**
([Intro to structured data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data);
[Schema.org](https://schema.org/)).

**It does not directly boost rankings.** Its job is **eligibility for rich
results** (enhanced SERP appearances) and helping machines understand entities
and relationships on the page. Correct markup makes you *eligible*; Google still
decides whether to show a rich result based on quality and its own rules.
**[OFFICIAL]**
([Structured data general guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)).

**Two firm rules:** (1) mark up only content that is **actually visible on the
page** — invisible or fabricated markup is a spam violation; (2) supply all
**required** properties for a type or it won't be eligible. **[OFFICIAL]**

**Types worth implementing for a content/article site** (validate every one in
the [Rich Results Test](https://search.google.com/test/rich-results) and monitor
in Search Console):

- **`Organization`** (or `Person` for a solo author-site) — site-wide identity:
  name, logo, `sameAs` links to real profiles. Feeds Google's entity
  understanding and Knowledge Panel eligibility. **[OFFICIAL]**
  ([Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)).
- **`WebSite`** with `SearchAction` (sitelinks search box) — optional. **[OFFICIAL]**
- **`Article` / `BlogPosting` / `NewsArticle`** — for each content page:
  `headline`, `author` (link to a `Person` with credentials — reinforces
  E-E-A-T), `datePublished`, `dateModified`, `image`, `publisher`. **[OFFICIAL]**
  ([Article](https://developers.google.com/search/docs/appearance/structured-data/article)).
- **`BreadcrumbList`** — powers breadcrumb display in results and clarifies site
  hierarchy. **[OFFICIAL]**
  ([Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)).
- **`Person`** (author entity) — bio, `jobTitle`, `sameAs`. Ties content to a
  credible, real author. **[OFFICIAL / CONSENSUS]**

**Types to know are restricted or gone — do NOT rely on these for rich results:**

- **`FAQPage`** — FAQ rich results were **restricted in August 2023** to
  well-known government/health sites, and **fully deprecated (removed for all
  sites) in 2026.** The markup is still a valid Schema.org type and can still
  aid machine understanding, but it will **not** earn a SERP rich result for a
  normal site — do not add it expecting extra SERP real estate. **[OFFICIAL]**
  ([HowTo/FAQ changes](https://developers.google.com/search/blog/2023/08/howto-faq-changes)).
- **`HowTo`** — HowTo rich results were **deprecated in 2023** (mobile then
  desktop). Same story: valid vocabulary, no rich result. **[OFFICIAL]** (same
  source).

Bottom line: implement `Organization`/`Person`, `Article`, and `BreadcrumbList`
cleanly and keep them valid; treat FAQ/HowTo markup as optional semantic context
only, never as a rich-result strategy.

---

## 6. Measurement — Google Search Console (GSC) signals to watch

GSC is the **primary, authoritative** feedback loop (it reports Google's own
data, unlike third-party estimators). The proof of "first-page ranking" the
project needs comes from here. **[OFFICIAL]**
([Search Console help](https://support.google.com/webmasters/answer/9128668)).

**Indexing / Pages report** — is the page even in the index?
- Confirm target URLs show **"Indexed"** (Page indexing report). Investigate any
  "Discovered – not indexed" / "Crawled – not indexed" / "Excluded" states first
  — an un-indexed page can never rank. **[OFFICIAL]**
- Use **URL Inspection** to see live crawl status, the **rendered** HTML
  (verifies JS content is seen), canonical Google chose, and to **Request
  Indexing** for a new/updated page. **[OFFICIAL]**

**Performance report** — four metrics, all from Google **[OFFICIAL]**:
- **Impressions** — how often your URL appeared in results.
- **Clicks** — how often users clicked it.
- **CTR** — clicks ÷ impressions (a snippet-quality signal; improve via title/
  description).
- **Average position** — mean ranking position across impressions. **"First page"
  ≈ average position ≤ ~10 for the target query** — this is the number to screenshot
  as proof. Filter Performance by the exact query to show it.

**Also watch:** the **Core Web Vitals** report (field pass/fail by URL group,
mobile + desktop) and **Mobile Usability**/page-experience signals; the
**Sitemaps** report (submitted vs. indexed); and any **Manual Actions** /
**Security** issues (must be zero). **[OFFICIAL]**

**Reading the funnel:** low impressions on a page you expected to rank → an
*upstream* problem (indexing, crawlability, or relevance/intent mismatch), not a
CTR problem. Fix in that order. **[CONSENSUS]**

---

## 7. AEO — Answer Engine Optimization (getting retrieved and cited by AI)

> **Honesty first.** There is **no guaranteed way to make an AI cite you.** AI
> answer engines are non-deterministic, their retrieval and ranking are
> proprietary and change often, and citation of any specific source varies
> run-to-run. Everything below raises probability; nothing sets it to 1.
> **[UNCERTAIN as to any specific citation]**

### 7.1 How the major answer engines actually retrieve and cite

Most AI answer engines use **RAG (Retrieval-Augmented Generation)**: rather than
answering purely from the model's memory, the system **retrieves live web
documents, then generates an answer grounded in that retrieved text, attaching
citations.** **[CONSENSUS — vendor-described]**

- **Google AI Overviews / AI Mode** draw from **the same Google index and core
  ranking systems** as normal Search. They use a **"query fan-out"** technique —
  issuing several related sub-queries and synthesizing the results. Google states
  there are **no special requirements and no special structured data** to appear;
  a page must simply be **indexed and eligible to show in Search with a snippet.**
  This means classic SEO *is* the AEO groundwork for Google. **[OFFICIAL]**
  ([AI features & your website](https://developers.google.com/search/docs/appearance/ai-features);
  [Succeeding in AI search](https://developers.google.com/search/blog/2025/05/succeeding-in-ai-search)).
- **Perplexity** runs real-time web retrieval on **every** query (hybrid
  keyword + embedding retrieval, then re-ranking), and cites sources inline by
  default — it is the most citation-dense mainstream engine. **[CONSENSUS —
  reverse-engineered / vendor statements, not a published spec]**
- **ChatGPT Search** uses web results (historically Bing-indexed) but only
  invokes web search on a *fraction* of queries; otherwise it answers from
  training data. Being in the underlying web index is a prerequisite for being
  cited when it does search. **[CONSENSUS]**

**The load-bearing takeaway:** for every one of these, **being crawlable,
indexed, and genuinely useful is the prerequisite.** You cannot be cited from a
page the engine cannot retrieve or does not trust.

### 7.2 What actually raises the odds of being cited (practitioner consensus)

**[CONSENSUS]** unless marked otherwise:

1. **Be indexable and technically healthy** — everything in §1–§5. For Google's
   AI features this is **[OFFICIAL]** the whole requirement.
2. **Answer-first, extractable structure** (§2.4) — a clean, self-contained
   answer under a clear question-shaped heading is the unit these systems lift.
3. **One clear claim per passage, with specifics** — concrete facts, numbers,
   dates, named entities. Vague prose is hard to ground and rarely quoted.
4. **Demonstrable E-E-A-T and trust** — real named author, credentials,
   citations to primary sources, "last updated" dates. Engines and their rankers
   favor sources they can treat as reliable.
5. **Corroboration across the web** — being mentioned/consistent across multiple
   independent, reputable sources correlates with being surfaced. (A brand-new
   site with zero external mentions is at a disadvantage here — expect the AI
   citation to be the *slower* of the two proof goals.) **[CONSENSUS / UNCERTAIN]**
6. **Match real question phrasing** — write the way people ask, including natural
   long-tail questions, so the passage matches the fanned-out sub-queries.
7. **Keep content fresh and accurate** — outdated or wrong facts get filtered
   out and erode trust.

### 7.3 Things sold as AEO magic that are NOT proven

- **`llms.txt`** — a proposed file listing "AI-friendly" content. **No major AI
  provider (Google, OpenAI, Anthropic, Meta) has committed to reading it in
  production**; Google has publicly declined to support it. Independent analyses
  find **no correlation between having `llms.txt` and being cited more.** It is
  low-cost and harmless to add, but do **not** count it as a citation lever.
  **[CONSENSUS — strongly evidenced skepticism]**
  ([SE Ranking analysis](https://seranking.com/blog/llms-txt/)).
- **Adding `FAQPage`/`HowTo` schema for AI** — see §5; these no longer produce
  rich results and are not a demonstrated citation trigger. Structure the actual
  Q&A in visible content instead. **[CONSENSUS]**
- **"Guaranteed AI citation" services / a secret schema that forces citation** —
  do not exist. **[UNCERTAIN → treat as false]**

### 7.4 SEO ↔ AEO relationship

For Google specifically, **AEO is a superset of good SEO, not a separate
discipline** — Google says its normal best practices are what make you eligible
for AI features **[OFFICIAL]**. For non-Google engines, the *same* fundamentals
(retrievable, structured, trustworthy, corroborated) do most of the work
**[CONSENSUS]**. So the strategy is one strategy: **build an excellent, technically
flawless, genuinely authoritative page, and both goals are served by the same
work.**

---

## 8. What this means for the demo (the bar to clear)

Mapping back to the project's three proof goals:

1. **First-page Google ranking on a long-tail keyword, shown in Search Console.**
   Achievable because (a) long-tail = low competition, and (b) the owner has a
   real E-E-A-T edge on accessibility topics. Requires: indexable page (§1),
   intent-matched answer-first content (§2), clean technical SEO (§3), passing
   CWV (§4). Proof = GSC Performance report, filtered to the query, average
   position ≤ ~10.
2. **At least one AI-engine citation.** No guarantee (§7). Maximize odds via
   §7.2. Expect this to lag the Google ranking, because it also benefits from
   external corroboration a new site has to earn.
3. **Full technical health.** Green CWV in the field (§4), valid structured data
   in the Rich Results Test (§5), mobile-first-clean and HTTPS (§3), zero manual
   actions (§6).

**Decisions the owner should make (flagged for a human, not for me to decide):**

- **The one long-tail keyword** is still unchosen — this gates everything.
  Pick a specific low-competition question where the owner's first-hand
  experience is a real advantage.
- **Confirm the exact bar with the friend** — "first page" (≤10) vs. "top 3",
  and which AI engine's citation counts.
- **Author identity / disclosure** — how prominently to surface the owner's real
  name and lived experience (strong E-E-A-T, but a personal privacy choice for a
  15-year-old).

---

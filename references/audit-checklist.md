# SEO + AEO audit checklist

Audit **one page** objectively. Each item is written so the answer is
**PASS / FAIL / N/A**, with *how to check* named. Companion reference (the *why*
plus sources): [`sources.md`](./sources.md).

**Scoring rule.** The **gates** are five specific items, not whole sections:
**A1** (HTTP 200), **A2** (not blocked in robots.txt), **A3** (no `noindex`),
**A8** (content in the served HTML), and **D** (Core Web Vitals). A FAIL on any
of those means the page cannot rank at all — fix them before anything else.

Everything else, including the rest of section A, is a **quality multiplier**:
important, sometimes urgent, but not blocking. A page with no canonical still
ranks — Google picks one. A page missing from the sitemap still ranks — a
sitemap aids discovery, it is not an entry requirement. Calling those gates
spends the word that is supposed to mean *stop everything*, and a reader who
learns the label is inflated stops believing it on the item where it's true.

Aim for **100% of gates + ≥90% of the rest** before calling a page "done."

**Before you start: check what you can actually do.** Several items below
need a tool you may not have. Where you don't have it, say so and hand the
person the exact thing to open — then work from what they bring back. Never
report a check as passed when you couldn't run it, and never estimate a
measurement you couldn't take.

| Item needs | You can do it if you have | Otherwise |
|---|---|---|
| Fetching the page or its `robots.txt`/`sitemap.xml` | web access | Ask for `view-source:` output, or the file contents pasted |
| Status codes and headers (`curl -I`) | a shell | Ask them to run it, or check in the browser's Network tab |
| Core Web Vitals field data | web access to the PageSpeed API | Send them `https://pagespeed.web.dev/analysis?url=<URL>` |
| Rich Results Test | web access | Send them `https://search.google.com/test/rich-results` |
| **Search Console** — A6, A5's "submitted", P1, P3 | never — it needs their login | Always the site owner's to check. Tell them exactly what to look at. |
| Lighthouse, DevTools — D8, E6, E7 | a browser you drive | Theirs to run |

Search Console items are marked below. They are not failures of the audit;
they are the parts only the owner can see.

---

## A. Crawlability & Indexing (holds four of the five gates)

- [ ] **A1. Returns HTTP 200.** *(GATE.)* `curl -I <url>` shows `200`. No 3xx chain to the
  final URL, no 4xx/5xx. *(Only 200 pages get indexed.)*
- [ ] **A2. Not blocked in `robots.txt`.** *(GATE.)* The URL and its CSS/JS/image resources
  are crawlable. Check `/robots.txt` and URL Inspection → "Crawl allowed? Yes".
- [ ] **A3. Indexable directives.** *(GATE.)* Page has **no** `noindex` (meta robots or
  `X-Robots-Tag` header). Verify in rendered HTML *and* response headers, not
  just source.
- [ ] **A4. Self-referencing / correct canonical.** `link rel="canonical"`
  points to this page's preferred URL (or the intended canonical). Google's
  chosen canonical (URL Inspection) matches your intent.
- [ ] **A5. In an XML sitemap** that is submitted in Search Console, and the
  sitemap lists the canonical URL (not a redirecting/duplicate variant).
- [ ] **A6. Actually indexed.** *(Owner-only — needs Search Console.)* URL Inspection / Page indexing report says
  **"URL is on Google" / Indexed** — not "Discovered/Crawled – currently not
  indexed" or "Excluded". *(Not automatable — requires Search Console access.)*
- [ ] **A7. Reachable by internal links.** At least one crawlable `a href` from
  another indexed page points here (not orphaned, not JS-only navigation).
- [ ] **A8. Content present in rendered DOM.** *(GATE.)* URL Inspection → "View rendered
  HTML" (or DevTools Elements) shows the main text and links — i.e. content does
  not depend on a user action or a failed client fetch.

## B. Content & Search Intent (תוכן וכוונת חיפוש)

- [ ] **B1. One primary query/topic** per page; the page's purpose is obvious.
- [ ] **B2. Intent match.** The page format (guide / list / definition / tool)
  matches what already ranks on page 1 for the target query. *(Check by
  searching the query and eyeballing the top results.)*
- [ ] **B3. Answer-first.** A direct, self-contained answer appears in the first
  1–3 sentences (and under each major heading) before background/caveats.
- [ ] **B4. Heading hierarchy.** Exactly one `h1`; logical `h2`/`h3`; headings
  phrased as the questions a reader would ask where natural.
- [ ] **B5. Original value.** Contains first-hand experience, original analysis,
  specifics (numbers, dates, named entities) — not a rehash of other pages.
- [ ] **B6. Named, credible author.** Visible author with bio/credentials; a
  "last updated" date; sources cited for factual claims. *(E-E-A-T / trust.)*
- [ ] **B7. Complete.** A reader finishes without needing to search again for the
  same task.
- [ ] **B8. Unique, descriptive `title`** (primary query near the front) and a
  compelling meta description. Not duplicated across pages.
- [ ] **B9. Descriptive URL slug** (words, hyphens, no junk parameters).
- [ ] **B10. Accurate & current.** No factual errors; no stale claims. For
  YMYL-ish topics (health/safety/money) accuracy is non-negotiable.

## C. Structured Data (נתונים מובנים)

- [ ] **C1. JSON-LD present** (`script type="application/ld+json"`), using
  Schema.org vocabulary. *(JSON-LD is Google's recommended format.)*
- [ ] **C2. Validates** in the Rich Results Test with **zero errors** (warnings
  acceptable). No "invalid"/missing required properties.
- [ ] **C3. `Article`/`BlogPosting`** on content pages with `headline`, `author`
  (→ `Person`), `datePublished`, `dateModified`, `image`, `publisher`.
- [ ] **C4. `Organization` or `Person`** site identity present (name, logo,
  `sameAs` to real profiles).
- [ ] **C5. `BreadcrumbList`** present and matches the visible breadcrumb / site
  hierarchy.
- [ ] **C6. Markup mirrors visible content only** — nothing marked up that isn't
  on the page; no fabricated data. *(Spam-policy violation otherwise.)*
- [ ] **C7. No reliance on dead rich-result types.** Not counting on
  `FAQPage`/`HowTo` for a SERP rich result (both deprecated — see reference §5).
  If used, it's for semantic context only and reflects real on-page Q&A.

## D. Performance / Core Web Vitals (GATE — ביצועים; all of D is a gate)

*Judge on **field** data (PageSpeed Insights "real users" / GSC Core Web Vitals),
mobile first. Lab scores are for debugging only.*

- [ ] **D1. LCP ≤ 2.5 s** at the 75th percentile (field). *(Good.)*
- [ ] **D2. INP ≤ 200 ms** at the 75th percentile (field). *(Good; INP replaced
  FID in March 2024.)*
- [ ] **D3. CLS ≤ 0.1** at the 75th percentile (field). *(Good.)*
- [ ] **D4. Passes on BOTH mobile and desktop** (assessed separately).
- [ ] **D5. LCP image optimized** — compressed, correctly sized, explicit
  `width`/`height`, not lazy-loaded, ideally `preload`ed.
- [ ] **D6. No layout shift sources** — images/embeds/ads have reserved
  dimensions; web fonts use `font-display: swap`.
- [ ] **D7. Minimal blocking JS** — main thread not overloaded (protects INP);
  defer/async non-critical scripts.
- [ ] **D8. Lighthouse mobile Performance** used only to *diagnose* D1–D3 (note:
  a green Lighthouse score ≠ passing field CWV).

> **Thresholds are volatile.** Confirm D1–D3 against [web.dev/articles/vitals](https://web.dev/articles/vitals)
> before reporting them as current — and see the known-misinformation box in
> `sources.md` §4 for the fake numbers circulating online.

## E. Accessibility & Mobile (נגישות ומובייל)

- [ ] **E1. Mobile parity** — same content, links, and meta-robots on mobile and
  desktop *(mobile-first indexing uses the mobile version as source of truth)*.
- [ ] **E2. Responsive, no horizontal scroll**, tap targets adequately sized,
  legible base font.
- [ ] **E3. HTTPS** with a valid certificate across the whole page (no mixed
  content).
- [ ] **E4. Semantic HTML & landmarks** — real `h1`/headings, `nav`, `main`,
  lists; proper reading order.
- [ ] **E5. Images have meaningful `alt`** text (decorative images `alt=""`).
- [ ] **E6. Keyboard operable** — all interactive elements reachable/usable by
  keyboard, visible focus states.
- [ ] **E7. Sufficient color contrast** (WCAG AA: 4.5:1 body text).
- [ ] **E8. Accessible names / ARIA** where needed; forms have labels.
- [ ] **E9. `lang` attribute set** (`html lang="…"`), correct for the content
  language.
- [ ] **E10. Screen-reader spot check** passes.

## F. AEO-readiness (סיכוי להיות מצוטט ע״י מנועי AI — probabilistic, NOT guaranteed)

*No item here guarantees a citation. They raise the odds. A hard requirement for
Google's AI features is simply: the page passes A–E and is eligible to show with
a snippet.*

- [ ] **F0. AI retrieval crawlers are not blocked** (a gate for AEO specifically — it blocks citation, not ranking). Check
  `robots.txt` for `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`. These
  are **not** the training crawlers — blocking `GPTBot` or `ClaudeBot` opts out
  of model training and changes nothing about AI answers, while blocking the
  retrieval bots removes the site from those answers entirely. Sites do this to
  themselves by accident. Say which kind you found; don't lump them together.
  See [`ai-crawlers.md`](./ai-crawlers.md).
- [ ] **F1. Retrievable** — passes all of Section A (an AI cannot cite what it
  can't retrieve/index). *(For Google AI Overviews/AI Mode this is the whole
  official requirement. Note that eligibility is not selection: ranking top-10
  no longer predicts citation the way it did.)*
- [ ] **F2. Extractable answer chunks** — self-contained answers under
  question-shaped headings (ties to B3/B4); short paragraphs, lists, tables for
  facts/steps.
- [ ] **F3. One clear claim per passage**, with concrete specifics (facts,
  numbers, dates, named entities) that a model can ground a citation on.
- [ ] **F4. Question-phrased content** matching how people actually ask (natural
  long-tail phrasing appears in visible text), **and the adjacent questions
  answered too** — comparison, price, setup steps. Fan-out retrieves passages
  for the sub-questions, not only the literal query.
- [ ] **F4b. The answer is high on the page**, not only early in its section.
  Citations cluster heavily in the top third of a page.
- [ ] **F5. Trust signals present** — named expert author, credentials, primary
  sources cited, clear "last updated" (ties to B6).
- [ ] **F6. External corroboration exists or is being built** — the page's key
  facts are consistent with, and ideally referenced by, other reputable sources.
  *(Weakest for a brand-new site; expect AI citation to lag the Google ranking.)*
- [ ] **F7. Not relying on unproven or contradicted levers** — `llms.txt`
  (Google has said Search does not use it), FAQ/HowTo schema (switched off at
  the platform level), structured data as a citation driver (one controlled
  study found no gain and a small decline), or any "guaranteed citation"
  service. Harmless to have; not the plan.
- [ ] **F8. Realistic target chosen.** On general consumer queries a handful of
  large community and reference platforms take most citations, and a business
  page will not displace them. The winnable ground is specific, technical, or
  branded questions. Say so rather than promising head terms.

## G. Content quality, RTL & site hygiene (איכות תוכן ובאגים)

*The "boring but costly" category. Several of these are accessibility bugs
first and SEO bugs second — fixing them pays twice.*

- [ ] **G1. No placeholder text in production.** No `Lorem ipsum`, `TODO`,
  `undefined`, `[object Object]`, `NaN`, or untranslated strings in visible copy.
- [ ] **G2. Title length** ~50–60 chars. Longer gets truncated in results;
  much shorter wastes the slot.
- [ ] **G3. Meta description length** ~140–160 chars, written as CTR copy.
  It does not affect ranking directly — it affects whether anyone clicks.
- [ ] **G4. Single-hop redirects.** No A→B→C chains; collapse to A→C and link
  to the final URL.
- [ ] **G5. Descriptive anchor text.** No "click here" / "read more" /
  "לחץ כאן". Anchor text is both a ranking signal and a screen-reader cue.
- [ ] **G6. Image attributes.** Explicit `width`/`height` (prevents CLS),
  hero image **not** lazy-loaded (protects LCP), modern formats (WebP/AVIF).
- [ ] **G7. RTL / bidi correctness.** `html lang="he" dir="rtl"` both set and
  agreeing; Latin text, numbers, and brand names inside RTL runs isolated with
  `bdi` or `dir="auto"` so they do not render in the wrong visual order.
  Check nested components too — LTR-authored component libraries often hardcode
  their own `dir`.
- [ ] **G8. No orphan pages.** Every sitemap URL is reachable by following
  internal links. Orphans are live and declared but accumulate no internal
  signal.
- [ ] **G9. No duplicate content at scale.** On templated/programmatic page
  sets, pages that differ only by a swapped noun share the same fate: search
  engines may index only one. *(Reported via crawl duplicate detection.)*
- [ ] **G10. One canonical host.** http→https and www↔non-www 301-redirect to
  a single host rather than dual-serving the same content.

---

### Proof artifacts to capture *(all owner-only — these need Search Console access and live measurement, so they are things to hand the owner, not things to report as done)*

- [ ] **P1. Ranking position, tracked over time** — Search Console →
  Performance, filtered to the exact target query. Record where it actually
  is and which way it's moving. **This is a measurement, not a target you
  commit to hitting** — nobody can promise a position, and a checklist that
  reads like they can is the thing this skill exists to avoid.
- [ ] **P2. AI citation** — a screenshot of ChatGPT / Perplexity / Google AI
  Overview answer that links to the page. *(May take longer; not guaranteed.)*
- [ ] **P3. Technical health** — Rich Results Test = valid; PageSpeed/GSC CWV =
  all green (mobile + desktop); GSC = indexed, zero manual actions.

---

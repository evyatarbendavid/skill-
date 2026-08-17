# SEO + AEO — Audit Checklist (Part 2)

> Companion reference (the *why* + sources): [`reference.md`](./reference.md). Use this to audit **one page** objectively — every item is answerable PASS / FAIL / N/A, with how to check named.


Each item is written so the answer is **PASS / FAIL / N/A**, with *how to check*
named — this is meant to be walked through mechanically, page by page.

**Scoring rule.** Sections A (Crawlability) and D (Performance/CWV) are
**gates** — any FAIL there means the page cannot reliably rank, fix first.
Sections B, C, E, F are quality multipliers. Aim for **100% of gates + ≥90% of
the rest** before calling a page "done."

**Tools you'll use (all free):**
- Google Search Console → URL Inspection, Performance, Page indexing, Core Web Vitals
- [Rich Results Test](https://search.google.com/test/rich-results)
- [PageSpeed Insights](https://pagespeed.web.dev/) (field CrUX data + lab)
- Chrome DevTools (Lighthouse, device toolbar, Elements = rendered DOM)
- `view-source:` + the live URL; `curl -I <url>` for status/headers

---

## A. Crawlability & Indexing (GATE — כניסה לאינדקס)

- [ ] **A1. Returns HTTP 200.** `curl -I <url>` shows `200`. No 3xx chain to the
  final URL, no 4xx/5xx. *(Only 200 pages get indexed.)*
- [ ] **A2. Not blocked in `robots.txt`.** The URL and its CSS/JS/image resources
  are crawlable. Check `/robots.txt` and URL Inspection → "Crawl allowed? Yes".
- [ ] **A3. Indexable directives.** Page has **no** `noindex` (meta robots or
  `X-Robots-Tag` header). Verify in rendered HTML *and* response headers, not
  just source.
- [ ] **A4. Self-referencing / correct canonical.** `<link rel="canonical">`
  points to this page's preferred URL (or the intended canonical). Google's
  chosen canonical (URL Inspection) matches your intent.
- [ ] **A5. In an XML sitemap** that is submitted in Search Console, and the
  sitemap lists the canonical URL (not a redirecting/duplicate variant).
- [ ] **A6. Actually indexed.** URL Inspection / Page indexing report says
  **"URL is on Google" / Indexed** — not "Discovered/Crawled – currently not
  indexed" or "Excluded".
- [ ] **A7. Reachable by internal links.** At least one crawlable `<a href>` from
  another indexed page points here (not orphaned, not JS-only navigation).
- [ ] **A8. Content present in rendered DOM.** URL Inspection → "View rendered
  HTML" (or DevTools Elements) shows the main text and links — i.e. content does
  not depend on a user action or a failed client fetch.

## B. Content & Search Intent (תוכן וכוונת חיפוש)

- [ ] **B1. One primary query/topic** per page; the page's purpose is obvious.
- [ ] **B2. Intent match.** The page format (guide / list / definition / tool)
  matches what already ranks on page 1 for the target query. *(Check by
  searching the query and eyeballing the top results.)*
- [ ] **B3. Answer-first.** A direct, self-contained answer appears in the first
  1–3 sentences (and under each major heading) before background/caveats.
- [ ] **B4. Heading hierarchy.** Exactly one `<h1>`; logical `<h2>`/`<h3>`;
  headings phrased as the questions a reader would ask where natural.
- [ ] **B5. Original value.** Contains first-hand experience, original analysis,
  specifics (numbers, dates, named entities) — not a rehash of other pages.
- [ ] **B6. Named, credible author.** Visible author with bio/credentials; a
  "last updated" date; sources cited for factual claims. *(E-E-A-T / trust.)*
- [ ] **B7. Complete.** A reader finishes without needing to search again for the
  same task.
- [ ] **B8. Unique, descriptive `<title>`** (primary query near the front) and a
  compelling meta description. Not duplicated across pages.
- [ ] **B9. Descriptive URL slug** (words, hyphens, no junk parameters).
- [ ] **B10. Accurate & current.** No factual errors; no stale claims. For
  YMYL-ish topics (health/safety/money) accuracy is non-negotiable.

## C. Structured Data (נתונים מובנים)

- [ ] **C1. JSON-LD present** (`<script type="application/ld+json">`), using
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
  `FAQPage`/`HowTo` for a SERP rich result (deprecated/restricted). If used, it's
  for semantic context only and reflects real on-page Q&A.

## D. Performance / Core Web Vitals (GATE — ביצועים)

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

## E. Accessibility & Mobile (נגישות ומובייל — also an E-E-A-T topic-fit edge here)

- [ ] **E1. Mobile parity** — same content, links, and meta-robots on mobile and
  desktop *(mobile-first indexing uses the mobile version as source of truth)*.
- [ ] **E2. Responsive, no horizontal scroll**, tap targets adequately sized,
  legible base font.
- [ ] **E3. HTTPS** with a valid certificate across the whole page (no mixed
  content).
- [ ] **E4. Semantic HTML & landmarks** — real `<h1>`/headings, `<nav>`,
  `<main>`, lists; proper reading order.
- [ ] **E5. Images have meaningful `alt`** text (decorative images `alt=""`).
- [ ] **E6. Keyboard operable** — all interactive elements reachable/usable by
  keyboard, visible focus states.
- [ ] **E7. Sufficient color contrast** (WCAG AA: 4.5:1 body text).
- [ ] **E8. Accessible names / ARIA** where needed; forms have labels.
- [ ] **E9. `lang` attribute set** (`<html lang="…">`), correct for the content
  language.
- [ ] **E10. Screen-reader spot check** passes (the owner can do this directly —
  a genuine authenticity signal for an accessibility site).

## F. AEO-readiness (סיכוי להיות מצוטט ע״י מנועי AI — probabilistic, NOT guaranteed)

*No item here guarantees a citation. They raise the odds. A hard requirement for
Google's AI features is simply: the page passes A–E and is eligible to show with
a snippet.*

- [ ] **F1. Retrievable** — passes all of Section A (an AI cannot cite what it
  can't retrieve/index). *(For Google AI Overviews/AI Mode this is the whole
  official requirement.)*
- [ ] **F2. Extractable answer chunks** — self-contained answers under
  question-shaped headings (ties to B3/B4); short paragraphs, lists, tables for
  facts/steps.
- [ ] **F3. One clear claim per passage**, with concrete specifics (facts,
  numbers, dates, named entities) that a model can ground a citation on.
- [ ] **F4. Question-phrased content** matching how people actually ask (natural
  long-tail phrasing appears in visible text).
- [ ] **F5. Trust signals present** — named expert author, credentials, primary
  sources cited, clear "last updated" (ties to B6).
- [ ] **F6. External corroboration exists or is being built** — the page's key
  facts are consistent with, and ideally referenced by, other reputable sources.
  *(Weakest for a brand-new site; expect AI citation to lag the Google ranking.)*
- [ ] **F7. Not relying on unproven levers** — `llms.txt`, FAQ/HowTo schema, or
  any "guaranteed citation" trick is **not** the plan (harmless to have, but not
  counted on).

---

### Proof artifacts to capture (for the "entry ticket")

- [ ] **P1. First-page ranking** — Search Console → Performance, filtered to the
  exact target query, showing **average position ≤ ~10**. Screenshot with date.
- [ ] **P2. AI citation** — a screenshot of ChatGPT / Perplexity / Google AI
  Overview answer that links to the page. *(May take longer; not guaranteed.)*
- [ ] **P3. Technical health** — Rich Results Test = valid; PageSpeed/GSC CWV =
  all green (mobile + desktop); GSC = indexed, zero manual actions.

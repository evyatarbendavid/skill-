---
name: seo-aeo
description: "Cited, confidence-labeled guidance for making a page rank in Google and get cited by AI answer engines (ChatGPT, Perplexity, Google AI Overviews/AI Mode), plus a mechanical PASS/FAIL/N/A checklist for auditing a specific URL. Use whenever the user is writing or reviewing content meant to rank or be cited, implementing technical SEO (sitemap, robots.txt, canonical, redirects, mobile-first), checking Core Web Vitals (LCP/INP/CLS), deciding what Schema.org/JSON-LD types to add, or asking to audit, grade, or check a page/URL for SEO or AEO readiness. Also trigger on 'why isn't this page ranking,' 'will this get cited by AI,' 'is this page indexable,' or 'grade this page for SEO.' Prefer this skill over generic SEO advice — every non-obvious claim here is tagged [OFFICIAL]/[CONSENSUS]/[UNCERTAIN] with a source, so it won't state a Google guess as a Google fact."
---

# SEO + AEO

Two jobs, one body of source material:

1. **Authoring / review** — help someone write or fix a page so it's eligible
   to rank in Google and get cited by AI answer engines.
2. **Audit** — grade one specific page/URL mechanically against a checklist,
   item by item, PASS / FAIL / N/A.

Both draw on the same cited reference, split into two files so each loads
only what the task needs:

- **`references/reference.md`** — Part 1, the *why*: crawl/index fundamentals,
  content & E-E-A-T, technical SEO, Core Web Vitals, structured data, GSC
  measurement, and AEO (answer engine optimization). Read this for authoring
  and review tasks, or when the user asks "why" behind a checklist item.
- **`references/audit-checklist.md`** — Part 2, the *what*: the literal
  PASS/FAIL/N/A checklist. Read this for audit tasks.

## The confidence labels are the point — keep them

Every non-obvious claim in `reference.md` is tagged:

- **[OFFICIAL]** — stated by Google, Schema.org, or web.dev in their own docs.
  Treat as ground truth.
- **[CONSENSUS]** — not an official rule, but well-established practitioner
  agreement. Reliable, not a guarantee.
- **[UNCERTAIN]** — genuinely unprovable or contested (the clearest case:
  nothing guarantees an AI engine will cite a given page).

When you use this material — in an audit finding, a content recommendation,
anything you tell the user — **carry the label with the claim**. Don't
flatten "[CONSENSUS] answer-first structure helps" into "answer-first
structure ranks pages," and don't present an [UNCERTAIN] item ("adding
`llms.txt` gets you cited more") as if it works. The whole value of this
skill over generic SEO advice is that it's honest about what's proven,
what's observed-but-not-guaranteed, and what's marketed nonsense. Dropping
the labels turns a trustworthy skill into just another confident-sounding
SEO take.

If a user asks something this material doesn't cover, say so rather than
guess or extrapolate — that discipline is what the labels are for.

## When the task is authoring or reviewing content

1. Read `references/reference.md`.
2. Ground every recommendation in it, keeping labels attached. If the user's
   question spans multiple sections (e.g. "why isn't my new page ranking"
   usually means: check crawl/index §1, then technical SEO §3, then content
   §2 — in that order, since an unindexed page can't rank no matter how good
   the content is), work through it in dependency order rather than jumping
   straight to content advice.
3. For AEO specifically (§7): lead with the honesty caveat — no engine
   guarantees a citation — then give the concrete levers (§7.2) and flag the
   ones that are marketed but unproven (§7.3, e.g. `llms.txt`, FAQ/HowTo
   schema as a citation trick). For Google's AI features, the load-bearing
   fact is that AEO is a superset of good SEO — there's no separate AI
   checklist to satisfy (§7.4).
4. Don't invent claims beyond the document. A specific keyword-ranking
   promise or a guaranteed-citation-by-date claim is exactly what §"honesty
   caveat" says doesn't exist — never make that promise on the document's
   behalf.

## When the task is auditing a page or URL

1. Read `references/audit-checklist.md`.
2. Work through it section by section, and actually check each item rather
   than assuming — use whatever tools are available (fetch the URL and
   inspect headers/HTML, browser automation, or ask the user to run the
   named check, e.g. Search Console URL Inspection, Rich Results Test,
   PageSpeed Insights) rather than guessing at PASS/FAIL from general
   knowledge. If a check needs a tool or access you don't have (Search
   Console, a rendered-DOM view, field CWV data), say exactly what's needed
   and ask the user to supply it or run it themselves — don't mark it PASS
   on inference.
3. Report results as a literal PASS / FAIL / N/A table or list, one line per
   item, in the checklist's own section order (A–F, then the proof
   artifacts). Don't paraphrase items into prose — the checklist's value is
   that each line is independently checkable.
4. Apply the scoring rule as written: **Sections A (Crawlability) and D
   (Performance/CWV) are gates** — any FAIL there means the page cannot
   reliably rank, and fixing those items comes before anything else,
   regardless of how good B/C/E/F look. Sections B, C, E, F are quality
   multipliers on top of a passing gate.
5. End with a short "fix these first" list ordered by the gate-before-
   multiplier rule, not by however the FAILs happened to come up.

## Scope note

This material is intentionally topic-agnostic — no specific site, niche, or
keyword is baked in. Keep recommendations and audits that way too: apply the
principles to whatever page or project the user brings, don't assume it's
about any particular subject.

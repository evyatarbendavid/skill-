---
name: seo-aeo
description: >
  Audit and fix a website's SEO (Google ranking) and AEO (getting cited by AI
  answer engines like ChatGPT, Perplexity, and Google AI Overviews/AI Mode) by
  running real diagnostics against a live URL — HTTP status and redirect chains,
  robots.txt, canonical tags, sitemap.xml, JSON-LD structured data, broken
  internal links, duplicate titles/content, accessibility basics, and Core Web
  Vitals field data — and, when pointed at the site's local source tree, writing
  real fixes (sitemap.xml, canonical tags, JSON-LD blocks). Use whenever the user
  wants to audit, improve, or troubleshoot a site's search ranking or its
  visibility in AI answers; mentions SEO, AEO, GEO, Core Web Vitals, LCP/INP/CLS,
  schema markup, structured data, sitemaps, canonical URLs, crawling or indexing;
  is building a website and wants it to rank well; or asks why a page is not
  ranking, not indexed, or not being cited by AI.
compatibility: Requires network access and Python 3.8+. Standard library only — no pip install needed. Optional PAGESPEED_API_KEY env var raises the Core Web Vitals lookup quota.
---

# SEO + AEO audit and fix

Real diagnostics and real fixes for search ranking and AI-answer citation. This
skill runs actual checks against a live URL rather than walking a checklist from
memory, and can write the fixes it finds.

## The two modes — keep them separate

| Mode | What it needs | What it does |
|---|---|---|
| **Audit** (default) | just a URL | Read-only. Fetches and analyzes the live site. Writes nothing, ever. |
| **Fix** (`--fix`) | URL **and** `--local-dir` | Writes fixes into the site's **source files**. Dry-run by default; `--apply` actually writes. |

Fixing is a file write, so it needs the site's local source tree — a live URL is
not enough. If the user asks for fixes and you do not know where the source
lives, **ask them for the path** before running. Never write into `node_modules`,
`dist/`, `build/`, `.next/`, or other build output; target the source templates.

## Run the audit

```bash
python3 scripts/audit.py <url> [options]
```

Paths here are relative to this skill's own directory. Run the script by its
full path from wherever you are — the skill may be installed in this project
(`.claude/skills/seo-aeo/`), in your home directory (`~/.claude/skills/seo-aeo/`),
or anywhere else, so do not assume a working directory.

Common options (full list via `--help`):

| Flag | Meaning |
|---|---|
| `--local-dir PATH` | Site source root. Required for `--fix`. |
| `--fix` | Plan fixes for auto-fixable failures. Dry-run unless `--apply`. |
| `--apply` | Actually write the planned fixes to disk. |
| `--json` | Machine-readable report instead of the console table. |
| `--max-pages N` / `--max-depth N` | Crawl bounds (defaults 25 / 2). |
| `--skip-cwv` | Skip the PageSpeed Insights call. |
| `--pagespeed-key KEY` | Or set `PAGESPEED_API_KEY`. |

Exit code is `1` if a **GATE** section (A Crawlability, D Performance) has any
FAIL, else `0`.

## Workflow

1. **Run the audit.** Start with plain audit mode on the URL the user gave you.
2. **Read the report against the checklist.** Every finding carries a checklist
   ID (`A1`, `C3`, `G7`…). `references/audit-checklist.md` explains what each
   item means and how to verify it by hand. **Sections A and D are gates** — a
   FAIL there means the page cannot reliably rank at all, so surface those first
   and loudest; everything else is a quality multiplier.
   The report opens with a **severity-ranked punch list** (critical → low);
   lead with that rather than reciting all findings in order.
3. **Verify anything date-sensitive before you assert it** (see below).
4. **Fix what is safely fixable.** Re-run with `--fix --local-dir <path>` to see
   the planned diffs, show them to the user, then `--apply`. Respect whatever
   autonomy level the user has set — if unclear, show the diff and confirm.
5. **Report — do not guess — what needs human judgment.** The report marks these
   `HUMAN_JUDGMENT` with a reason. Typical cases: which URL should be canonical
   when several are plausible, author identity and credentials for E-E-A-T,
   rewriting content into answer-first structure, what a broken link *should*
   point to.
6. **For AEO questions**, read the AEO section of `references/seo-aeo-reference.md`,
   and re-verify the "AI answers are now the default surface" framing live — it is
   the most volatile fact in this whole skill.

## Live verification — this is not optional

A file on disk cannot keep itself current. Google changes thresholds, retires
rich-result types, and reshapes its AI surfaces continuously. So:

**Trust the static reference for structurally stable things** — the
crawl → index → serve model, how canonical/robots.txt/sitemaps mechanically
work, JSON-LD syntax, what E-E-A-T means.

**Re-verify these live, every time, before stating them as current:**
- Core Web Vitals metrics and their numeric thresholds
- Which structured-data types still produce rich results
- How Google AI Overviews / AI Mode currently select and cite sources
- Anything about `llms.txt` or other proposed AI-crawler conventions
- The current core-update situation

Use WebSearch/WebFetch against `developers.google.com/search`, `web.dev`,
`schema.org`, and recent (last ~90 days) reporting.
`references/live-verification-map.md` has the full stable-vs-volatile table and
ready-made search queries. **Say in your output which facts you verified live
and which came from the static reference** — that distinction is the honest part.

The reference file carries a `Last verified` date. If it is more than ~90 days
old, treat every volatile claim in it as unconfirmed until you re-check.

## Fix-safety rules

- Never overwrite unrelated content in a file.
- Always show the diff before `--apply`.
- Never invent values. A JSON-LD fix leaves `TODO` placeholders for anything
  only a human knows (author name, credentials, publish dates) and reports them
  separately rather than fabricating them.
- Never guess a canonical URL when more than one candidate is plausible, and
  never silently overwrite an existing canonical tag that points somewhere else —
  that is a `HUMAN_JUDGMENT` case.
- Broken links are **reported, not fixed** — where a link should point is a
  content decision.
- Only mark up content that is actually visible on the page. Fabricated
  structured data is a Google spam-policy violation.
- Confirm before any multi-file bulk change (find/replace across templates,
  URL restructuring). After fixing, re-run the audit on the specific items —
  do not assume the fix worked.

## References

Load these on demand — do not read them all up front.

| File | Read it when |
|---|---|
| `references/audit-checklist.md` | Running or explaining a formal audit (items A1–F7, P1–P3) |
| `references/seo-aeo-reference.md` | Explaining *why* something matters; any SEO/AEO question beyond the checklist |
| `references/live-verification-map.md` | Before stating any dated or volatile fact |
| `references/structured-data-schemas.md` | Deciding what a JSON-LD fix should contain |

`assets/jsonld-templates/` holds the boilerplate the fixer injects.

`assets/CLAUDE-seo-aeo-standard.md` is a drop-in project standard. When someone
is building a site and wants these rules enforced on **every** page they touch —
not only when they remember to ask for an audit — offer to copy it into their
project root as `CLAUDE.md` (or append it as a section if one already exists).
The skill is the tool you reach for; that file is the standard that applies
without being asked.

## Honesty requirements

Two things this skill must never claim:

1. **Google does not guarantee crawling, indexing, or ranking**, even for a
   page that follows every guideline. Anyone promising a specific position by a
   date is selling certainty that does not exist.
2. **No technique forces an AI engine to cite you.** AI retrieval is
   non-deterministic and proprietary. Everything in the AEO section raises
   probability; nothing sets it to 1.

What this skill genuinely does is remove every *technical* reason to be excluded
and maximize the odds. Say it that way.

If a user asks something these references do not cover, say so and verify it
live rather than guessing. That discipline is the whole point of the
`[OFFICIAL]` / `[CONSENSUS]` / `[UNCERTAIN]` labels in the reference.

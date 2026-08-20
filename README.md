# seo-aeo-audit

A Claude Code plugin that audits and fixes a website's **SEO** (classic
Google/Bing ranking) and **AEO/GEO** (visibility and citation in AI answer
engines — Google AI Overviews, ChatGPT, Perplexity, Copilot, Gemini,
Claude). Works on an existing site (audit + fix) or a brand-new one being
built (build spec, checked as you go).

It doesn't just hand you a checklist — it dispatches subagents to actually
review every page and, once you confirm findings, implement the fixes in
code directly.

## Install

```
/plugin marketplace add evyatarbendavid/skill-
/plugin install seo-aeo-audit@evyatar-tools
```

That's it. After this the skill is available in every session, on this
machine, in any project. No per-project setup, no copying files.

If the install summary says `Run /reload-plugins to activate.`, run that.
To pull in later updates:

```
/plugin update seo-aeo-audit
```

> The trailing hyphen in `evyatarbendavid/skill-` is part of the repository
> name, not a typo.

## Usage

**Audit a live site** (report only — no code access, so it can diagnose but
not fix):
```
/seo-aeo-audit https://example.com
```

**Audit and fix a local project** (the full loop: find, fix, verify) — run
from inside the project directory:
```
/seo-aeo-audit
```
or point at it explicitly:
```
/seo-aeo-audit /path/to/project
```

**Build a new page correctly from the start**, when there's nothing to
audit yet:
```
/seo-aeo-audit build me a landing page for [whatever you're building]
```
The same checklist runs as a build spec instead of a retroactive audit —
each page is checked against it while it's being written.

You don't have to use the slash command. The skill is written to trigger on
its own when you paste a URL or a project path and ask to check, audit,
improve, or "make sure it's ready."

## What each file does

| File | Role |
|---|---|
| **`skills/seo-aeo-audit/SKILL.md`** | The orchestrator. Figures out what you gave it (a URL, a local project, or "build me a new page"), enumerates pages, and dispatches the other two in the right order. It doesn't check anything itself. |
| **`agents/seo-page-auditor.md`** | The inspector. Reviews one page at a time against the full checklist. **Read-only** — it reports, it never touches code. One copy runs per page, in parallel. |
| **`agents/seo-fixer.md`** | The implementer. Takes a confirmed findings list and makes the actual code changes, then re-reads the file to confirm the fix worked. Has edit access; the inspector doesn't. |

Three files rather than one because Claude Code subagents each get their
own permissions. The inspector is deliberately read-only so it can't change
your code while reviewing it; only the fixer can edit, and only after
you've seen what it's about to change.

## What it actually checks

Full detail lives in `agents/seo-page-auditor.md`. Briefly:

- **Technical SEO** — crawlability, indexing, canonical tags, hreflang,
  pagination, faceted-navigation crawl traps, sitemap/robots.txt, redirects
- **Performance** — real Core Web Vitals via the PageSpeed Insights API
  (measured, not guessed from code), TTFB, third-party script bloat
- **Structured data** — schema.org/JSON-LD correctness, including
  AEO-relevant `Speakable` markup
- **Security and trust** — HSTS, CSP, exposed config files
- **Mobile and accessibility** — tap targets, contrast, keyboard nav, ARIA
- **AEO/GEO** — answer-block structure, E-E-A-T, freshness, and
  per-platform notes for each major answer engine
- **Hebrew/RTL** — `lang`/`dir` correctness, bidi bugs, Israeli local
  search signals
- **Content quality** — duplicate content at scale, broken and orphan
  links, navigation consistency, leaked placeholder text

## Two things it will never claim

**Google does not guarantee crawling, indexing, or ranking** — that's
Google's own wording, and it holds even for a page that follows every
guideline. **No technique forces an AI engine to cite you** either; AI
retrieval is non-deterministic and proprietary.

What this plugin does is remove every technical reason to be excluded and
maximize the odds. Anyone promising a specific position by a date is
selling certainty that doesn't exist.

## Staying current

Search-engine and AI-answer-engine behavior shifts every few months, so the
checklist carries its own expiry warning: the auditor is instructed to
verify current Core Web Vitals thresholds and AEO practices against primary
sources before a real pre-launch audit, rather than trusting the numbers in
the file. If it finds something outdated, tell it to update the relevant
file in place.

---

## Also in this repo

`tools-seo-audit-cli/` is a standalone Python audit tool (standard library
only, no install) that measures the mechanically-checkable subset —
status codes, redirect chains, robots.txt, canonical, sitemap membership,
JSON-LD property validation, broken links, duplicate titles and content,
RTL correctness, Core Web Vitals. It predates the plugin and isn't required
by it, but it's useful when you want deterministic numbers rather than an
agent's read, or a CI gate:

```bash
python3 tools-seo-audit-cli/scripts/audit.py https://example.com/
./tests/run_tests.sh   # 106 tests, no network needed
```

Exit code is `1` when a gate section fails, so it drops into CI as-is.

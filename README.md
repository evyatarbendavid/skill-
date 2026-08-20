# seo-aeo

A Claude skill that applies Google's actual ranking rules and AI
answer-engine citation principles to any website work — building a page,
reviewing one, or fixing one that isn't performing.

It loads itself whenever you touch a site, even if you never say the word
"SEO."

## Install

### Claude Desktop / claude.ai

Download **[`seo-aeo.zip`](seo-aeo.zip)** from this repo, then:

**Settings → Capabilities → Skills → Upload skill** → pick the zip.

That's it. No terminal, no setup.

### Claude Code

```
/plugin marketplace add evyatarbendavid/skill-
/plugin install seo-aeo@evyatar-tools
```

Installed once, available in every project on that machine.
`/plugin update seo-aeo` pulls later changes.

> The trailing hyphen in `skill-` is part of the repository name.

Claude Code also gets two subagents the Desktop version doesn't:
`seo-page-auditor` (read-only, one page at a time, in parallel) and
`seo-fixer` (the only one with edit access). The skill works either way —
it just does full-site passes faster where subagents exist.

## What it knows

**The gates.** Five things a page cannot rank without: HTTP 200, not
blocked in robots.txt, no `noindex`, content actually present in the served
HTML, and Core Web Vitals passing. Everything else is a multiplier on a
page that already clears these.

**Core Web Vitals** — LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1, at the 75th
percentile of real users, all three, mobile and desktop separately. Plus
what actually causes each one to fail, and how to measure a live URL
through the free PageSpeed Insights API instead of guessing from code.

**Crawlability** — canonical tags, sitemaps, redirect chains, hreflang
reciprocity, and the faceted-navigation URL explosion that quietly eats
crawl budget on any site with filters.

**Structured data** — what to implement, and what's dead. `FAQPage` rich
results were removed entirely in May 2026 and `HowTo` in 2023; seven more
types went in June 2025. The skill knows not to recommend them, and knows
the most common self-inflicted bug is marking up content that isn't
visible on the page.

**AEO** — why the unit that gets cited is a *passage*, not a page, and how
to write one: a direct self-contained answer in 40–60 words before the
background, under a question-shaped heading. Plus E-E-A-T, freshness, and
why `llms.txt` is not the lever it's sold as.

**Hebrew and RTL** — `lang`/`dir` correctness, and the bidi bugs where
English words or numbers inside Hebrew text render in the wrong visual
order. Also the opportunity: AI engines have far thinner Hebrew data, so a
well-structured Hebrew page competes against a much weaker field.

**Quality bugs** — duplicate content at scale, `Lorem ipsum` and `TODO`
shipped to production, broken and orphan links, inconsistent navigation,
buttons that don't go where their label promises.

## Two things it will never tell you

**Google does not guarantee crawling, indexing, or ranking.** That's
Google's own wording, and it holds for a page that follows every rule here.

**Nothing forces an AI engine to cite you.** Retrieval is
non-deterministic and proprietary.

What the skill does is remove every technical reason to be excluded and
maximize the odds. Anyone promising a specific position by a date is
selling certainty that doesn't exist — and this skill is built to say so
rather than play along.

## Staying honest as things change

Search behavior shifts every few months, so the skill separates what's
stable from what isn't. The crawl model and how canonical tags work don't
move; Core Web Vitals thresholds, which schema types still produce rich
results, and how AI Overviews select sources do. For anything in the second
group the skill verifies against `developers.google.com/search` and
`web.dev` before stating it, and tells you which facts it checked live.

It also carries a list of **false claims currently circulating** — that
Google cut LCP to 2.0s, tightened CLS to 0.08, added an "FCP" vital, or set
a January 2026 deadline — so a search result echoing them doesn't get
mistaken for confirmation.

The baseline was verified 2026-08-18. Past roughly 90 days, the skill
treats its own volatile claims as unconfirmed until re-checked.

## Repo layout

```
plugins/seo-aeo/
  skills/seo-aeo/          the skill itself — one copy, the source of truth
    SKILL.md
    references/
      audit-checklist.md   every item as PASS / FAIL / N/A
      sources.md           cited, labelled OFFICIAL / CONSENSUS / UNCERTAIN
  agents/                  Claude Code only: the auditor and the fixer
seo-aeo.zip                built from the skill folder, for Desktop upload
build.sh                   regenerates the zip
tests/                     package integrity + the standalone CLI's tests
```

Run `./build.sh` after editing the skill, or the zip goes stale — there's a
test that fails if you forget.

## Tests

```bash
./tests/run_tests.sh
```

Checks the package stays installable (frontmatter the loader accepts, no
dangling reference links, zip in sync with source, the auditor agent still
read-only) and that the factual corrections don't get edited back out — if
someone removes the FAQPage or the no-guarantees language, a test fails.

## Also here

`tools-seo-audit-cli/` is a standalone Python tool (standard library only)
that measures the mechanically-checkable subset and exits non-zero when a
gate fails, so it drops into CI. Not required by the skill.

```bash
python3 tools-seo-audit-cli/scripts/audit.py https://example.com/
```

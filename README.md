# seo-aeo

A Claude skill that applies Google's actual ranking rules and AI
answer-engine citation principles to any website work — building a page,
reviewing one, or fixing one that isn't performing.

Once installed it loads itself whenever you touch a site, even if you never
say the word "SEO."

## Install

Get the files — green **Code** button → **Download ZIP**, then unzip, or:

```bash
git clone https://github.com/evyatarbendavid/skill-.git
```

**The skill is `SKILL.md` plus the `references/` folder.** Everything else
in this repo is optional: `agents/` helps only in Claude Code, `tests/`
protects the skill's own accuracy, and `tools-seo-audit-cli/` is a separate
command-line tool. Nothing else is needed for the skill to work.

**Claude Desktop / claude.ai** — add it under Settings → Capabilities →
Skills. Point the upload at the folder holding `SKILL.md` (the folder you
just unzipped). If your version asks for a `.zip` rather than a folder,
zip that folder and upload the zip — the skill itself is plain Markdown
either way.

**Claude Code** — copy it where Claude Code looks for skills:

```bash
mkdir -p ~/.claude/skills/seo-aeo
cp -r SKILL.md references ~/.claude/skills/seo-aeo/
cp -r agents/* ~/.claude/agents/          # optional — see below
```

For one project rather than every project, use `.claude/skills/seo-aeo/`
inside that project instead.

**Then just work.** You don't have to invoke it by name. Ask about a page,
paste a URL or a component, or start building one, and it loads itself.

## What's here

| Path | What it is |
|---|---|
| `SKILL.md` | The skill. Everything it knows, in one file. |
| `references/ai-crawlers.md` | Which AI bot does what, and why blocking the wrong one backfires |
| `references/examples.md` | Before/after for the edits people get wrong, and a full worked page report |
| `references/platforms.md` | How each answer engine picks sources, and which one a given site should realistically aim at |
| `references/situations.md` | Depth that only applies if the site is large, e-commerce, multilingual, thin, mid-migration, or chasing entity recognition |
| `references/audit-checklist.md` | Every item as PASS / FAIL / N/A |
| `references/working-in-code.md` | What changes when you have the source: framework route files, where head tags and sitemaps actually live, and the mistakes that ship to production |
| `references/field-notes.md` | What actually turned up broken auditing live sites — with the sample size stated, so it reads as evidence rather than as a rule |
| `references/sources.md` | The cited reasoning, labelled OFFICIAL / CONSENSUS / UNCERTAIN |
| `agents/` | Optional. Two Claude Code subagents — a read-only auditor and a fixer — for full-site passes. Not needed on Desktop. |

The references load on demand, so the skill stays light until it needs the
depth.

## What it knows

**The gates.** Five things a page cannot rank without: HTTP 200, not
blocked in robots.txt, no `noindex`, content actually present in the served
HTML, and Core Web Vitals passing. Everything else is a multiplier on a
page that already clears these.

**Core Web Vitals** — the real thresholds, what actually causes each to
fail, and how to measure a live URL through the free PageSpeed Insights API
instead of guessing from code. Including the part most guidance misses:
single-page apps no longer get a free pass, because Chrome now measures
in-app route changes too.

**Crawlability** — canonical, sitemaps, redirect chains, hreflang
reciprocity, faceted-navigation URL explosion, and the sharp version of the
JavaScript problem: `canonical` and `meta robots` injected client-side may
never be seen before indexing decisions are already made.

**Structured data** — what to implement, and what's dead. `FAQPage` rich
results were removed entirely in May 2026, `HowTo` in 2023, seven more
types in June 2025. It also refuses to claim schema drives AI citation,
because the one controlled study on that found it doesn't.

**AEO** — why the unit that gets cited is a *passage*, not a page, and how
to write one. Plus the correction that matters most: "rank top-10 and
citations follow" no longer holds, and the four major engines agree with
each other on only about 12% of what they cite.

**AI crawlers** — the three different bots each vendor runs, and why
blocking `GPTBot` doesn't remove you from ChatGPT's answers while blocking
`OAI-SearchBot` does.

**Hebrew and RTL** — `lang`/`dir` correctness and the bidi bugs where
English words or numbers inside Hebrew render in the wrong visual order.
Also the opportunity: AI engines have far thinner Hebrew data, so a
well-structured Hebrew page competes against a much weaker field.

**Quality bugs** — duplicate content at scale, `Lorem ipsum` shipped to
production, orphan pages nothing links to, buttons that don't go where
their label promises.

## Two things it will never tell you

**Google does not guarantee crawling, indexing, or ranking.** That's
Google's own wording, and it holds for a page following every rule here.

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
group it verifies against `developers.google.com/search` and `web.dev`
before stating it, and tells you which facts it checked live.

It also carries a list of **false claims currently circulating** — the
invented Core Web Vitals numbers, "Google penalizes AI-written content,"
"you need an llms.txt to appear in ChatGPT," third-party Domain Authority
as a Google ranking factor — so a search result echoing them doesn't get
mistaken for confirmation.

Baseline verified 2026-08-21. Past roughly 90 days, the skill treats its
own volatile claims as unconfirmed until re-checked.

## Tests

```bash
./tests/run_tests.sh
```

Checks the skill stays loadable (frontmatter parses as YAML, no dangling
reference links, the auditor agent still read-only) and that the factual
corrections don't get edited back out — remove the FAQPage line or the
no-guarantees language and a test fails.

`tests/evals.json` is a different kind of check: sixteen prompts covering
what the skill should do, including three it should **not** trigger on.
Those need a real model rather than an assertion, so run them by installing
the skill and asking:

```bash
mkdir -p ~/.claude/skills/seo-aeo
cp -r SKILL.md references ~/.claude/skills/seo-aeo/
printf 'Summarise the plot of Hamlet.' | claude -p     # must NOT trigger
printf 'Check my site for broken links.' | claude -p   # must trigger
```

The negative cases matter most. A description broad enough to catch every
real case is usually broad enough to fire on unrelated ones, and a skill
that loads when it shouldn't is worse than one that occasionally doesn't.

## Also here

`tools-seo-audit-cli/` is a standalone Python tool (standard library only)
that measures the mechanically-checkable subset and exits non-zero when a
gate fails, so it drops into CI. Not required by the skill.

```bash
python3 tools-seo-audit-cli/scripts/audit.py https://example.com/
```

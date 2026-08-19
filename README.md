# seo-aeo

A Claude Code skill that audits and fixes a website's **SEO** (Google ranking)
and **AEO** (getting cited by AI answer engines — Google AI Overviews/AI Mode,
ChatGPT, Perplexity).

It runs real diagnostics against a live URL rather than reciting a checklist
from memory, and — pointed at the site's source tree — writes the fixes that are
safely unambiguous.

## Install

Per project:

```bash
cp -r .claude/skills/seo-aeo /path/to/project/.claude/skills/
```

For every project on the machine:

```bash
cp -r .claude/skills/seo-aeo ~/.claude/skills/
```

No dependencies. Standard library Python 3.8+.

## Use

Ask Claude in plain language — "audit example.com for SEO", "why isn't my site
showing up in Google", "make this page rank" — or run the tool directly:

```bash
# Read-only audit of any live URL
python3 .claude/skills/seo-aeo/scripts/audit.py https://example.com/

# Plan fixes (dry run — writes nothing)
python3 .claude/skills/seo-aeo/scripts/audit.py https://example.com/ \
    --local-dir ./site --fix --diffs

# Apply them
python3 .claude/skills/seo-aeo/scripts/audit.py https://example.com/ \
    --local-dir ./site --fix --apply
```

Exit code is `1` when a gate section (A crawlability, D performance) fails,
so it drops into CI as-is.

Set `PAGESPEED_API_KEY` for a higher Core Web Vitals quota; without one the
keyless PageSpeed endpoint is rate-limited and those checks report `N/A`.

## What it checks

Findings map to a checklist (`references/audit-checklist.md`) and open with a
severity-ranked punch list.

| Section | Covers |
|---|---|
| **A** *(gate)* | HTTP status, redirect chains, robots.txt, noindex, canonical, sitemap membership, internal linking, content in the served HTML |
| **B** | Heading hierarchy, title/description uniqueness, URL slugs, duplicate content |
| **C** | JSON-LD presence and required properties; flags rich-result types Google has retired |
| **D** *(gate)* | LCP / INP / CLS from real-user field data, mobile and desktop |
| **E** | Viewport, HTTPS and mixed content, landmarks, alt text, `lang` |
| **F** | AEO readiness: retrievability, extractable answer chunks, question-shaped headings, trust signals |
| **G** | Placeholder text in production, title/description length, redirect chains, vague anchors, image attributes affecting CLS/LCP, RTL and bidi correctness, orphan pages |

## What it will not do

- **Guess.** An existing canonical pointing elsewhere, an unmappable URL, or a
  broken link's intended target are reported as `HUMAN_JUDGMENT`, not resolved.
- **Invent values.** JSON-LD fixes fill only fields the audit actually knows;
  author names and dates stay `TODO` and are reported. Wrong structured data is
  worse than absent structured data.
- **Overwrite.** Existing canonical tags and JSON-LD blocks are never clobbered.
- **Promise rankings.** Google does not guarantee crawling, indexing, or
  ranking, and nothing forces an AI engine to cite you. The skill removes
  technical reasons to be excluded; it does not sell certainty.

## Staying current

Google changes thresholds, retires rich-result types, and reshapes its AI
surfaces continuously — so a static file goes stale. `SKILL.md` requires
re-verifying volatile facts against primary sources before asserting them, and
`references/live-verification-map.md` lists exactly which facts those are and
how to check them.

## Project standard

`assets/CLAUDE-seo-aeo-standard.md` is a drop-in `CLAUDE.md` that holds every
page in a project to these rules without anyone having to ask:

```bash
cp .claude/skills/seo-aeo/assets/CLAUDE-seo-aeo-standard.md /path/to/site/CLAUDE.md
```

## Tests

```bash
./tests/run_tests.sh
```

106 tests, no network required. `test_seo_aeo.py` covers the modules;
`test_site_archetypes.py` runs the real CLI against six site shapes — a clean
static blog, a client-rendered SPA, a Hebrew RTL site, a broken legacy page, an
e-commerce catalogue with duplicate URLs, and a single-page landing site — to
check the audit holds up on shapes it was not written against.

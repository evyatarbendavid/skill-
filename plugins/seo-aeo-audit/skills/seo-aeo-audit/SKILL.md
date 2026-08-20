---
name: seo-aeo-audit
description: Runs a full multi-agent SEO + AEO/GEO (Answer/Generative Engine Optimization) audit-and-repair pass across an entire website — every page, every navigation transition, every button/CTA. Invoke directly with /seo-aeo-audit followed by a URL or a local path, or let it auto-trigger whenever the user pastes a site URL, a local project path, or a repo and asks to check, audit, improve, fix, or "make sure it's ready" for SEO, AI search visibility, bugs, broken links, duplicate content, or launch readiness. Dispatches a seo-page-auditor subagent per page for deep repeated review, then a seo-fixer subagent to implement fixes directly in code, then re-verifies.
---

# Full-Site SEO & AEO Audit + Auto-Fix

## What "done" looks like

The user gives you *anything* that identifies a site — a live URL, a
local build/source directory, a repo, or just "check my site" while
sitting in the project. You:

1. Enumerate **every page/route**.
2. Dispatch the `seo-page-auditor` subagent to deeply review each page —
   technical SEO, AEO/GEO, RTL if relevant, duplicate content, broken
   links, and every navigation transition and interactive element.
3. Aggregate findings into one prioritized report.
4. **Fix what can be fixed in code, directly — not just report it**, via
   the `seo-fixer` subagent.
5. Re-verify, and repeat the audit→fix loop until clean or the pass
   budget is used up.

This is the difference between handing someone a checklist and actually
running an autonomous QA pass. Don't stop at step 3.

## Step 1 — Resolve the target and mode

- A live URL → crawl mode, audit an existing site.
- A local path, "this project," or nothing (already inside a project) →
  local mode, scoped to the current repo, audit existing pages.
- A pasted block of code → ask which page/route it belongs to, or treat
  it as a single-file review if there's no routing context.
- **Starting a brand-new project or page** ("build me a landing page,"
  "scaffold a new site," anything where there's little/no existing code
  yet) → **build mode**: skip the crawl/enumerate steps below entirely.
  Instead, as pages get written, hand each one to `seo-page-auditor` in
  its "build-spec" mode (see that agent's own instructions) so SEO/AEO
  correctness is designed in from the first draft instead of retrofitted
  later. `seo-fixer` isn't needed in this mode — you're writing the page
  right the first time, not patching an existing one.

Ask one clarifying question only if genuinely ambiguous. Otherwise
proceed — don't stall on detail you can infer.

## Step 2 — Enumerate pages

- Local: find route files (Next.js `app/`/`pages/`, etc.) or built
  `.html` files.
- Live: read `sitemap.xml` if present, else crawl same-domain links from
  the homepage.
- **Large site (100+ pages)**: don't deep-audit every single page —
  cluster by template/type (e.g. all "exercise detail" pages share one
  template), deep-audit a representative sample per cluster, then apply
  confirmed fixes to the whole cluster via its shared source. State the
  sampling strategy explicitly in the report — don't sample silently.

## Step 3 — Deep per-page pass: dispatch `seo-page-auditor`

For each page (or cluster representative from Step 2), dispatch the
`seo-page-auditor` subagent in parallel — batch in groups if the page
count is large (default concurrent-subagent limit is 20). It's
read-only and self-contained: it carries its own full checklist and
reports findings, it never edits.

## Step 4 — Aggregate

Merge every subagent's findings into one severity-ranked, deduplicated
list — Critical / High / Medium / Low — each item naming the affected
page(s) and *why it matters* (ranking / AI-citation / UX).

Show this before fixing anything non-trivial. Skip confirmation only for
unambiguous, low-risk, mechanical fixes (e.g. a missing alt attribute) —
confirm before anything touching many files, URL structure, or content
meaning.

## Step 5 — Fix: dispatch `seo-fixer`

For confirmed findings, dispatch the `seo-fixer` subagent (has
Edit/Write access) with the specific findings for its page(s). Run in
parallel per page/cluster the same way as Step 3.

## Step 6 — Re-verify, loop

Re-run Step 3 on the fixed pages to confirm the findings are actually
gone. If issues remain, repeat Steps 3–6.

**On "run it N times"**: treat a request for many passes as "keep going
until it's actually clean," not a literal instruction to always burn N
full passes regardless of findings. Default: stop when a re-verify pass
finds nothing left to fix, or after 3 fix→reverify cycles, whichever
comes first. Full-site subagent passes are token-expensive — each
subagent is its own context window — so loop until *actually done*, and
say so if you're stopping early because returns have flattened, rather
than silently under-delivering or burning budget for its own sake.

## Step 7 — Final report

One clean summary: what was found, what was fixed automatically, what's
left needing a human/business call (URL restructuring, content strategy,
anything genuinely ambiguous), and the current severity counts.

## Subagents this skill uses

Both ship with this plugin and are available by name — dispatch them with
the Agent tool using these `subagent_type` values:

| Agent | Role | Access |
|---|---|---|
| `seo-page-auditor` | Deep audit of one page — carries its own full SEO/AEO/RTL/bugs checklist | Read-only, never edits |
| `seo-fixer` | Implements confirmed fixes in code | Edit/Write |

The split is deliberate: the auditor physically cannot change code while
reviewing it, and the fixer only runs on findings you've seen.

## Install

This is a Claude Code plugin. Users install it once and it's available in
every project on that machine:

```
/plugin marketplace add evyatarbendavid/skill-
/plugin install seo-aeo-audit@evyatar-tools
```

Nothing to copy, no per-project setup. `/plugin update seo-aeo-audit`
pulls later changes.

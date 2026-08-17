# Third-Party Skills — Attribution

The skills under `.claude/skills/` were vendored from public open-source
repositories, unmodified except where noted. Each keeps its original
license. If you touch these files, please preserve attribution.

| Skill(s) | Source repo | License | Full text |
|---|---|---|---|
| `ui-ux-pro-max`, `banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT (© Next Level Builder) | `LICENSES/ui-ux-pro-max-skill-MIT.txt` |
| `frontend-design`, `algorithmic-art`, `brand-guidelines`, `canvas-design`, `claude-academy-guide`, `claude-api`, `discernment-nudge`, `doc-coauthoring`*, `internal-comms`, `mcp-builder`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills) | Apache 2.0 | `.claude/skills/<name>/LICENSE.txt` (each skill ships its own copy) |
| `watch` | [bradautomates/claude-video](https://github.com/bradautomates/claude-video) | MIT (© Bradley Bonanno) | `LICENSES/claude-video-MIT.txt` |
| `no-ai-slop` | [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | MIT (© Peter Yang) | `LICENSES/no-ai-slop-MIT.txt` |
| `ab-testing`, `ad-creative`, `ads`, `ai-seo`, `analytics`, `aso`, `attribution`, `churn-prevention`, `co-marketing`, `cold-email`, `community-marketing`, `competitor-profiling`, `competitors`, `content-strategy`, `copy-editing`, `copywriting`, `cro`, `customer-research`, `directory-submissions`, `emails`, `free-tools`, `image`, `influencer-marketing`, `launch`, `lead-magnets`, `marketing-council`, `marketing-ideas`, `marketing-loops`, `marketing-plan`, `marketing-psychology`, `offers`, `onboarding`, `paywalls`, `popups`, `pricing`, `product-marketing`, `programmatic-seo`, `prospecting`, `public-relations`, `referrals`, `revops`, `sales-enablement`, `schema`, `seo-audit`, `signup`, `site-architecture`, `sms`, `social`, `video` (49 skills) | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | MIT (© Corey Haines) | `LICENSES/marketingskills-MIT.txt` |
| 274 skills from `.claude/skills/` — general engineering, agent-ops, growth, and domain skills. Full list with descriptions: `docs/ecc-skills-index.md` | [affaan-m/ecc](https://github.com/affaan-m/ecc) ("Everything Claude Code") | MIT (© Affaan Mustafa) | `LICENSES/ecc-MIT.txt` |

`.claude/skills/ui-styling/LICENSE.txt` also ships inside that skill folder as part of the original upstream package.

\* `doc-coauthoring` ships without its own `LICENSE.txt` in the upstream
repo (every sibling skill has one). The repo's `.claude-plugin/marketplace.json`
groups it under the same `example-skills` plugin as `algorithmic-art`,
`canvas-design`, `frontend-design`, etc. — all Apache 2.0 — so this is very
likely a missing file upstream rather than an intentional restriction.
Treated as Apache 2.0 by that grouping; flagging here rather than silently
assuming, in case it should be pulled if this gets clarified otherwise.

## From `anthropics/skills`, NOT vendored on purpose

- **`docx`, `pdf`, `pptx`, `xlsx`** — the repo's own README says these are
  "source-available, not open source": each ships a proprietary
  "© Anthropic, PBC. All rights reserved" license, not Apache 2.0. Also
  redundant here — they're already available in every session automatically
  via account-level skill sync (`~/.claude/skills/synced/`), not something
  this repo needs to carry.
- **`skill-creator`** — Apache 2.0, no license blocker, but same
  redundancy: already synced at the account level
  (`~/.claude/skills/synced/skill-creator`) in every session regardless of
  which repo is open. Skipped to avoid a stale duplicate; if the
  account-level copy ever falls out of sync, say so and it can be vendored
  properly.

## `ecc` — vendored partially, on purpose

`affaan-m/ecc` is not a skills pack — it's a full agent-harness framework
(285 skills, 68 agents, its own memory system, a security scanner
"AgentShield") that ships **runtime hooks**: `hooks/hooks.json` (at the repo
root, not copied here) registers `PreToolUse` handlers on `Bash`, `Write`,
`Edit`, `MultiEdit`, and a wildcard `*` matcher, running third-party Node
scripts on every tool call. Its own README says to install via
`/plugin marketplace add` + `/plugin install ecc@ecc` and explicitly "do not
also run a full manual install."

Owner decision (2026-08-17): vendor the **skills only** — no hooks, no
agents subsystem, no top-level framework. Concretely, from the 285 skills in
`skills/`, **11 were excluded**:

- `design-system` — name collision with the existing `nextlevelbuilder`
  skill already in this repo; kept the original, skipped ecc's version.
- `ck`, `continuous-learning`, `continuous-learning-v2`, `delivery-gate`,
  `gateguard`, `safety-guard`, `strategic-compact` — each is itself a
  hook-based runtime system (session observers, PreToolUse gates, a
  suggest-compact hook) with instructions to wire into `settings.json`, or
  ships its own hook script inside the skill folder
  (`delivery-gate/hooks/quality-gate.py`,
  `continuous-learning-v2/hooks/observe.sh` + `agents/*.sh`). This is
  exactly the runtime-behavior layer the owner chose to skip.
- `plankton-code-quality`, `inherit-legacy-style` — both are primarily
  guides to installing a PostToolUse/PreToolUse enforcement hook from
  outside this vendored set; kept out for the same reason.
- `ecc-guide` — a meta-guide to the *whole* ECC framework (references
  `hooks/hooks.json`, install manifests, and other top-level paths that
  don't exist in this partial vendor); doesn't stand alone without the rest
  of the framework.

The remaining 274 are plain knowledge/workflow skills (`SKILL.md` plus, in
some cases, scripts that only run when the skill itself is explicitly
invoked — e.g. an icon generator, a slide exporter — never on their own).
Verified before vendoring: no `PreToolUse`/`PostToolUse`/`SessionStart`
wiring, no `postinstall` scripts, no other name collisions.

## Not vendored as skills (different mechanism / not skill-shaped)

- **[microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)** —
  an MCP *server*, not a skill. Wired up in `.mcp.json` at the repo root
  instead — gives Claude a real, controllable browser.
- **[shadcn-ui/ui](https://github.com/shadcn-ui/ui)** — a React component
  library, not a Claude skill. Relevant as a project dependency if we ever
  scaffold a frontend, not something to "install" here.
- **[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)** —
  a standalone CLI for reading Twitter/Reddit/YouTube/etc. Could be added
  later as a dev-container tool if we need it.
- **[abi/screenshot-to-code](https://github.com/abi/screenshot-to-code)** —
  a full standalone app (FastAPI + React), not something that plugs into
  Claude directly.

Say the word if any of these four should be turned into a proper skill or
wired in some other way later.

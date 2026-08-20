# AI crawlers and robots.txt

> **Verification status.** The bot names and the three-category split are
> documented by their vendors and stable. The traffic-impact studies and
> compliance statistics below come from industry research that could not be
> read at its primary source — treat the specific numbers as directional,
> and re-verify before quoting a figure to someone making a decision.

## The mistake almost everyone makes

"Should I block AI crawlers?" is not one decision. Each major vendor runs
**three functionally different bots**, and blocking the wrong one produces
the opposite of what people usually intend.

| Vendor | Trains the model | Builds the answer-engine index | Fetches live for one user's question |
|---|---|---|---|
| OpenAI | `GPTBot` | `OAI-SearchBot` | `ChatGPT-User` |
| Anthropic | `ClaudeBot` | `Claude-SearchBot` | `Claude-User` |
| Perplexity | — | `PerplexityBot` | `Perplexity-User` |
| Google | `Google-Extended` *(a control token, not a separate crawler)* | Googlebot itself — AI Overviews and AI Mode run on the normal index | — |
| Apple | `Applebot-Extended` | — | — |

Also worth knowing: `Bytespider` (ByteDance), `Meta-ExternalAgent`,
`Amazonbot`, and `CCBot` — Common Crawl, which feeds many models
indirectly.

**The consequence that catches people out:** blocking `GPTBot` opts you out
of future model *training*. It does **not** remove you from ChatGPT's
answers. That's `OAI-SearchBot`. Sites that wanted to protect their content
from training and accidentally blocked retrieval instead removed themselves
from the answer engine while still appearing in the training set they'd
already been scraped into.

So treat it as two independent decisions:

1. **Training** — an intellectual-property call. Legitimate either way, and
   genuinely the site owner's to make, not yours.
2. **Retrieval** — a visibility call. Blocking these removes you from that
   engine's answers.

For Google there is no separation on the retrieval side: AI Overviews and
AI Mode use the ordinary index. You cannot appear in Google Search while
opting out of Google's AI answers. `Google-Extended` controls Gemini model
training only.

## robots.txt is a request, not a fence

For Googlebot, robots.txt is reliably honored. For AI crawlers it is
**best-effort**, and the gap is measurable:

- Cloudflare de-listed Perplexity's crawler as verified, reporting stealth
  crawling — rotating IPs and altered user-agent strings, including
  impersonating Chrome — found using private honeypot domains that could
  only have been reached by ignoring robots directives. Perplexity disputed
  the finding.
- Cloudflare reported roughly **13% of AI bot requests bypassed robots.txt
  in Q4 2025**, up sharply through that year.
- One study of sites blocking AI crawlers found **most were still cited
  anyway** — blocking often failed at the one thing it was for.

**The rule:** if a site needs enforcement rather than a polite request,
that's server or CDN-level bot management — Cloudflare bot rules, WAF, rate
limiting. Never tell someone robots.txt will keep their content out of AI
systems. It expresses a preference that well-behaved crawlers honor.

## Should a site block them?

Default answer: **no, don't block retrieval bots** — and don't present
blocking as an SEO or AEO tactic, because it is the opposite of one.

Research on publishers who blocked AI crawlers found measurable traffic
loss, attributed mainly to disappearing from AI answers rather than to lost
referral clicks. The magnitude is genuinely uncertain — the same research
team revised its own estimate substantially between versions — so state the
direction, not a number.

Combined with the compliance gap above, blocking tends to land in the worst
position available: a real visibility cost, without reliably achieving the
exclusion it was meant to achieve.

Blocking is a legitimate **business or legal** decision — during licensing
negotiations, or where content genuinely must not be reused. Frame it that
way. It is not a performance optimization, and anyone who presents it as
one has it backwards.

## What to actually check on a site

- Does `robots.txt` block any retrieval bot **unintentionally**? A blanket
  `User-agent: * / Disallow: /` on a staging config that shipped to
  production is the usual culprit.
- Is the block deliberate and documented? If the owner made an IP decision,
  respect it — and note the visibility cost once, without relitigating.
- Are training and retrieval treated as separate decisions, or did one
  blanket rule collapse both?
- If exclusion actually matters to them, is anything enforcing it beyond
  robots.txt?

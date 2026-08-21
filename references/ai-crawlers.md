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
- Cloudflare has reported a meaningful share of AI bot requests ignoring
  robots.txt, rising through 2025. *(An earlier revision of this file put
  that at "roughly 13% in Q4 2025". A re-check could not corroborate that
  specific figure at its source — adjacent Cloudflare statistics exist,
  that one was not found. The direction is well supported; treat the number
  as unverified and do not quote it.)*
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

## The lever this discussion usually misses

`robots.txt` is the wrong tool for keeping content out of **Google's** AI
answers, and it is not the only one available. Google's robots meta
directives apply to AI Overviews and AI Mode as well as to ordinary
results:

| Directive | Effect |
|---|---|
| `nosnippet` | No snippet anywhere — web results, Images, Discover, AI Overviews, AI Mode — and the content is not used as a direct input to AI Overviews or AI Mode |
| `data-nosnippet` | The same, scoped to the HTML element you wrap, leaving the rest of the page usable |
| `max-snippet:[n]` | Caps snippet length across those same surfaces, and limits how much may be used as a direct input |
| `max-snippet:0` | Makes the page ineligible for AI Overviews |

These are honored, unlike a `robots.txt` line addressed to a third-party
crawler, because Google is the party reading them. That makes this the only
reliable exclusion control in the whole discussion — for Google's surfaces.
It does nothing about ChatGPT, Perplexity, or Copilot.

**And it costs the ordinary snippet.** The same directive that pulls a page
out of AI Overviews strips the description under its blue link. The result
becomes a bare title, which is a real click-through loss on a page that was
ranking fine. For most sites that is a worse trade than the citation was.
Where it earns its place — paywalled excerpts, licensed text, a passage
that must not be quoted out of context — `data-nosnippet` around that
passage is usually the right size of tool, not `nosnippet` on the page.

*(Verified 2026-08-21 against Google's robots meta tag documentation as
reported by trade press; the directives themselves are long-standing, their
stated application to AI Overviews and AI Mode is the recent part.)*

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
- If the goal is specifically to stay out of Google's AI answers, are they
  reaching for `robots.txt` when `nosnippet` or `data-nosnippet` is the
  control that actually works? Check that they know it costs the ordinary
  search snippet too.

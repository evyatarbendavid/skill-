# Situations

Guidance that only applies when you're in a particular position. Read the
section you're in; ignore the rest.

> **Verification status.** Structural rules here (schema shapes, hreflang
> semantics, redirect practice) are documented and stable. Where a claim
> depends on current Google behavior it is marked. Re-verify anything
> date-sensitive before quoting it to someone making a decision.

---

## A large site — thousands of URLs or more

Crawl budget only becomes a real constraint somewhere past roughly ten
thousand URLs, or on any site whose content changes constantly. Below that,
worrying about it is a distraction from work that matters more.

It's the product of two things: how much load the server can take, and how
much Google thinks the site is worth crawling. You can influence both.

**Server logs are the only ground truth.** Search Console's crawl stats are
a summary and third-party crawlers are simulations. Logs are what actually
happened. On a large site, read them quarterly — monthly if it's
e-commerce or otherwise fast-moving — and look for:

- Pages Googlebot has never fetched. These are your
  "discovered, not indexed" candidates before Search Console tells you.
- URL patterns eating the budget: faceted filter combinations, internal
  search results, session IDs, infinite calendars.
- Status-code waste — redirect chains being crawled repeatedly, 5xx spikes
  that quietly reduce crawl rate for weeks after they're fixed.

**Segment logs by bot.** It is no longer just Googlebot and Bingbot. AI
crawlers can be a meaningful share of total crawl load, and a traffic
problem that looks like a Googlebot pattern is sometimes an AI crawler
hammering a paginated endpoint. See `ai-crawlers.md` for who's who.

**Sampling when auditing.** Don't audit ten thousand pages. Cluster by
template — all product pages share one, all category pages another — audit
a representative of each cluster, and fix at the shared component so the
fix propagates. State that you sampled and how. Silent sampling reported as
a full audit is the thing not to do.

---

## An e-commerce site

**Product variants.** Google's pattern is `ProductGroup` with `hasVariant`.
The group carries the shared name; each variant `Product` needs its own
identifier (GTIN or SKU), its own URL, and `variesBy` naming what
distinguishes it — color, size, material. One shared JSON-LD block covering
a page of variants is not enough.

**Out-of-stock items — do not delete the page.** This is the expensive
mistake, because it throws away every ranking signal the URL accumulated
and every link pointing at it.

- Temporarily unavailable: keep the URL live and returning 200, mark
  `availability: OutOfStock` in the schema, show alternatives, offer a
  back-in-stock notification.
- Permanently discontinued: 301 to the closest equivalent product, or to
  the category if there isn't one. Not to the homepage — a redirect that
  lands somewhere unrelated reads as a soft 404.

**Shipping and returns are now part of the markup.** `Offer` needs
`shippingDetails` and `hasMerchantReturnPolicy` for shopping rich-result
eligibility. *(Reported as a 2026 requirement change — confirm against
current documentation before telling a client to prioritize it.)*

**Reviews.** `aggregateRating` needs real reviews behind it, displayed on
the page. Presenting reviews collected elsewhere as your own is explicitly
against the spam policy — and it's the kind of thing that gets a manual
action rather than a quiet ranking drop.

---

## A site in more than one language

**Structure.** Subfolders (`/de/`, `/fr/`) are the default: one domain
accumulating authority, cheap to add, simple to maintain. Country-code
domains split that authority across separate properties and need a real
reason — genuine local-entity presence, regulatory requirement, or a market
where the local TLD carries trust the `.com` won't. Subdomains sit between
and rarely win on merit.

**hreflang is a graph, and it must be complete.** Every version lists every
other version *including itself*. A one-way link — A points to B, B doesn't
point back — is ignored, and it's the most common way hreflang is broken
while looking implemented.

**`x-default` is misunderstood constantly.** It's for a genuinely
locale-neutral destination — a language picker, a geo-router. It is not
"the fallback content page for everyone else." Pointing it at your English
page because English feels like the default is the standard error.

**Region codes must be real.** `en-EU`, `en-INTL`, and `en-GLOBAL` are
silently ignored — there is no EU region code. Use ISO codes: `en-GB`,
`en-US`, `de-AT`. Use bare `en` when the content genuinely doesn't differ
by country.

**Check canonical and hreflang together.** If a page's canonical points
elsewhere while hreflang claims that page for a locale, the canonical wins
and the hreflang is discarded. Auditing them separately is how this
survives for years.

---

## A site with a lot of thin or overlapping pages

The decision is delete, noindex, or merge — and it turns on two questions:
does the page have external links pointing at it, and can its content be
absorbed into something stronger?

- **Has links, weak content** → merge into the stronger page and 301. You
  keep the link equity.
- **No links, no traffic, nothing worth keeping** → delete. Removing genuinely
  worthless pages carries no penalty and can help how clearly the rest of
  the site reads.
- **Needed by users, not wanted in search** — thank-you pages, internal
  search results, filtered views → `noindex`, keep them live. They have a
  job; that job isn't ranking.

The reason this matters more than it used to: a cluster of near-identical
thin pages confuses systems trying to identify which page on your site is
*the* authority on a topic. That applies to classic ranking and to AI
retrieval alike.

---

## A site migration

Where migrations lose traffic is rarely the redirects themselves — it's
what got forgotten alongside them.

- **Map redirects one to one.** Pattern rules for a folder that moved
  evenly are fine; content that moved unevenly needs an explicit map. A
  pattern rule quietly sending fifty pages to one destination is a mass
  soft-404.
- **Update hreflang in the same deploy.** Old URLs redirecting correctly
  while hreflang still points at pre-migration addresses is the single most
  common cause of a migration that "went fine" and lost half its
  international traffic.
- Re-verify every property in Search Console, submit the new sitemap
  immediately, and watch Crawl Stats and the indexing report daily for the
  first fortnight.
- **Expect a dip.** Even a clean migration usually dips before recovering.
  Say that up front, so a normal dip doesn't trigger a panic rollback that
  makes things genuinely worse.

---

## Someone wants to be "an entity Google recognizes"

Worth understanding, worth being honest that the causal chain is thin.

You cannot submit anything to the Knowledge Graph. What you can do is make
the identity consistent and cross-referenced: `Organization` schema with
`sameAs` pointing to every verified profile, the same name and details
everywhere, and — where the subject genuinely qualifies — presence in the
reference sources these systems draw on.

The useful part of the idea is picking one canonical URL as the entity's
home, usually the homepage or an about page, and linking to it consistently
from everywhere else you exist. That's good practice regardless.

The rest is practitioner theory, not measurement. Present it that way.
Treat anyone selling guaranteed Knowledge Panel placement the same as
anyone selling guaranteed rankings.

# Field notes — what actually breaks on real sites

Findings from auditing live production sites with this skill's checklist,
kept separate from the documented rules because they are observations, not
requirements.

> **Read the sample before quoting the numbers.** These come from **seven
> homepages**: pypi.org, nodejs.org, docker.com, eclipse.org, apache.org,
> yarnpkg.com, rustup.rs — all well-resourced open-source and developer
> infrastructure, audited 2026-08-21. No CMS blog, no product page, no news
> site, and **no Hebrew or RTL site** is represented; the audit environment
> could not reach them. Seven pages of one kind is an anecdote with a table
> around it. Use these to know what to *look* for first, never as "N% of the
> web does X."

---

## What was missing most often

Ranked by how many of the seven failed it:

| Sites | What was missing |
|---|---|
| 7/7 | `Organization`/`Person` entity markup |
| 6/7 | Any JSON-LD at all |
| 4/7 | The homepage's own URL, absent from the site's sitemap |
| 4/7 | A clean heading hierarchy (h1→h4, two h1s) |
| 2/7 | A self-referencing canonical |

Every one of the seven had a `<title>` and a real `<h1>`. **The classic
on-page checklist was not where these sites failed.** They failed on
machine-readability: who the entity is, and whether the page is declared in
the site's own map of itself.

That is worth knowing when you prioritize. On a competently built site, the
first hour is better spent on entity identity and sitemap correctness than
on re-checking titles that are probably already fine. On a site built by
someone with no SEO exposure at all, the reverse is usually true — check
the gates and the basics first. Look before you assume which kind you have.

---

## Failure patterns worth checking by name

**The sitemap that omits the homepage.** Four sites had a working, populated
`sitemap.xml` that simply didn't list `/`. It is easy to miss precisely
because the sitemap *exists* and validates — a check that stops at "sitemap
present: yes" will never catch it. The homepage is usually the most-linked
page on the site, so this costs little for Google, which found it long ago
by other means. It costs more for an AI retrieval system meeting the site
for the first time. Check that the sitemap contains the homepage, not just
that a sitemap exists.

**One description, templated across every page.** Two sites shipped the same
meta description on four or five crawled pages — a global site-description
fallback rendering wherever a page-specific one wasn't authored. This reads
as "has a meta description" on every single page and fails the thing
descriptions are for. It is a different bug from a missing description, and
you only see it by comparing pages against each other, never by auditing one
page in isolation. When auditing a site, collect descriptions across pages
and look for repeats.

**`Crawl-Delay` still sitting in `robots.txt`.** One site specified
`Crawl-Delay: 4`. Google has not honored that directive in years — crawl
rate is a Search Console setting now. It's harmless where it sits, and it is
a reliable tell that the file hasn't been reviewed in a long time. Treat it
as a prompt to read the rest of that `robots.txt` carefully rather than as a
finding worth reporting on its own.

**Language pickers put RTL text on LTR pages.** A global site's footer
language switcher labels each option in its own script — `עברית`,
`العربية`. That is correct and should stay. It does mean "page contains
Hebrew characters" is not a test for "page is Hebrew": judge by the declared
`lang` and by how much of the content is actually RTL.

---

## AEO readiness was weak everywhere

**Zero** of the seven had a subheading phrased as a question. Query fan-out
matches user sub-questions against page structure, and on these pages there
was nothing for it to match.

The honest reading is not "these sites are bad at AEO." It is that **a
homepage is a gateway, not a citation source.** Marketing copy that
introduces a product is doing its job; it was never going to be the passage
an answer engine lifts. The mistake would be auditing a homepage for AEO,
reporting a wall of failures, and calling it an AEO assessment of the site.

So: when someone asks how their site does on AI citation, audit the pages
that answer questions — docs, guides, articles, support content. Say which
pages you looked at. If the only page available is the homepage, report
answer-shape findings as "expected for this page type" rather than as
failures, and say where a real AEO audit would need to look.

---

## Two things that surprised the audit

**Good prose and good plumbing don't travel together.** The page with the
clearest answer-first opening in the sample — apache.org, a one-line mission
statement followed by plain-language explanation — was also the page with no
canonical, no meta description, and no JSON-LD. The site with the best
structured data was a private company's marketing site, not the
twenty-five-year-old institution. **Institutional age and prestige predicted
nothing.** Don't infer that a serious organization has the technical basics
covered; check.

**Some pages don't need search at all.** rustup.rs — the page every Rust
developer is told to visit — has no `lang` attribute and no viewport meta
tag, and it doesn't matter, because nobody arrives there from a search
result. They arrive from documentation links and a `curl` command in a
README.

Technical SEO correctness and real-world usefulness are decoupled whenever a
page's distribution channel isn't search. Before ranking fixes, ask how the
page actually gets its visitors. On a page reached by direct link, most SEO
findings are correctly ignored — and the accessibility ones (`lang`,
viewport) still are not, because those affect every visitor regardless of
how they arrived. Separating those two is the useful judgment; reporting all
of it at equal weight is not.

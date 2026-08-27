# Working in code

Read this when there is code in front of you — a pasted component, a local
repo, a framework project — or when there's no page yet and you're writing
one. The page-level rules in `SKILL.md` still apply; this is what changes
when you can see and edit the source.

---

## Building a new page from scratch

Nothing to audit yet. This needs no web access at all — no fetch, no live
URL, nothing a blocked network can interrupt. The check sections in
`SKILL.md` are the spec; this is the order to bake them in while writing,
so a page ships right instead of getting a retrofit pass later.

**1. The `<head>`, complete, before any content is written.** Cheap now,
expensive as a rewrite once the page exists:

```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><!-- primary term first, 50-60 chars --></title>
  <meta name="description" content="<!-- 140-160 chars, click-through copy, not a summary -->">
  <link rel="canonical" href="<!-- this page's own real URL — never a dev address -->">
  <meta property="og:title" content="<!-- can match <title> -->">
  <meta property="og:description" content="<!-- can match the meta description -->">
  <meta property="og:image" content="<!-- 1200x630 -->">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
</head>
```

**2. One `<h1>` stating the page's purpose**, subheadings phrased the way
someone would actually ask — `SKILL.md`'s AEO section covers what
"question-shaped" means and when a plain label is correct instead.

**3. The opening paragraph answers before it explains.** Two sentences,
direct, before any scene-setting — this is the single highest-leverage AEO
decision and it costs nothing while the page is still being drafted.
`references/examples.md` §1 has the before/after.

**4. `Organization` JSON-LD, sitewide, from the first page.** Fill only
what is actually known; leave the rest `TODO` rather than inventing a
value — fabricated markup is a spam-policy violation even on a page that
hasn't launched yet:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "TODO",
  "url": "TODO: the real domain, not localhost",
  "logo": { "@type": "ImageObject", "url": "TODO" },
  "sameAs": ["TODO: real profile URLs, or remove this array entirely"]
}
```

**5. Images ship with `alt`, `width`, and `height` from the first commit.**
Adding these across a site nobody built with them in mind is the expensive
version of a decision that takes five seconds now.

**6. Use the framework's own metadata API, not raw `<head>` HTML, once the
framework is known.** The table below has the mapping — the skeleton above
is the *content* every one of those APIs needs; only the syntax changes.

---

**One pasted component is still worth a real answer.** Most of the
checklist needs the page, but a component carries its own bugs and they are
worth naming rather than deflecting with "I'd need the whole site":

- **A clickable thing built from `<div onClick>` instead of `<a href>`.**
  This is the most common SEO bug in React code and it is fully visible in
  one file. A crawler follows `href`s; it does not fire click handlers, so
  a card, tile, or "read more" built this way is a link that no search
  engine and no AI crawler can follow. It also can't be opened in a new
  tab, middle-clicked, or reached by keyboard. `<a href>` styled as a card
  does everything the div did.
- Images with no `alt`, or `loading="lazy"` on something that is plainly
  the hero.
- Anchor text that describes nothing — "click here", "read more",
  "לחץ כאן" — where the component knows the destination and could say it.
- Heading level chosen for size. You cannot judge `h2` vs `h3` without the
  page, so say that instead of guessing — but an `h1` inside a repeated
  card component is wrong from the file alone.
- Text baked into an image, and interactive elements with no accessible
  name.

Say which findings are certain from this file and which need the route.
That distinction is the useful part; a flat "send me more" is not.

**On a framework project, the page is not an HTML file.** Most sites people
bring are Next.js, Astro, SvelteKit, Nuxt, or similar, and the two things
audits most often want to change — head tags and `sitemap.xml` — are not
where a static site puts them:

| Project | Head tags come from | A static `sitemap.xml` goes in |
|---|---|---|
| Next.js app router | `export const metadata` / `generateMetadata` in `page.tsx`, `layout.tsx` | `public/` — unless `app/sitemap.ts` exists, which generates it |
| Next.js pages router | `next/head` in the page, `_app` / `_document` | `public/` |
| Astro | a layout component in `src/layouts/` | `public/` |
| SvelteKit | `<svelte:head>` in `+page.svelte`, `+layout.svelte` | `static/` |
| Nuxt | `useHead` / `definePageMeta`, `app.vue` | `public/` |
| Gatsby | the `Head` export, or the starter's `Seo` component | `static/` |
| Hugo / Jekyll | templates in `layouts/` or `_layouts`, values from front matter | it generates one; don't add a second |

Two consequences worth stating rather than discovering. A `sitemap.xml`
written to the repository root of any of these is **not served** — the fix
looks applied and changes nothing. And a fix belongs at the route file that
produces the URL (`/products/copper-kettle` → `app/products/[slug]/page.tsx`),
which means it applies to every page that route serves — say that, because
it is more pages than were audited.

**Never write a URL you got from a dev server into a source file.** Working
from a local project, the address in front of you is `localhost:3000` — and
a canonical tag, a sitemap entry, or a JSON-LD `url` built from it ships a
developer's machine to production, where it is worse than the tag being
missing. Ask for the real domain before writing any of them. If you don't
have it, leave the value as an explicit `TODO` and say which fields are
waiting on it, rather than filling in something that looks complete and
isn't.

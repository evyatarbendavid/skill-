# Working in code

Read this when there is code in front of you — a pasted component, a local
repo, a framework project. The page-level rules in `SKILL.md` still apply;
this is what changes when you can see and edit the source.

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

# Worked examples

Before-and-after for the things that are easy to agree with in principle and
easy to get wrong in practice.

---

## 1. The answer-first rewrite

This is the single highest-leverage edit for AEO. Same facts both times —
only the order changed.

### Before — the answer is buried

> ## Choosing a standing desk
>
> When we started testing standing desks back in 2023, the category was a
> mess. Manufacturers were making wild claims, review sites were mostly
> republishing spec sheets, and the few genuinely useful data points were
> buried in forum threads. We spent eight months and tested forty-one desks
> before we felt we understood the category well enough to write about it.
> What we eventually found, after all that, was that the single most
> important specification is the height range — most adults need a desk
> that travels from about 60cm to 125cm.

The useful sentence is the last one. An extraction system reading the first
40 words gets a story about the authors. Nothing citable.

### After — answer first, story second

> ## What height range do you need in a standing desk?
>
> Most adults need a desk that travels from **60cm to 125cm**. Measure your
> elbow height seated and standing before shopping — if either measurement
> falls outside the desk's range, no amount of adjustment fixes it.
>
> We reached that range across eight months and forty-one desks tested. The
> outliers matter: under 165cm tall, look for a 58cm minimum; over 195cm,
> confirm the desk exceeds 128cm before ordering.

What changed:

- **Heading is the question**, phrased the way someone would search it.
- **First sentence is a complete answer.** It survives being lifted out of
  the page with no surrounding context — which is exactly what happens.
- **A specific number, early.** "60cm to 125cm" is groundable. "The right
  height for you" is not.
- **Credibility follows the answer** instead of delaying it. The eight
  months and forty-one desks still do their E-E-A-T work in paragraph two.

The story wasn't deleted. It was moved behind the answer.

### Same thing in Hebrew

**Before:**

> ## על בחירת שולחן עמידה
>
> כשהתחלנו לבדוק שולחנות עמידה, גילינו שוק מבולגן — יצרנים עם הבטחות
> מוגזמות, אתרי ביקורות שפשוט משכתבים מפרטים טכניים, ומעט מאוד מידע אמין.
> אחרי שמונה חודשים וארבעים ואחד שולחנות שבדקנו, הבנו שהמפרט הכי חשוב
> הוא טווח הגובה.

**After:**

> ## איזה טווח גובה צריך בשולחן עמידה?
>
> רוב המבוגרים צריכים שולחן שנע בין **60 ל-125 ס"מ**. מדדו את גובה המרפק
> בישיבה ובעמידה לפני הקנייה — אם אחת מהמדידות מחוץ לטווח של השולחן, שום
> כוונון לא יפתור את זה.
>
> הגענו לטווח הזה אחרי שמונה חודשים ו-41 שולחנות שבדקנו.

Note the numbers are written as digits inside Hebrew text. That is correct
and searchable — but see §4 below, because it is also where bidi bugs live.

---

## 2. Title and meta description

### Before

```html
<title>Home | ErgoDesk Israel - Standing Desks, Office Chairs, Monitor Arms, Accessories and More</title>
<meta name="description" content="Welcome to our website.">
```

Two failures: the title is 96 characters and truncates to "Home | ErgoDesk
Israel - Standing Desks, Office Chairs, Mon…", spending its most valuable
position on the word "Home". The description says nothing, so Google
composes its own snippet from whatever text it finds.

### After

```html
<title>Standing Desks Tested and Compared — ErgoDesk Israel</title>
<meta name="description" content="We tested 41 standing desks over eight months. Height range, stability at full extension, and motor noise measured — with the three mistakes buyers make most often.">
```

- **51 characters**, primary term first, brand last where it still gets seen.
- **Description is 168 characters** of click-through copy. It does not affect
  ranking. It affects whether anyone clicks, which is the only thing a
  description was ever for.
- It promises something specific. "Welcome to our website" promises nothing.

---

## 3. JSON-LD that actually validates

Annotated — the comments explain the parts people get wrong. Strip them
before shipping; JSON does not allow comments.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",

  "headline": "What Height Range Do You Need in a Standing Desk?",
  // Under ~110 chars, and it matches the visible h1. A headline that
  // disagrees with the page is worse than none.

  "image": ["https://example.com/desk-hero-16x9.webp"],
  // Required. Multiple aspect ratios (16x9, 4x3, 1x1) if you have them.

  "datePublished": "2026-02-01",
  "dateModified": "2026-08-18",
  // ISO 8601. dateModified is a real freshness signal for AEO — but only
  // set it when the content actually changed. Bumping it on a whitespace
  // edit is the kind of thing that erodes trust when noticed.

  "author": {
    "@type": "Person",
    "name": "Dana Levi",
    "url": "https://example.com/about/dana-levi",
    "jobTitle": "Ergonomics researcher"
  },
  // A nested Person, not a bare string. This is the structured-data half
  // of E-E-A-T. "author": "Team" does nothing for you.

  "publisher": {
    "@type": "Organization",
    "name": "ErgoDesk Israel",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },

  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/guides/standing-desk-height/"
  }
  // The canonical URL of this page. Ties the markup to one URL.
}
```

### The bug to check for first

The most common self-inflicted schema failure is markup describing content
that is not on the page. Before shipping any block, read it back against the
rendered page and confirm every claim is visible to a human. `FAQPage`
markup for questions that appear nowhere is the classic case — and since FAQ
rich results were removed entirely in May 2026, that markup now carries all
of the spam risk and none of the upside.

---

## 4. RTL and bidi

### The bug

```html
<html lang="he">
  <p>מחקר של Stanford University משנת 2024 מצא ירידה של 32 אחוז</p>
```

Two problems. There is no `dir="rtl"`, so the whole page lays out
left-to-right. And even once that is fixed, the Latin run and the numbers
sit inside a Hebrew paragraph with no isolation — so where the bidi
algorithm places them depends on what surrounds them. Adjacent numbers and
punctuation can visibly reorder.

### The fix

```html
<html lang="he" dir="rtl">
  <p>מחקר של <bdi>Stanford University</bdi> משנת <bdi>2024</bdi> מצא ירידה של 32 אחוז</p>
```

`<bdi>` isolates the run so its internal direction cannot leak into the
surrounding text. For anything user-generated or coming from a database —
names, addresses, product titles — use `dir="auto"` on the container
instead, since you cannot know in advance which direction the content will
be.

### Where it hides

The root element is the easy part. Check nested components: LTR-authored
component libraries frequently hardcode `dir="ltr"` on their own wrappers,
and modals and toasts injected at the document root often do not inherit
the page's direction at all. A page that looks correct until a dialog opens
is the common shape of this bug.

---

## 5. Reporting a finding

Findings get acted on in proportion to how specific they are.

**Useless:**

> Missing alt text. Add alt text to images.

**Useful:**

> **High — `img.hero-banner` has no `alt` attribute** (`Hero.jsx`, line 14).
> It is also the LCP element and is `loading="lazy"`, which delays the
> largest paint on every visit.
> Fix: add a description of what the image shows, and drop `loading="lazy"`
> from this one image — lazy-loading is for below the fold.

Name the element and the file. State why it matters. Give the fix. Rank it
against everything else, so the reader knows what to do first rather than
being handed twenty equal-looking items.

---

## 6. A complete report for one page

The shape matters as much as the content. Someone who receives twenty
equal-looking bullets does nothing; someone who receives this fixes the top
two before lunch.

This example is a small bakery's product page, reviewed from a live URL with
no repo access — so nothing here is fixed, and the report says so at the top
rather than ending with fixes that were never applied.

---

> ## `example.co.il/breads/challah` — review
>
> **How I checked:** fetched the page and its `robots.txt` and
> `sitemap.xml`; read the served HTML, not the rendered page. Core Web
> Vitals come from PageSpeed Insights field data (real Chrome users, 28-day
> rolling, mobile). I could not check Search Console — that needs your
> login — so anything about impressions or coverage is outside what I can
> see.
>
> **Since I only have the URL, I can't change anything.** Everything below
> is a description of what to change and where.
>
> ### Gates — one is failing
>
> | | |
> |---|---|
> | HTTP 200 | ✅ |
> | Not blocked in `robots.txt` | ✅ |
> | No `noindex` | ✅ |
> | Content in the served HTML | ✅ |
> | Core Web Vitals | ❌ **LCP 4.1s** (needs ≤2.5s) |
>
> Nothing else on this page matters as much as the LCP number. A page this
> slow on a phone is competing with a handicap no amount of good content
> makes up for.
>
> ### Critical
>
> **LCP is 4.1s on mobile; the cause is the hero image.**
> `challah-hero.jpg` is 2.4 MB, served as a JPEG at full desktop size to
> phones as well, with no width or height on the `<img>`. Three fixes, in
> order of payoff: export it as WebP (usually 60–70% smaller at the same
> visible quality), add a `srcset` so phones get a phone-sized file, and put
> explicit `width`/`height` on the tag so the layout stops jumping while it
> loads. Expect this one change to move LCP under 2.5s on its own.
>
> ### High
>
> **The page never says what challah is.** It opens with "Our bakery has
> been family-run since 1961" and gets to the product in the fourth
> paragraph. Someone asking an AI "what is challah" will be answered from a
> page that says so in its first sentence, and this isn't one. Move a
> two-sentence direct answer to the top; the family story stays, one
> paragraph lower. See §1 above for the same edit worked through.
>
> **No `Organization` markup anywhere on the site.** Nothing tells Google or
> an AI engine that this bakery is a specific business with an address, a
> phone number, and a Facebook page — it has to infer it from prose. This is
> cheap to add once, sitewide, and it's the single most commonly missing
> thing on otherwise well-built sites. `LocalBusiness` (a subtype of
> `Organization`) is the right type here, with `address`, `openingHours`,
> and `sameAs` pointing at the profiles you actually run.
>
> ### Medium
>
> **The meta description is the same on all eleven product pages.** It reads
> "Fresh bread baked daily at our family bakery" everywhere. That passes any
> check asking "is there a description" and fails the only thing a
> description does, which is give someone a reason to click *this* result
> rather than the one above it. One per product.
>
> **Latin text inside Hebrew renders in the wrong order.** In the
> ingredients list, `שמן זית Extra Virgin 500ml` displays with the `500ml`
> in the wrong place on some browsers. Wrap the Latin run in `<bdi>`. Full
> explanation in §4.
>
> ### Low
>
> **No `og:image`.** When someone shares this page on WhatsApp, it appears
> as a bare link with no picture — for a bakery, where the picture is the
> product, that's a real loss for a five-minute fix.
>
> ### One decision I need from you
>
> Two addresses show this same page — `example.co.il/challah` and
> `example.co.il/breads/challah`. Google will pick one to show and quietly
> ignore the other, and right now it's picking for you. Which should people
> land on? Whichever you choose, the other gets pointed at it, so no one
> hits a dead end and no links break.
>
> *(The technical name for this is the canonical URL, if you want to look it
> up or ask someone else about it.)*
>
> ### What I could not check
>
> - **Search Console data** — impressions, click-through, coverage errors.
>   Needs your account.
> - **The other ten product pages.** They share a template, so the
>   description and schema findings almost certainly apply to all of them,
>   but I looked at one and I'm not going to claim I looked at eleven.
> - **INP** — no field data yet for this page, which usually means low
>   traffic rather than good performance. Not a pass; an unknown.

---

What makes that report work, and what to copy from it:

- **The gates are a table at the top, and a failing one is named as the
  thing that matters most.** Not buried at position nine in a flat list.
- **Ranked, and the ranking is honest.** The 2.4 MB image outranks the
  missing `og:image` by a wide margin, and the report says so instead of
  presenting both as findings.
- **Every finding names the file or element, why it matters, and the fix.**
- **The decision is asked in the owner's language**, with the technical term
  parked in an aside for whoever wants it.
- **The limits are stated in two places** — what tools were used at the top,
  what couldn't be reached at the bottom. Neither is an apology; both stop
  the reader from believing the report covers more than it does.
- **Sampling is admitted.** "I looked at one and I'm not going to claim I
  looked at eleven" is the line that keeps an audit trustworthy.

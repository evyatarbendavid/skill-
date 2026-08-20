# Structured data property reference

Mirror of the validation rules in `scripts/seo_aeo/structured_data.py`. Keep the
two in sync — if you change one, change the other.

**Format:** JSON-LD in a `script type="application/ld+json"` block. Google's
recommended format. Always include `"@context": "https://schema.org"`.

**Two firm rules (Google spam policy):**
1. Only mark up content that is **actually visible on the page**.
2. Supply all **required** properties, or the type is not eligible.

---

## Article / BlogPosting / NewsArticle

For content pages. `BlogPosting` and `NewsArticle` are subtypes of `Article` —
pick the most specific one that is true.

| Property | Status | Notes |
|---|---|---|
| `headline` | **Required** | Keep under ~110 chars. Should match the visible `h1`. |
| `image` | **Required** | URL or ImageObject. Multiple aspect ratios preferred (16x9, 4x3, 1x1). |
| `datePublished` | **Required** | ISO 8601. |
| `author` | **Required** | Nested `Person` (or `Organization`). **Never fabricate.** |
| `dateModified` | Recommended | ISO 8601. Strong freshness/trust signal. |
| `publisher` | Recommended | Nested `Organization` with `name` + `logo`. |
| `mainEntityOfPage` | Recommended | The canonical page URL. |
| `description` | Recommended | Short summary. |

`author` should be a real `Person` object with `name` and ideally `url` /
`sameAs` / `jobTitle` — this is the structured-data half of E-E-A-T.

## Organization

Site-wide identity. One per site, typically on the homepage.

| Property | Status | Notes |
|---|---|---|
| `name` | **Required** | |
| `url` | **Required** | Canonical homepage URL. |
| `logo` | Recommended | ImageObject or URL. Needed for Knowledge Panel eligibility. |
| `sameAs` | Recommended | Array of URLs to **real, verifiable** profiles (LinkedIn, X, GitHub, Wikipedia). Never invent these. |
| `description` | Optional | |
| `contactPoint` | Optional | |

## Person

For a solo author-site, or as the `author` of an Article.

| Property | Status | Notes |
|---|---|---|
| `name` | **Required** | |
| `url` | Recommended | Author/about page. |
| `jobTitle` | Recommended | Credential signal. |
| `sameAs` | Recommended | Real profiles only. |
| `description` | Recommended | Short bio establishing expertise. |
| `image` | Optional | |

## BreadcrumbList

Clarifies site hierarchy; still produces breadcrumb display in results.

| Property | Status | Notes |
|---|---|---|
| `itemListElement` | **Required** | Array of `ListItem`. |
| → `position` | **Required** | 1-based integer, in order. |
| → `name` | **Required** | Visible breadcrumb label. |
| → `item` | Required except last | URL. The final (current-page) item may omit it. |

Must match the **visible** breadcrumb on the page.

## WebSite (+ SearchAction)

Optional. Sitelinks search box.

| Property | Status |
|---|---|
| `name` | **Required** |
| `url` | **Required** |
| `potentialAction` (`SearchAction`) | Optional |

---

## Types that no longer produce rich results

Valid Schema.org vocabulary — Google may still read them for page understanding —
but they earn **no SERP rich result**. Do not add them expecting SERP real
estate, and do not present them to a user as a ranking or citation lever.

| Type | Status |
|---|---|
| `FAQPage` | Restricted Aug 2023; **fully removed for all sites May 7, 2026** |
| `HowTo` | Deprecated mobile Aug 2023, desktop Sep 2023 |
| `Book` (Book Actions) | Retired June 2025 |
| `Course` (Course Info) | Retired June 2025 |
| `ClaimReview` | Retired June 2025 |
| `Occupation` (Estimated Salary) | Retired June 2025 |
| `LearningResource` (Learning Video) | Retired June 2025 |
| `SpecialAnnouncement` | Retired June 2025 |
| `Vehicle` (Vehicle Listing) | Retired June 2025 |

Unused structured data does **not** hurt Search rankings — it simply does
nothing. Leaving existing FAQPage markup in place is fine; adding it as a
*strategy* is not.

> **Re-verify before recommending any type for its rich result.** Google prunes
> these regularly. See `live-verification-map.md`.

---

## Common validation failures

| Symptom | Cause |
|---|---|
| "Missing field 'author'" | `author` given as a bare string where Google expects a `Person` object. A string often still validates, but the object form is stronger. |
| Dates rejected | Not ISO 8601. Use `2026-08-17` or `2026-08-17T10:30:00+03:00`. |
| "Invalid object type for field" | `@type` missing on a nested object. |
| Multiple conflicting entities | Several JSON-LD blocks describing the same thing differently. Use `@id` to link, or consolidate into one `@graph`. |
| Rich result not showing despite valid markup | Validity grants *eligibility* only. Google still decides. Not a bug. |
| Markup describes content not on the page | **Spam-policy violation.** Remove it. |

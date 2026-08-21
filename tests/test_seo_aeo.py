#!/usr/bin/env python3
"""Test suite for the seo-aeo skill.

Hermetic: everything runs against in-process fixtures or a local HTTP server on
a loopback port. No outbound network, so the suite is meaningful in a sandbox
where the proxy blocks most hosts.

    python3 tests/test_seo_aeo.py           # or: python3 -m unittest discover tests
"""

import http.server
import json
import shutil
import socketserver
import sys
import types
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "tools-seo-audit-cli" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from seo_aeo import (  # noqa: E402
    accessibility, aeo, canonical, crawler, fixers, htmldoc,
    pathmap, quality, report, sitemap, structured_data,
)
from seo_aeo.fetch import _decode_body, normalize_url, same_host  # noqa: E402
import audit  # noqa: E402
from seo_aeo import fetch as fetch_mod  # noqa: E402
from seo_aeo.models import (  # noqa: E402
    CRITICAL, FAIL, HUMAN_JUDGMENT, LOW, NA, PASS, WARN,
    AuditResult, Finding,
)

PAGE_FULL = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A Perfectly Reasonable Page Title For Testing</title>
  <meta name="description" content="A meta description of a believable length, written the way real CTR copy is written, long enough to fill the snippet slot properly.">
  <link rel="canonical" href="https://example.com/page">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Article",
   "headline":"H","image":["https://example.com/i.jpg"],
   "datePublished":"2026-01-01","author":{"@type":"Person","name":"Real Person"}}
  </script>
</head>
<body>
  <nav><a href="/about">About the project</a></nav>
  <main>
    <h1>Main Heading</h1>
    <h2>What is this?</h2>
    <p>An answer sentence.</p>
    <ul><li>one</li><li>two</li><li>three</li></ul>
    <img src="/a.webp" alt="Descriptive alt" width="80" height="60">
    <img src="/deco.webp" alt="">
  </main>
</body>
</html>"""


class TestHtmlParsing(unittest.TestCase):
    def setUp(self):
        self.doc = htmldoc.parse(PAGE_FULL)

    def test_extracts_head_metadata(self):
        self.assertEqual(self.doc.title, "A Perfectly Reasonable Page Title For Testing")
        self.assertEqual(self.doc.lang, "en")
        self.assertEqual(self.doc.canonical, "https://example.com/page")
        self.assertTrue(self.doc.has_viewport)
        self.assertIn("believable length", self.doc.meta_description)

    def test_extracts_structure(self):
        self.assertEqual(self.doc.h1s, ["Main Heading"])
        self.assertEqual(len(self.doc.images), 2)
        self.assertTrue(self.doc.has_main)
        self.assertTrue(self.doc.has_nav)
        self.assertEqual(len(self.doc.jsonld_raw), 1)

    def test_script_content_is_not_visible_text(self):
        # JSON-LD lives in a script tag; counting it as page copy would inflate
        # word counts and corrupt duplicate-content hashes.
        self.assertNotIn("schema.org", self.doc.visible_text)
        self.assertIn("An answer sentence.", self.doc.visible_text)

    def test_malformed_html_does_not_raise(self):
        doc = htmldoc.parse("<html><head><title>x</title><body><p>unclosed")
        self.assertEqual(doc.title, "x")

    def test_head_insert_offset(self):
        self.assertIsNotNone(htmldoc.head_insert_offset(PAGE_FULL))
        self.assertIsNone(htmldoc.head_insert_offset("<html><body>no head</body></html>"))

    def test_noindex_detection(self):
        self.assertFalse(htmldoc.has_noindex(self.doc))
        doc = htmldoc.parse('<html><head><meta name="robots" content="noindex, follow"></head></html>')
        self.assertTrue(htmldoc.has_noindex(doc))


class TestFetchDecoding(unittest.TestCase):
    def test_gzip_decoded_with_lowercase_header(self):
        # Regression: header lookup used to be case-sensitive, so gzip bodies
        # were never decompressed and every content check ran on binary noise.
        import gzip
        raw = gzip.compress(b"<html><title>hi</title></html>")
        out = _decode_body(raw, {"content-encoding": "gzip"})
        self.assertIn("<title>hi</title>", out)

    def test_gzip_detected_by_magic_bytes(self):
        import gzip
        raw = gzip.compress(b"<p>magic</p>")
        self.assertIn("magic", _decode_body(raw, {}))

    def test_url_normalization(self):
        self.assertEqual(normalize_url("https://X.com/a#frag"), "https://x.com/a")
        self.assertEqual(normalize_url("https://x.com"), "https://x.com/")
        self.assertTrue(same_host("https://www.x.com/a", "https://x.com/b"))
        self.assertFalse(same_host("https://x.com", "https://y.com"))


class TestCanonical(unittest.TestCase):
    def _check(self, html, url="https://example.com/page"):
        return canonical.check(htmldoc.parse(html), url)

    def test_missing_is_the_only_auto_fixable_case(self):
        result = self._check("<html><head></head></html>")
        self.assertEqual(result.classification, canonical.MISSING)
        self.assertTrue(result.auto_fixable)

    def test_self_referencing_passes(self):
        result = self._check('<html><head><link rel="canonical" href="https://example.com/page"></head></html>')
        self.assertEqual(result.classification, canonical.SELF)
        self.assertFalse(result.auto_fixable)

    def test_cross_domain_needs_a_human(self):
        result = self._check('<html><head><link rel="canonical" href="https://other.com/x"></head></html>')
        self.assertEqual(result.classification, canonical.CROSS_DOMAIN)
        self.assertTrue(result.needs_human)
        self.assertFalse(result.auto_fixable)

    def test_other_page_same_site_needs_a_human(self):
        result = self._check('<html><head><link rel="canonical" href="/other"></head></html>')
        self.assertEqual(result.classification, canonical.OTHER_SAME_SITE)
        self.assertTrue(result.needs_human)

    def test_multiple_canonicals_needs_a_human(self):
        result = self._check('<html><head>'
                             '<link rel="canonical" href="https://example.com/page">'
                             '<link rel="canonical" href="https://example.com/other">'
                             '</head></html>')
        self.assertEqual(result.classification, canonical.MULTIPLE)
        self.assertTrue(result.needs_human)


class TestStructuredData(unittest.TestCase):
    def test_required_properties_enforced(self):
        result = structured_data.analyze(['{"@type":"Article","headline":"H"}'])
        self.assertFalse(result.all_valid)
        missing = result.blocks[0].missing_required["Article"]
        self.assertIn("image", missing)
        self.assertIn("author", missing)

    def test_valid_article_passes(self):
        result = structured_data.analyze(['''{"@type":"Article","headline":"H",
            "image":"i.jpg","datePublished":"2026-01-01","author":{"@type":"Person","name":"P"}}'''])
        self.assertTrue(result.all_valid)
        self.assertTrue(result.has_article())

    def test_invalid_json_is_reported_not_raised(self):
        result = structured_data.analyze(['{not json'])
        self.assertTrue(result.parse_errors)
        self.assertFalse(result.has_any)

    def test_one_bad_block_does_not_hide_the_others(self):
        result = structured_data.analyze(['{bad', '{"@type":"Person","name":"P"}'])
        self.assertEqual(len(result.parse_errors), 1)
        self.assertTrue(result.has_type("Person"))

    def test_graph_entities_are_found(self):
        result = structured_data.analyze(
            ['{"@context":"https://schema.org","@graph":[{"@type":"Organization","name":"N","url":"u"}]}'])
        self.assertTrue(result.has_type("Organization"))
        self.assertTrue(result.all_valid)

    def test_organization_subtypes_count_as_organization(self):
        # Regression, found auditing docker.com: valid Corporation markup with
        # sameAs links was reported as "no Organization or Person markup",
        # failing exactly the sites that implemented entity markup properly.
        result = structured_data.analyze(
            ['{"@type":"Corporation","name":"Docker","url":"https://www.docker.com/",'
             '"sameAs":["https://github.com/docker"]}'])
        self.assertTrue(result.has_type("Organization", "Person"))
        self.assertTrue(result.all_valid)
        for subtype in ("Restaurant", "OnlineStore", "NGO", "CollegeOrUniversity"):
            sub = structured_data.analyze(
                ['{"@type":"%s","name":"N","url":"u"}' % subtype])
            self.assertTrue(sub.has_type("Organization"), subtype)

    def test_unrelated_types_still_do_not_count_as_organization(self):
        result = structured_data.analyze(['{"@type":"WebPage","name":"N"}'])
        self.assertFalse(result.has_type("Organization", "Person"))

    def test_a_subtype_inherits_its_parents_required_properties(self):
        # Corporation is an Organization, so it owes name and url too — before
        # the fix, subtypes were exempt from validation entirely.
        result = structured_data.analyze(['{"@type":"Corporation","name":"Acme"}'])
        self.assertIn("url", result.blocks[0].missing_required["Corporation"])

    def test_breadcrumblist_is_not_widened_by_the_subtype_map(self):
        result = structured_data.analyze(['{"@type":"Corporation","name":"N","url":"u"}'])
        self.assertFalse(result.has_type("BreadcrumbList"))

    def test_dead_rich_result_types_noted_but_not_failed(self):
        result = structured_data.analyze(['{"@type":"FAQPage","mainEntity":[]}'])
        notes = " ".join(result.blocks[0].notes)
        self.assertIn("FAQPage", notes)
        # Deprecated markup is harmless to keep — it must not be a hard failure.
        self.assertFalse(result.blocks[0].missing_required)


class TestSitemap(unittest.TestCase):
    def test_urlset_parsing_and_membership(self):
        result = sitemap.SitemapResult()
        result.urls = {normalize_url("https://example.com/a")}
        self.assertTrue(result.lists("https://example.com/a"))
        self.assertFalse(result.lists("https://example.com/b"))


class TestPathmap(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "index.html").write_text("<html></html>")
        (self.dir / "guide").mkdir()
        (self.dir / "guide" / "index.html").write_text("<html></html>")
        (self.dir / "node_modules").mkdir()
        (self.dir / "node_modules" / "index.html").write_text("<html></html>")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_resolves_root_and_directory_urls(self):
        self.assertEqual(pathmap.resolve(self.dir, "https://x.com/"),
                         (self.dir / "index.html").resolve())
        self.assertEqual(pathmap.resolve(self.dir, "https://x.com/guide/"),
                         (self.dir / "guide" / "index.html").resolve())

    def test_unknown_url_returns_none_rather_than_guessing(self):
        self.assertIsNone(pathmap.resolve(self.dir, "https://x.com/nope/"))
        self.assertIn("could not find", pathmap.explain_failure(self.dir, "https://x.com/nope/"))

    def test_build_output_is_never_writable(self):
        self.assertTrue(pathmap.is_forbidden(self.dir / "node_modules" / "index.html", self.dir))
        self.assertIsNone(pathmap.resolve(self.dir, "https://x.com/node_modules/"))

    def test_server_rendered_extension_is_refused(self):
        reason = pathmap.explain_failure(self.dir, "https://x.com/page.php")
        self.assertIn("non-HTML extension", reason)


class TestBlockedNetworkIsNotASiteFailure(unittest.TestCase):
    """A blocking proxy answers a CONNECT with a 403 that looks exactly like a
    403 from the origin — same status line, plausible headers, empty body.
    Reporting that as "this page returns 403" makes a confident, specific
    claim about the wrong machine."""

    def _result(self, error):
        return fetch_mod.FetchResult(url="https://example.com/", error=error)

    def test_proxy_and_dns_failures_are_recognized_as_local(self):
        for error in (
            "URLError: Tunnel connection failed: 403 Forbidden",
            "URLError: <urlopen error [Errno 111] Connection refused>",
            "URLError: [Errno -2] Name or service not known",
            "URLError: [Errno -3] Temporary failure in name resolution",
            "OSError: [Errno 113] No route to host",
            "URLError: certificate verify failed: unable to get local issuer",
        ):
            self.assertTrue(self._result(error).blocked_locally, error)

    def test_a_real_server_response_is_not_treated_as_local(self):
        # An origin 404 or 500 is evidence about the site and must still fail.
        self.assertFalse(fetch_mod.FetchResult(
            url="https://example.com/", status=404).blocked_locally)
        self.assertFalse(
            self._result("HTTPError: 500 Internal Server Error").blocked_locally)

    def test_no_error_is_not_a_block(self):
        self.assertFalse(fetch_mod.FetchResult(
            url="https://example.com/", status=200).blocked_locally)


class TestFrameworkProjects(unittest.TestCase):
    """Most sites people ask about are framework projects. The tool only edits
    static HTML — the right limit — but "could not find index.html" reads as a
    broken tool rather than as the real answer, which is that the pages are
    route files and here is the one behind this URL."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, relative, content="x"):
        path = self.dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def _pkg(self, **deps):
        self._write("package.json", json.dumps({"dependencies": deps}))

    def test_plain_html_project_is_not_a_framework(self):
        self._write("index.html", "<html></html>")
        self.assertIsNone(pathmap.detect_framework(self.dir))

    def test_next_app_router_detected_and_routed(self):
        self._pkg(next="15.0.0")
        self._write("app/page.tsx")
        self._write("app/about/page.tsx")
        self._write("app/products/[slug]/page.tsx")
        fw = pathmap.detect_framework(self.dir)
        self.assertIn("app router", fw.name)
        self.assertEqual(pathmap.likely_source(self.dir, "https://x.com/"),
                         self.dir / "app" / "page.tsx")
        self.assertEqual(pathmap.likely_source(self.dir, "https://x.com/about"),
                         self.dir / "app" / "about" / "page.tsx")
        # A dynamic segment serves any value in that position.
        self.assertEqual(
            pathmap.likely_source(self.dir, "https://x.com/products/copper-kettle"),
            self.dir / "app" / "products" / "[slug]" / "page.tsx")

    def test_src_app_layout_is_found_too(self):
        self._pkg(next="15.0.0")
        self._write("src/app/page.tsx")
        fw = pathmap.detect_framework(self.dir)
        self.assertEqual(fw.routes_dir, "src/app")

    def test_sveltekit_detected_and_routed(self):
        self._pkg(**{"@sveltejs/kit": "2.0.0"})
        self._write("src/routes/+page.svelte")
        self._write("src/routes/about/+page.svelte")
        self.assertEqual(pathmap.detect_framework(self.dir).name, "SvelteKit")
        self.assertEqual(pathmap.likely_source(self.dir, "https://x.com/about"),
                         self.dir / "src" / "routes" / "about" / "+page.svelte")

    def test_astro_and_gatsby_are_distinguished_by_dependency(self):
        self._pkg(astro="5.0.0")
        self._write("src/pages/index.astro")
        self.assertEqual(pathmap.detect_framework(self.dir).name, "Astro")

    def test_next_pages_router_flat_file(self):
        self._pkg(next="14.0.0")
        self._write("pages/about.tsx")
        self.assertEqual(pathmap.detect_framework(self.dir).name,
                         "Next.js (pages router)")
        self.assertEqual(pathmap.likely_source(self.dir, "https://x.com/about"),
                         self.dir / "pages" / "about.tsx")

    def test_two_dynamic_routes_are_ambiguous_and_return_none(self):
        # Guessing between them would edit the wrong file.
        self._pkg(next="15.0.0")
        self._write("app/[category]/page.tsx")
        self._write("app/[slug]/page.tsx")
        self.assertIsNone(pathmap.likely_source(self.dir, "https://x.com/kettles"))

    def test_an_exact_directory_beats_a_dynamic_one(self):
        self._pkg(next="15.0.0")
        self._write("app/about/page.tsx")
        self._write("app/[slug]/page.tsx")
        self.assertEqual(pathmap.likely_source(self.dir, "https://x.com/about"),
                         self.dir / "app" / "about" / "page.tsx")

    def test_route_files_in_build_output_are_ignored(self):
        self._pkg(next="15.0.0")
        self._write(".next/server/app/page.tsx")
        self.assertIsNone(pathmap.detect_framework(self.dir))

    def test_failure_message_names_the_framework_and_the_route_file(self):
        self._pkg(next="15.0.0")
        self._write("app/products/[slug]/page.tsx")
        message = pathmap.explain_failure(self.dir, "https://x.com/products/kettle")
        self.assertIn("Next.js", message)
        self.assertIn("app/products/[slug]/page.tsx", message)
        self.assertIn("metadata", message)
        # It must not read as "your project is broken".
        self.assertNotIn("could not find a local file", message)

    def test_unroutable_url_still_names_the_framework(self):
        self._pkg(next="15.0.0")
        self._write("app/page.tsx")
        message = pathmap.explain_failure(self.dir, "https://x.com/nope/deep")
        self.assertIn("Next.js", message)

    def test_plain_site_gets_a_root_sitemap(self):
        self._write("index.html", "<html></html>")
        target, refusal = pathmap.sitemap_target(self.dir)
        self.assertIsNone(refusal)
        self.assertEqual(target, self.dir / "sitemap.xml")

    def test_framework_sitemap_goes_to_the_served_static_directory(self):
        # A sitemap.xml at a Next.js repo root is not served at /sitemap.xml,
        # so writing it there is a fix that changes nothing.
        self._pkg(next="15.0.0")
        self._write("app/page.tsx")
        self._write("public/favicon.ico")
        target, refusal = pathmap.sitemap_target(self.dir)
        self.assertIsNone(refusal)
        self.assertEqual(target, self.dir / "public" / "sitemap.xml")

    def test_sveltekit_uses_static_not_public(self):
        self._pkg(**{"@sveltejs/kit": "2.0.0"})
        self._write("src/routes/+page.svelte")
        self._write("static/favicon.png")
        target, _ = pathmap.sitemap_target(self.dir)
        self.assertEqual(target, self.dir / "static" / "sitemap.xml")

    def test_a_generated_sitemap_is_not_shadowed_by_a_static_one(self):
        self._pkg(next="15.0.0")
        self._write("app/page.tsx")
        self._write("public/favicon.ico")
        self._write("app/sitemap.ts")
        target, refusal = pathmap.sitemap_target(self.dir)
        self.assertIsNone(target)
        self.assertIn("app/sitemap.ts", refusal)

    def test_missing_static_directory_is_explained_not_guessed_at(self):
        self._pkg(next="15.0.0")
        self._write("app/page.tsx")
        target, refusal = pathmap.sitemap_target(self.dir)
        self.assertIsNone(target)
        self.assertIn("public/", refusal)

    def test_hugo_generates_its_own_sitemap(self):
        self._write("config.toml", "baseURL = 'https://x.com'")
        self._write("content/about.md", "# About")
        target, refusal = pathmap.sitemap_target(self.dir)
        self.assertIsNone(target)
        self.assertIn("every build", refusal)


class TestFixers(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "index.html").write_text(
            "<!doctype html>\n<html lang=\"en\">\n<head>\n  <title>T</title>\n</head>\n"
            "<body><h1>T</h1></body>\n</html>\n")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_sitemap_created_and_valid(self):
        plan = fixers.FixPlan()
        fixers.plan_sitemap(plan, self.dir, ["https://x.com/", "https://x.com/a"])
        plan.apply_all()
        content = (self.dir / "sitemap.xml").read_text()
        locs = [e.text for e in ET.fromstring(content).iter() if e.tag.endswith("loc")]
        self.assertEqual(sorted(locs), ["https://x.com/", "https://x.com/a"])

    def test_dry_run_writes_nothing(self):
        plan = fixers.FixPlan()
        fixers.plan_sitemap(plan, self.dir, ["https://x.com/"])
        self.assertFalse((self.dir / "sitemap.xml").exists())

    def test_multiple_fixes_to_one_file_compose(self):
        # Regression: each fix used to snapshot the file from disk, so the last
        # write silently discarded every earlier one.
        plan = fixers.FixPlan()
        fixers.plan_canonical(plan, self.dir, "https://x.com/", "https://x.com/")
        fixers.plan_jsonld(plan, self.dir, "https://x.com/", "organization",
                           known={"name": "N", "url": "https://x.com/"})
        fixers.plan_jsonld(plan, self.dir, "https://x.com/", "article",
                           known={"headline": "H"})
        plan.apply_all()
        content = (self.dir / "index.html").read_text()
        self.assertEqual(content.count('rel="canonical"'), 1)
        self.assertEqual(content.count("application/ld+json"), 2)

    def test_existing_canonical_is_never_overwritten(self):
        (self.dir / "index.html").write_text(
            '<html><head><link rel="canonical" href="https://other.com/x"></head></html>')
        plan = fixers.FixPlan()
        fixers.plan_canonical(plan, self.dir, "https://x.com/", "https://x.com/")
        self.assertEqual(plan.items, [])
        self.assertTrue(plan.refusals)
        self.assertIn("not overwriting", plan.refusals[0]["reason"])

    def test_no_head_tag_is_refused(self):
        (self.dir / "index.html").write_text("<html><body>no head</body></html>")
        plan = fixers.FixPlan()
        fixers.plan_canonical(plan, self.dir, "https://x.com/", "https://x.com/")
        self.assertEqual(plan.items, [])
        self.assertIn("no closing head", plan.refusals[0]["reason"])

    def test_nested_values_are_never_invented(self):
        # Regression: generic key matching used to fill an Article's author name
        # from the page title and the publisher logo from the page URL.
        plan = fixers.FixPlan()
        fixers.plan_jsonld(plan, self.dir, "https://x.com/", "article",
                           known={"headline": "Page Title", "name": "Page Title",
                                  "url": "https://x.com/"})
        plan.apply_all()
        content = (self.dir / "index.html").read_text()
        block = content.split("application/ld+json\">")[1].split("</script>")[0]
        data = json.loads(block)
        self.assertEqual(data["headline"], "Page Title")
        self.assertTrue(data["author"]["name"].startswith("TODO"))
        self.assertTrue(data["publisher"]["logo"]["url"].startswith("TODO"))
        self.assertIn("author.name", plan.items[0].placeholders)

    def test_generated_sitemap_is_wellformed_before_writing(self):
        plan = fixers.FixPlan()
        item = fixers.plan_sitemap(plan, self.dir, ["https://x.com/"])
        ET.fromstring(item.new_content)  # raises if malformed

    def test_diff_is_rendered_for_review(self):
        plan = fixers.FixPlan()
        item = fixers.plan_canonical(plan, self.dir, "https://x.com/", "https://x.com/")
        self.assertIn('+  <link rel="canonical"', item.render_diff())


class TestQuality(unittest.TestCase):
    def test_placeholder_text_detected(self):
        doc = htmldoc.parse("<html><body><p>TODO: write this section</p></body></html>")
        self.assertTrue(quality.find_placeholders(doc))

    def test_clean_copy_has_no_placeholders(self):
        self.assertEqual(quality.find_placeholders(htmldoc.parse(PAGE_FULL)), [])

    def test_title_and_meta_lengths(self):
        doc = htmldoc.parse(PAGE_FULL)
        _, title_issue = quality.check_title(doc)
        _, meta_issue = quality.check_meta_description(doc)
        self.assertEqual(title_issue, "")
        self.assertEqual(meta_issue, "")

        long_title = htmldoc.parse(f"<html><head><title>{'x' * 90}</title></head></html>")
        self.assertIn("truncated", quality.check_title(long_title)[1])

    def test_vague_anchors_in_both_languages(self):
        doc = htmldoc.parse('<html><body><a href="/a">click here</a>'
                            '<a href="/b">לחץ כאן</a>'
                            '<a href="/c">Read the installation guide</a></body></html>')
        found = quality.find_vague_anchors(doc)
        self.assertEqual(len(found), 2)

    def test_image_attributes(self):
        doc = htmldoc.parse('<html><body>'
                            '<img src="/hero.jpg" loading="lazy">'
                            '<img src="/ok.webp" width="10" height="10">'
                            '</body></html>')
        missing, lazy_early, legacy = quality.check_images(doc)
        self.assertIn("/hero.jpg", missing)
        self.assertIn("/hero.jpg", lazy_early)
        self.assertIn("/hero.jpg", legacy)


class TestRtl(unittest.TestCase):
    def test_ltr_page_is_not_assessed(self):
        html = "<html lang='en'><body><p>English only</p></body></html>"
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertFalse(result.applicable)

    def test_hebrew_without_dir_is_flagged(self):
        html = '<html lang="he"><body><p>שלום עולם</p></body></html>'
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertTrue(result.applicable)
        self.assertTrue(result.dir_missing)

    def test_correct_rtl_page_is_clean(self):
        html = '<html lang="he" dir="rtl"><body><p>שלום עולם וברוכים הבאים</p></body></html>'
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertFalse(result.dir_missing)
        self.assertFalse(result.dir_mismatch)
        self.assertEqual(result.bidi_risk_samples, [])

    def test_bidi_risk_detected(self):
        html = '<html lang="he" dir="rtl"><body><p>מחקר של Stanford University משנת 2024</p></body></html>'
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertTrue(result.bidi_risk_samples)

    def test_bdi_isolation_clears_the_risk(self):
        html = ('<html lang="he" dir="rtl"><body><p>מחקר של '
                '<bdi>Stanford University</bdi> משנת 2024</p></body></html>')
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertEqual(result.bidi_risk_samples, [])

    def test_dir_mismatch_detected(self):
        html = '<html lang="he" dir="ltr"><body><p>שלום</p></body></html>'
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertTrue(result.dir_mismatch)

    def test_language_picker_does_not_make_an_english_page_rtl(self):
        # Regression, found auditing pypi.org: a footer link labelled "עברית"
        # made an entirely English page trip the RTL checks.
        body = "<p>%s</p>" % (" ".join(["Deployed from the main branch today"] * 40))
        html = ('<html lang="en" dir="ltr"><body>' + body +
                '<ul><li><a href="/he">עברית</a></li>'
                '<li><a href="/en">English</a></li></ul>'
                '<p>Switch to desktop version</p></body></html>')
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertFalse(result.applicable)
        self.assertEqual(result.bidi_risk_samples, [])

    def test_bidi_scan_respects_element_boundaries(self):
        # Regression: the scanner split the flattened page text on ". ", so a
        # Hebrew label in one element and English text in the next were read as
        # one mixed-script sentence and reported as a hazard neither one is.
        html = ('<html lang="he" dir="rtl"><body>'
                '<p>שלום עולם וברוכים הבאים לאתר שלנו היום</p>'
                '<p>Switch to desktop version</p>'
                '</body></html>')
        result = quality.analyze_rtl(htmldoc.parse(html), html)
        self.assertTrue(result.applicable)
        self.assertEqual(result.bidi_risk_samples, [])


class TestAccessibility(unittest.TestCase):
    def test_missing_alt_detected_but_decorative_accepted(self):
        doc = htmldoc.parse('<html><body><img src="/a.png"><img src="/b.png" alt="">'
                            '<img src="/c.png" alt="real"></body></html>')
        result = accessibility.check_images(doc)
        self.assertEqual(result.missing, ["/a.png"])
        self.assertEqual(result.decorative, 1)
        self.assertEqual(result.with_alt, 1)

    def test_role_presentation_counts_as_decorative(self):
        doc = htmldoc.parse('<html><body><img src="/a.png" role="presentation"></body></html>')
        self.assertTrue(accessibility.check_images(doc).ok)

    def test_skipped_heading_levels_detected(self):
        doc = htmldoc.parse("<html><body><h1>a</h1><h4>b</h4></body></html>")
        result = accessibility.check_headings(doc)
        self.assertTrue(result.skipped_levels)

    def test_mixed_content_detected_on_https_only(self):
        doc = htmldoc.parse('<html><body><img src="http://x.com/a.png"></body></html>')
        self.assertTrue(accessibility.check_mixed_content(doc, "https://x.com/"))
        self.assertEqual(accessibility.check_mixed_content(doc, "http://x.com/"), [])


class TestAeo(unittest.TestCase):
    def test_question_headings_detected(self):
        doc = htmldoc.parse("<html><body><h2>What is this?</h2><h2>Pricing</h2></body></html>")
        shape = aeo.analyze_answer_shape(doc)
        self.assertEqual(len(shape.question_headings), 1)
        self.assertEqual(shape.total_headings, 2)

    def test_h1_is_not_counted_as_a_subheading(self):
        doc = htmldoc.parse("<html><body><h1>How to cook?</h1><h2>Steps</h2></body></html>")
        self.assertEqual(aeo.analyze_answer_shape(doc).total_headings, 1)

    def test_a_wh_word_alone_is_not_a_question(self):
        # Regression, found auditing eclipse.org: "Where our community connects"
        # is a declarative label, and counting it inflated the AEO score with a
        # heading no user question could match.
        for heading in ("Where our community connects", "What we build",
                        "Who we are", "How it works for teams and their data"):
            self.assertFalse(aeo.is_question_shaped(heading), heading)

    def test_real_questions_are_still_recognized(self):
        for heading in ("What is Docker?", "How do I install Node",
                        "Is it free", "How to install Python",
                        "Why does this matter", "Who should use this"):
            self.assertTrue(aeo.is_question_shaped(heading), heading)


class TestReportRendering(unittest.TestCase):
    def test_wrap_preserves_word_boundaries(self):
        # Regression: starting a new line dropped the separating space, so
        # wrapped text read "Inspectionfor".
        text = "requires Google Search Console access to check the URL Inspection report properly"
        lines = report._wrap(text, 40, "    ")
        self.assertEqual(" ".join(l.strip() for l in lines), text)

    def test_punch_list_orders_by_severity_then_status(self):
        result = AuditResult(url="x")
        result.add(Finding("C5", "crumbs", WARN))          # low
        result.add(Finding("A1", "status", FAIL))          # critical
        result.add(Finding("A8", "dom", WARN))             # critical, warn
        result.add(Finding("B8", "title", FAIL))           # high
        order = [f.id for f in result.punch_list()]
        self.assertEqual(order, ["A1", "A8", "B8", "C5"])

    def test_passing_findings_are_not_in_the_punch_list(self):
        result = AuditResult(url="x")
        result.add(Finding("A1", "status", PASS))
        result.add(Finding("A4", "canonical", NA))
        self.assertEqual(result.punch_list(), [])

    def test_severity_defaults_by_item(self):
        self.assertEqual(Finding("A1", "t", FAIL).severity, CRITICAL)
        self.assertEqual(Finding("B9", "t", WARN).severity, LOW)

    def test_gate_detection(self):
        result = AuditResult(url="x")
        result.add(Finding("C1", "sd", FAIL))
        self.assertFalse(result.gate_failed())
        result.add(Finding("A1", "status", FAIL))
        self.assertTrue(result.gate_failed())

    def test_json_round_trips(self):
        result = AuditResult(url="x")
        result.add(Finding("A1", "status", PASS, detail="ok"))
        parsed = json.loads(report.render_json(result))
        self.assertEqual(parsed["findings"][0]["section"], "A")
        self.assertTrue(parsed["findings"][0]["gate"])


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class TestCrawlerAgainstLocalServer(unittest.TestCase):
    """End-to-end over real HTTP, on loopback."""

    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp())
        (cls.dir / "index.html").write_text(
            '<html lang="en"><head><title>Same Title</title>'
            '<meta name="description" content="Shared description"></head>'
            '<body><main><h1>Home</h1>'
            '<a href="/a.html">Page A</a><a href="/gone.html">Missing</a>'
            '</main></body></html>')
        (cls.dir / "a.html").write_text(
            '<html lang="en"><head><title>Same Title</title>'
            '<meta name="description" content="Shared description"></head>'
            '<body><main><h1>A</h1></main></body></html>')

        handler = lambda *a, **k: _QuietHandler(*a, directory=str(cls.dir), **k)
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_crawl_finds_pages_and_broken_links(self):
        result = crawler.crawl(self.base, max_pages=5, max_depth=2, delay=0)
        self.assertGreaterEqual(result.page_count, 2)
        self.assertTrue(any(b.status == 404 for b in result.broken))

    def test_broken_link_attributes_its_source(self):
        result = crawler.crawl(self.base, max_pages=5, max_depth=2, delay=0)
        broken = [b for b in result.broken if b.status == 404][0]
        # The homepage is what linked to the missing page.
        self.assertEqual(normalize_url(broken.source), normalize_url(self.base))
        self.assertIn("gone.html", broken.target)

    def test_duplicate_titles_and_descriptions_detected(self):
        result = crawler.crawl(self.base, max_pages=5, max_depth=2, delay=0)
        self.assertIn("Same Title", result.duplicate_titles)
        self.assertIn("Shared description", result.duplicate_meta)

    def test_crawl_respects_page_limit(self):
        result = crawler.crawl(self.base, max_pages=1, max_depth=2, delay=0)
        self.assertEqual(result.page_count, 1)

    def test_inbound_link_detection(self):
        result = crawler.crawl(self.base, max_pages=5, max_depth=2, delay=0)
        self.assertTrue(result.inbound_links_to(self.base + "a.html"))


class TestDevServerUrlsNeverReachSource(unittest.TestCase):
    """Auditing a dev server is the normal way to use --fix while building.
    The URLs it returns start with http://localhost, and writing one of those
    into a canonical tag or a sitemap ships a developer's machine to
    production."""

    def _ctx(self, url, base_url=None):
        return types.SimpleNamespace(
            args=types.SimpleNamespace(base_url=base_url),
            page=types.SimpleNamespace(final_url=url))

    def test_localhost_without_a_base_url_blocks_writing(self):
        self.assertFalse(audit._may_write_urls(
            self._ctx("http://127.0.0.1:8099/index.html")))

    def test_a_base_url_unblocks_it(self):
        self.assertTrue(audit._may_write_urls(
            self._ctx("http://127.0.0.1:8099/index.html",
                      base_url="https://kettleworks.example")))

    def test_a_real_url_needs_no_base_url(self):
        self.assertTrue(audit._may_write_urls(self._ctx("https://example.com/x")))

    def test_public_url_swaps_the_origin_and_keeps_the_path(self):
        ctx = self._ctx("http://127.0.0.1:8099/breads/challah?v=2",
                        base_url="https://kettleworks.example/")
        self.assertEqual(audit._public_url(ctx, ctx.page.final_url),
                         "https://kettleworks.example/breads/challah?v=2")

    def test_public_url_is_a_no_op_without_a_base_url(self):
        ctx = self._ctx("https://example.com/x")
        self.assertEqual(audit._public_url(ctx, "https://example.com/x"),
                         "https://example.com/x")

    def test_the_block_reason_names_the_flag_that_lifts_it(self):
        reason = audit._local_url_block_reason(
            self._ctx("http://127.0.0.1:8099/index.html"))
        self.assertIn("--base-url", reason)


class TestSitemapDoesNotDuplicateAcrossOrigins(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>http://127.0.0.1:8099/kettles.html</loc></url>'
            '<url><loc>http://127.0.0.1:8099/care.html</loc></url>'
            '</urlset>')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_path_already_listed_is_not_added_under_another_origin(self):
        # Regression: with --base-url every crawled URL arrives rewritten, so a
        # plain membership test called the whole site missing and listed every
        # page twice — worse than the gap it set out to close.
        plan = fixers.FixPlan()
        fixers.plan_sitemap(plan, self.dir, [
            "https://kettleworks.example/kettles.html",
            "https://kettleworks.example/care.html",
            "https://kettleworks.example/index.html",
        ])
        plan.apply_all()
        content = (self.dir / "sitemap.xml").read_text()
        self.assertEqual(content.count("kettles.html"), 1)
        self.assertEqual(content.count("care.html"), 1)
        self.assertIn("https://kettleworks.example/index.html", content)

    def test_nothing_missing_means_no_write(self):
        plan = fixers.FixPlan()
        item = fixers.plan_sitemap(plan, self.dir, [
            "https://kettleworks.example/kettles.html",
            "https://kettleworks.example/care.html",
        ])
        self.assertIsNone(item)


class TestArticleDetection(unittest.TestCase):
    """C3 used to warn "no Article markup" on every page and offer to inject
    it — including on pages whose own finding text said Article did not apply.
    Marking a shop homepage as an Article is the spam problem the skill warns
    about, reached by being helpful."""

    def _ctx(self, url, html):
        doc = htmldoc.parse(html)
        return types.SimpleNamespace(
            doc=doc, page=types.SimpleNamespace(final_url=url, body=html))

    def test_a_shop_homepage_is_not_an_article(self):
        html = ('<html lang="en"><head><title>Kettleworks</title></head><body>'
                '<h1>Kettleworks</h1><h4>Our story</h4>'
                '<p>We have been making kettles since 1987.</p></body></html>')
        self.assertFalse(audit._looks_like_an_article(
            self._ctx("https://example.com/", html)))

    def test_a_blog_path_is_enough(self):
        html = '<html lang="en"><body><h1>Post</h1></body></html>'
        self.assertTrue(audit._looks_like_an_article(
            self._ctx("https://example.com/blog/descaling", html)))

    def test_a_dated_path_is_enough(self):
        html = '<html lang="en"><body><h1>Post</h1></body></html>'
        self.assertTrue(audit._looks_like_an_article(
            self._ctx("https://example.com/2026/06/descaling", html)))

    def test_long_dated_prose_under_subheadings_counts(self):
        body = " ".join(["Limescale is calcium carbonate left behind."] * 90)
        html = ('<html lang="en"><head><meta name="author" content="R. O."></head>'
                f'<body><h1>Descaling</h1><time datetime="2026-06-02">June</time>'
                f'<h2>Why it forms</h2><p>{body}</p><h2>The method</h2>'
                f'<p>{body}</p></body></html>')
        self.assertTrue(audit._looks_like_an_article(
            self._ctx("https://example.com/help/descaling", html)))

    def test_long_prose_without_a_date_or_byline_does_not_count(self):
        body = " ".join(["Copper conducts heat quickly and evenly."] * 90)
        html = ('<html lang="en"><body><h1>Kettles</h1>'
                f'<h2>Copper</h2><p>{body}</p><h2>Cast iron</h2><p>{body}</p>'
                '</body></html>')
        self.assertFalse(audit._looks_like_an_article(
            self._ctx("https://example.com/kettles", html)))


class TestLocalHostDetection(unittest.TestCase):
    def test_loopback_and_dev_tlds_are_local(self):
        for url in ("http://localhost:3000/", "http://127.0.0.1:8099/index.html",
                    "http://app.localhost/", "http://myapp.test/",
                    "http://printer.local/"):
            self.assertTrue(audit._is_local_host(url), url)

    def test_real_hosts_are_not_local(self):
        for url in ("https://example.com/", "http://localhost.example.com/",
                    "https://nodejs.org/en/learn"):
            self.assertFalse(audit._is_local_host(url), url)


class TestForeignCanonicalJudgement(unittest.TestCase):
    """A canonical pointing elsewhere is consolidation as often as it is a bug.
    The tool resolves the target before deciding, over real HTTP on loopback."""

    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp())
        (cls.dir / "canonical-target.html").write_text(
            '<html lang="en"><head><title>T</title></head>'
            '<body><main><h1>Target</h1></main></body></html>')
        handler = lambda *a, **k: _QuietHandler(*a, directory=str(cls.dir), **k)
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def _judge(self, target, sitemap_urls):
        page_url = self.base + "en/page.html"
        doc = htmldoc.parse(
            f'<html lang="en"><head><link rel="canonical" href="{target}">'
            f'</head><body><h1>x</h1></body></html>')
        can = canonical.check(doc, page_url)
        ctx = types.SimpleNamespace(sitemap=None)
        if sitemap_urls is not None:
            ctx.sitemap = types.SimpleNamespace(
                exists=True, urls={normalize_url(u) for u in sitemap_urls})
        return audit._judge_foreign_canonical(ctx, can)

    def test_live_target_in_the_sitemap_is_not_reported_as_a_problem(self):
        # The nodejs.org pattern: /en/x canonicalizing to /x, with /x in the
        # sitemap. Flagging that wastes the reader's time.
        target = self.base + "canonical-target.html"
        finding = self._judge(target, [target])
        self.assertEqual(finding.status, PASS)
        self.assertIn("deliberate", finding.detail)

    def test_dead_target_is_a_hard_failure(self):
        finding = self._judge(self.base + "does-not-exist.html", [])
        self.assertEqual(finding.status, FAIL)
        self.assertIn("404", finding.detail)

    def test_live_target_missing_from_the_sitemap_warns(self):
        target = self.base + "canonical-target.html"
        finding = self._judge(target, [self.base + "something-else.html"])
        self.assertEqual(finding.status, WARN)
        self.assertIn("not in the sitemap", finding.detail)

    def test_without_a_sitemap_it_stays_a_human_decision(self):
        target = self.base + "canonical-target.html"
        finding = self._judge(target, None)
        self.assertEqual(finding.status, HUMAN_JUDGMENT)


if __name__ == "__main__":
    unittest.main(verbosity=2)

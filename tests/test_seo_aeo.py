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
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / ".claude" / "skills" / "seo-aeo" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from seo_aeo import (  # noqa: E402
    accessibility, aeo, canonical, crawler, fixers, htmldoc,
    pathmap, quality, report, sitemap, structured_data,
)
from seo_aeo.fetch import _decode_body, normalize_url, same_host  # noqa: E402
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

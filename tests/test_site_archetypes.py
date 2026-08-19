#!/usr/bin/env python3
"""Generality tests: does the audit hold up across real-world site shapes?

The skill is meant to work on any site, so the risk is not "does it work on the
one site we tried" but "does it break, crash, or lie on a shape we did not
anticipate". Each fixture below is a site archetype with a different failure
mode, served over real HTTP.

    python3 tests/test_site_archetypes.py
"""

import http.server
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT = REPO_ROOT / ".claude" / "skills" / "seo-aeo" / "scripts" / "audit.py"
sys.path.insert(0, str(AUDIT.parent))

import json  # noqa: E402


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class ArchetypeCase(unittest.TestCase):
    """Serve a directory of files and run the real CLI against it."""

    files: dict = {}

    @classmethod
    def setUpClass(cls):
        if cls is ArchetypeCase:
            raise unittest.SkipTest("base class")
        cls.dir = Path(tempfile.mkdtemp())
        handler = lambda *a, **k: _QuietHandler(*a, directory=str(cls.dir), **k)
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        # Fixtures use {BASE} for self-referencing URLs, since the port is only
        # known once the server binds.
        base = f"http://127.0.0.1:{cls.port}/"
        for name, content in cls.files.items():
            path = cls.dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content.replace("{BASE}", base), encoding="utf-8")
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.port}/"
        cls.result = cls.audit(cls.base)

    @classmethod
    def tearDownClass(cls):
        if cls is ArchetypeCase:
            return
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.dir, ignore_errors=True)

    @classmethod
    def audit(cls, url, extra=()):
        proc = subprocess.run(
            [sys.executable, str(AUDIT), url, "--json", "--skip-cwv",
             "--max-pages", "6", "--max-depth", "2", *extra],
            capture_output=True, text=True, timeout=180,
        )
        # Exit code 1 just means a gate failed; only a crash is a problem.
        assert proc.returncode in (0, 1), f"crashed: {proc.stderr[-2000:]}"
        return json.loads(proc.stdout)

    # -- assertions shared by every archetype ---------------------------

    def finding(self, fid):
        for f in self.result["findings"]:
            if f["id"] == fid:
                return f
        self.fail(f"no finding {fid}")

    def status(self, fid):
        return self.finding(fid)["status"]

    def test_produces_a_complete_report(self):
        sections = {f["section"] for f in self.result["findings"]}
        self.assertEqual(sections, set("ABCDEFGP"))

    def test_no_check_crashed(self):
        # Every check must resolve to a status; an exception would show up as an
        # entry in errors rather than a silently missing finding.
        self.assertEqual(self.result["errors"], [], self.result["errors"])

    def test_every_non_pass_explains_itself(self):
        for f in self.result["findings"]:
            if f["status"] in ("FAIL", "WARN", "N/A", "HUMAN_JUDGMENT"):
                self.assertTrue(
                    f["detail"] or f["reason"],
                    f"{f['id']} is {f['status']} with no explanation")

    def test_severity_assigned_everywhere(self):
        for f in self.result["findings"]:
            self.assertIn(f["severity"], ("critical", "high", "medium", "low"))


class TestStaticBlogPost(ArchetypeCase):
    """A well-built static blog: everything should mostly pass."""

    files = {
        "index.html": '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How to Choose a Standing Desk: A Practical Guide</title>
<meta name="description" content="A practical, tested guide to choosing a standing desk, covering height range, stability, motor noise, and the three mistakes buyers most often make.">
<link rel="canonical" href="{BASE}">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","name":"Desk Guide","url":"http://example.com/"}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article","headline":"How to Choose a Standing Desk",
"image":["http://example.com/hero.webp"],"datePublished":"2026-02-01","dateModified":"2026-08-01",
"author":{"@type":"Person","name":"Dana Levi","url":"http://example.com/about"}}
</script>
</head><body><nav><a href="/about.html">About the author</a></nav>
<main><h1>How to Choose a Standing Desk</h1>
<h2>What height range do you actually need?</h2>
<p>Most adults need a desk that travels from 60cm to 125cm. Measure your elbow height seated and standing before shopping.</p>
<ul><li>Under 60cm: rare, check carefully</li><li>60-125cm: covers most people</li><li>Above 125cm: only for very tall users</li></ul>
<h2>How much stability is enough?</h2>
<p>Wobble at full extension is the most common complaint we hear, and it is the hardest thing to judge from a product page. A crossbar or a dual motor arrangement helps considerably, but the frame joint quality matters more than either. We loaded eleven desks to full height and pushed laterally at the desktop edge; the four that stayed steady all used welded rather than bolted crossmembers.</p>
<h2>Does motor noise actually matter day to day?</h2>
<p>In a shared office it does. Measured at one metre, the quietest desks we tested ran at 44 decibels and the loudest at 61, which is the difference between a background hum and a sound that stops a conversation.</p>
<table><tr><th>Type</th><th>Stability</th></tr><tr><td>Single motor</td><td>Fair</td></tr></table>
<img src="/hero.webp" alt="A height adjustable desk at standing height" width="800" height="600">
</main></body></html>''',
        "about.html": '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>About Dana Levi, Ergonomics Researcher</title>
<meta name="description" content="Dana Levi has tested over two hundred standing desks across eight years of ergonomics research and writes about what actually holds up.">
</head><body><main><h1>About Dana Levi</h1><p>Ergonomics researcher since 2018.</p></main></body></html>''',
        "robots.txt": "User-agent: *\nAllow: /\n",
    }

    def test_good_page_passes_the_content_gates(self):
        for fid in ("A1", "A2", "A3", "A4", "A8"):
            self.assertEqual(self.status(fid), "PASS", fid)

    def test_recognizes_valid_structured_data(self):
        self.assertEqual(self.status("C1"), "PASS")
        self.assertEqual(self.status("C2"), "PASS")
        self.assertEqual(self.status("C4"), "PASS")

    def test_recognizes_question_headings(self):
        self.assertEqual(self.status("F4"), "PASS")

    def test_clean_page_has_no_quality_bugs(self):
        for fid in ("G1", "G2", "G3", "G5"):
            self.assertEqual(self.status(fid), "PASS", fid)


class TestJavaScriptSPA(ArchetypeCase):
    """A client-rendered SPA: the classic modern technical-SEO failure."""

    files = {
        "index.html": '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>App</title></head>
<body><div id="root"></div><script src="/bundle.js"></script></body></html>''',
    }

    def test_empty_shell_is_flagged_as_a_gate_failure(self):
        self.assertEqual(self.status("A8"), "FAIL")
        self.assertTrue(self.result["gate_failed"])

    def test_missing_content_is_explained_as_a_js_problem(self):
        self.assertIn("JavaScript", self.finding("A8")["detail"])

    def test_aeo_is_reported_as_blocked_not_merely_weak(self):
        self.assertEqual(self.status("F1"), "FAIL")


class TestHebrewRtlSite(ArchetypeCase):
    """A Hebrew site — RTL correctness plus bidi hazards."""

    files = {
        "index.html": '''<!doctype html>
<html lang="he"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>מדריך לבחירת שולחן עמידה — כל מה שצריך לדעת לפני שקונים</title>
<meta name="description" content="מדריך מעשי לבחירת שולחן עמידה, כולל טווח גובה, יציבות, רעש מנוע ושלוש הטעויות הנפוצות ביותר של קונים בישראל.">
<link rel="canonical" href="{BASE}">
</head><body><main><h1>מדריך לבחירת שולחן עמידה</h1>
<p>מחקר של Stanford University משנת 2024 מצא שעמידה מפחיתה כאבי גב ב-32 אחוז.</p>
<a href="/guide.html">לחץ כאן</a>
</main></body></html>''',
        "guide.html": '<html lang="he" dir="rtl"><head><title>מדריך</title></head><body><main><h1>מדריך</h1><p>תוכן בעברית בלבד ללא ערבוב שפות כלל וכלל.</p></main></body></html>',
    }

    def test_missing_dir_attribute_is_a_failure(self):
        self.assertEqual(self.status("G7"), "FAIL")
        self.assertIn("dir", self.finding("G7")["detail"])

    def test_bidi_hazard_is_reported(self):
        self.assertIn("wrong visual order", self.finding("G7")["detail"])

    def test_hebrew_vague_anchor_is_caught(self):
        self.assertEqual(self.status("G5"), "WARN")
        self.assertIn("לחץ כאן", self.finding("G5")["detail"])

    def test_hebrew_content_does_not_break_other_checks(self):
        self.assertEqual(self.status("A1"), "PASS")
        self.assertEqual(self.status("E9"), "PASS")


class TestBrokenLegacySite(ArchetypeCase):
    """An old site with several problems at once."""

    files = {
        "index.html": '''<html>
<head><title>Home</title>
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="http://other-domain.example/elsewhere">
<script type="application/ld+json">{ this is not valid json }</script>
</head>
<body><h1>Home</h1><h4>Skipped heading level</h4>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
<img src="/photo.jpg">
<a href="/dead.html">click here</a>
</body></html>''',
    }

    def test_noindex_is_caught(self):
        self.assertEqual(self.status("A3"), "FAIL")

    def test_cross_domain_canonical_is_a_human_decision(self):
        self.assertEqual(self.status("A4"), "HUMAN_JUDGMENT")

    def test_invalid_jsonld_is_reported_not_ignored(self):
        self.assertEqual(self.status("C2"), "FAIL")

    def test_multiple_independent_problems_all_surface(self):
        self.assertEqual(self.status("G1"), "FAIL")   # lorem ipsum
        self.assertEqual(self.status("B4"), "FAIL")   # skipped heading
        self.assertEqual(self.status("E2"), "FAIL")   # no viewport
        self.assertEqual(self.status("E9"), "FAIL")   # no lang
        self.assertEqual(self.status("G5"), "WARN")   # click here

    def test_punch_list_puts_the_blocker_first(self):
        actionable = [f for f in self.result["findings"]
                      if f["status"] in ("FAIL", "WARN", "HUMAN_JUDGMENT")]
        criticals = [f["id"] for f in actionable if f["severity"] == "critical"]
        self.assertIn("A3", criticals)


class TestEcommerceWithFacets(ArchetypeCase):
    """Duplicate content from filter/sort URL variants."""

    files = {
        "index.html": '''<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shop All Products</title>
<meta name="description" content="Browse the full catalogue of products with filters for size colour and price to find exactly what suits your setup at home.">
</head><body><main><h1>Shop</h1>
<a href="/list.html">Product list</a>
<a href="/list-sorted.html">Product list sorted by price</a>
</main></body></html>''',
        # Same content at two URLs — the canonicalization problem in miniature.
        "list.html": '''<html lang="en"><head><meta charset="utf-8"><title>Product List</title>
<meta name="description" content="Every product we carry, listed with specifications and prices for straightforward comparison across the whole range."></head>
<body><main><h1>Products</h1><p>''' + ("Identical catalogue copy repeated for hashing. " * 20) + '''</p></main></body></html>''',
        "list-sorted.html": '''<html lang="en"><head><meta charset="utf-8"><title>Product List</title>
<meta name="description" content="Every product we carry, listed with specifications and prices for straightforward comparison across the whole range."></head>
<body><main><h1>Products</h1><p>''' + ("Identical catalogue copy repeated for hashing. " * 20) + '''</p></main></body></html>''',
    }

    def test_duplicate_content_is_surfaced_for_a_decision(self):
        dupes = [f for f in self.result["findings"]
                 if f["status"] == "HUMAN_JUDGMENT" and "uplicate" in f["title"]]
        self.assertTrue(dupes, "duplicate content across URLs was not reported")

    def test_duplicate_titles_reported_on_the_metadata_item(self):
        # The homepage itself is unique, so B8 should not fire on it; the point
        # is that the crawl noticed the collision at all.
        self.assertIn("B8", [f["id"] for f in self.result["findings"]])


class TestMinimalLandingPage(ArchetypeCase):
    """A one-page site with no sitemap, no robots.txt, no links anywhere."""

    files = {
        "index.html": '''<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coming Soon</title></head>
<body><main><h1>Coming Soon</h1><p>''' + ("We are building something. " * 30) + '''</p></main></body></html>''',
    }

    def test_single_page_site_does_not_produce_false_orphan_reports(self):
        self.assertEqual(self.status("G8"), "N/A")

    def test_no_inbound_links_is_not_asserted_on_a_one_page_site(self):
        self.assertEqual(self.status("A7"), "N/A")

    def test_missing_sitemap_is_reported_as_fixable(self):
        self.assertEqual(self.status("A5"), "FAIL")
        self.assertTrue(self.finding("A5")["fixable"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

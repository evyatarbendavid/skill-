#!/usr/bin/env python3
"""Checks the skill package stays installable and internally consistent.

These are the failures that silently break distribution: a zip that drifted
from the source, frontmatter the loader rejects, a reference file the skill
points at that isn't there, or a claim the skill is supposed to correct.

    python3 tests/test_skill_package.py
"""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT
SKILL_MD = ROOT / "SKILL.md"
AGENTS = ROOT / "agents"

# Mirrors the loader's own limits.
NAME_RE = re.compile(r"^[a-z0-9-]+$")
MAX_DESCRIPTION = 1024
MAX_NAME = 64


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"{path} has no YAML frontmatter"
    out, key = {}, None
    for line in match.group(1).splitlines():
        if re.match(r"^\w[\w-]*:", line):
            key, _, value = line.partition(":")
            key = key.strip()
            out[key] = value.strip()
        elif key and line.strip():
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


class TestSkillManifest(unittest.TestCase):
    def setUp(self):
        self.fm = frontmatter(SKILL_MD)

    def test_required_fields_present(self):
        self.assertIn("name", self.fm)
        self.assertIn("description", self.fm)

    def test_name_is_valid(self):
        name = self.fm["name"]
        self.assertTrue(NAME_RE.fullmatch(name), f"{name!r} is not kebab-case")
        self.assertLessEqual(len(name), MAX_NAME)
        self.assertEqual(name, "seo-aeo")

    def test_description_within_limits(self):
        desc = self.fm["description"].strip("'\" >|")
        self.assertLessEqual(len(desc), MAX_DESCRIPTION,
                             f"description is {len(desc)} chars, max {MAX_DESCRIPTION}")
        # Angle brackets are rejected by the loader.
        self.assertNotIn("<", desc)
        self.assertNotIn(">", desc)

    def test_description_says_when_to_trigger(self):
        # A description that only says what the skill is will under-trigger.
        desc = self.fm["description"].lower()
        self.assertIn("use", desc, "description should say when to use the skill")
        for cue in ("seo", "aeo", "ranking"):
            self.assertIn(cue, desc, f"description should mention {cue!r}")

    def test_exactly_one_skill_md(self):
        # No exclusions: a second SKILL.md anywhere in the repo can be
        # loaded as a rival skill manifest, so there must not be one.
        found = [p for p in ROOT.rglob("SKILL.md") if ".git" not in p.parts]
        self.assertEqual(len(found), 1, f"expected one SKILL.md, found {found}")


class TestReferences(unittest.TestCase):
    def test_referenced_files_exist(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for rel in re.findall(r"`(references/[\w.-]+)`", text):
            self.assertTrue((SKILL_DIR / rel).is_file(),
                            f"SKILL.md points at {rel}, which does not exist")

    def test_no_dangling_internal_links(self):
        # Reference files must not point at files that were left behind.
        for ref in (ROOT / "references").glob("*.md"):
            for target in re.findall(r"\]\(\./([\w.-]+\.md)\)", ref.read_text(encoding="utf-8")):
                self.assertTrue((ref.parent / target).is_file(),
                                f"{ref.name} links to missing {target}")

    def test_no_references_to_removed_tooling(self):
        # The packaged skill ships no scripts; pointing at one would strand
        # a Desktop user with an instruction they cannot follow. Agents are
        # scanned too — a dead reference sat in seo-fixer.md's description
        # field for exactly as long as this test skipped that directory.
        for path in ([SKILL_MD]
                     + list((ROOT / "references").glob("*.md"))
                     + list(AGENTS.glob("*.md"))):
            text = path.read_text(encoding="utf-8")
            for stale in ("scripts/audit.py", "audit_site.py", "live-verification-map.md"):
                self.assertNotIn(stale, text, f"{path.name} references {stale}")


class TestFactualGuardrails(unittest.TestCase):
    """The skill exists partly to correct specific misinformation. If those
    corrections ever get edited out, the skill starts spreading it instead."""

    def setUp(self):
        self.text = " ".join(p.read_text(encoding="utf-8")
                             for p in [SKILL_MD] + list((ROOT / "references").glob("*.md")))

    def test_states_correct_cwv_thresholds(self):
        for value in ("2.5", "200", "0.1"):
            self.assertIn(value, self.text)

    def test_debunks_the_fake_thresholds(self):
        self.assertIn("0.08", self.text, "should name the fake CLS number to reject it")
        self.assertIn("2.0s", self.text, "should name the fake LCP number to reject it")

    def test_faqpage_and_howto_marked_dead(self):
        self.assertRegex(self.text, r"FAQPage.{0,400}(removed|deprecat|restricted)")
        self.assertRegex(self.text, r"HowTo.{0,400}(deprecat|2023)")

    def test_howto_dated_2023_not_2026(self):
        # The source document dated HowTo's deprecation to 2026; it was 2023.
        # Check every mention rather than the first — the first is whichever
        # section happens to come earliest in the file, which moves as the
        # skill is edited, and a test that moves with it tests nothing.
        self.assertRegex(self.text, r"HowTo.{0,300}?2023",
                         "HowTo's 2023 deprecation date must be stated somewhere")
        self.assertNotRegex(self.text, r"HowTo[^.]{0,120}deprecated[^.]{0,40}2026",
                            "HowTo must never be dated to 2026")

    def test_verification_dates_agree(self):
        # Two files carry a "verified on" date driving the same 90-day rule.
        # Disagreeing by a day is harmless; disagreeing at all means one was
        # updated and the other forgotten, which is how they drift by months.
        dates = set()
        for path in (SKILL_MD, ROOT / "references" / "sources.md"):
            found = re.findall(r"[Vv]erified:? (\d{4}-\d{2}-\d{2})",
                               path.read_text(encoding="utf-8"))
            dates.update(found)
        self.assertEqual(len(dates), 1,
                         f"verification dates disagree: {sorted(dates)}")

    def test_no_file_frames_a_ranking_position_as_a_deliverable(self):
        # SKILL.md refuses to promise positions. A reference file listing
        # "average position <= 10" as a proof artifact to produce quietly
        # promises exactly that, and the reference is what gets loaded for
        # an audit.
        for path in (ROOT / "references" / "audit-checklist.md",
                     ROOT / "references" / "sources.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(
                text, r"(Proof|deliverable|goal)[^.]{0,80}average position",
                f"{path.name} frames a ranking position as something to deliver")

    def test_refuses_to_promise_rankings(self):
        self.assertRegex(self.text, r"does not guarantee|doesn't guarantee")
        self.assertRegex(self.text, r"[Nn]othing forces an AI engine to cite|no guaranteed")

    def test_all_files_agree_top_10_no_longer_predicts_citation(self):
        # SKILL.md, sources.md and the auditor each state this independently.
        # The correction is worthless if one of the three still teaches the
        # old assumption — whichever file the reader happens to open wins.
        for path in (SKILL_MD,
                     ROOT / "references" / "sources.md",
                     AGENTS / "seo-page-auditor.md"):
            text = path.read_text(encoding="utf-8")
            self.assertRegex(
                text, r"(76%|entry ticket|not.{0,20}predictor)",
                f"{path.name} must carry the corrected top-10 framing")

    def test_does_not_claim_ai_answers_are_the_default_for_most_queries(self):
        # This file carried that overclaim itself. Clickstream measurement puts
        # AI Overviews on a large minority of searches and AI Mode under 1% —
        # the reach is the part everyone inflates.
        # Presence-tested, not absence-tested: an absence test on prose matches
        # the correction itself ("not yet the default output for most queries")
        # and passes for the wrong reason. Assert the measured shares are here —
        # nobody can restate the overclaim while these two numbers stand.
        # Presence-tested, not absence-tested: an absence test on prose matches
        # the correction itself ("not yet the default output for most queries")
        # and passes for the wrong reason. Assert the measured shares are here —
        # nobody can restate the overclaim while these two numbers stand.
        #
        # Checked against SKILL.md specifically, not the whole corpus. SKILL.md
        # is the file that always gets read; a number surviving only in a
        # reference nobody opened does not keep the skill honest.
        for name, text in (("SKILL.md", SKILL_MD.read_text(encoding="utf-8")),
                           ("sources.md", (ROOT / "references" / "sources.md")
                            .read_text(encoding="utf-8"))):
            flat = " ".join(text.split())
            self.assertRegex(flat, r"AI Overviews[^.]{0,140}20%",
                             f"{name} should state the measured AI Overview reach")
            self.assertRegex(flat, r"AI Mode[^.]{0,300}(0\.34%|under 1%|less than 1%)",
                             f"{name} should state how small AI Mode's share is")
            self.assertIn("large minority", flat, name)

    def test_names_the_page_level_control_over_ai_answers(self):
        # robots.txt is the wrong tool for staying out of Google's AI answers,
        # and it is the only one most discussions mention.
        flat = " ".join(self.text.split())
        self.assertIn("max-snippet", flat)
        self.assertIn("data-nosnippet", flat)
        # The tradeoff is the part that decides whether to use it at all.
        self.assertRegex(flat, r"nosnippet[^|]{0,400}(ordinary|normal) (search )?snippet")

    def test_ai_visibility_reporting_carries_its_limits(self):
        flat = " ".join(self.text.split())
        self.assertRegex(flat, r"Search Generative AI performance report")
        for limit in ("no click data", "backfill", "UK"):
            self.assertIn(limit, flat, f"should state the {limit!r} limit")

    def test_soft_navigations_are_not_sold_as_a_ranking_input(self):
        # The API shipped; whether CrUX counts it is undetermined. Claiming the
        # second half follows from the first is the easy mistake here.
        flat = " ".join(self.text.split())
        self.assertIn("Soft Navigations API", flat)
        self.assertRegex(flat, r"(CrUX|undetermined|to be determined)[^.]{0,200}"
                               r"(undetermined|to be determined|not a given)")

    def test_llms_txt_not_sold_as_a_lever(self):
        # Check every mention, not just the first — the first is the
        # volatile-facts table, the claim itself lives further down.
        self.assertIn("llms.txt", self.text)
        self.assertRegex(self.text, r"llms\.txt.{0,900}?(not a citation lever|"
                                    r"no major provider has confirmed)")


class TestFieldNotesStayEvidence(unittest.TestCase):
    """Observations from a handful of sites are useful for deciding what to
    check first and worthless as statistics. The file has to keep saying which
    it is, or the next reader quotes '6 of 7 sites' as a fact about the web."""

    def setUp(self):
        self.text = (ROOT / "references" / "field-notes.md").read_text(encoding="utf-8")
        # Reflow, dropping blockquote markers: these assertions are about what
        # the file says, and a line break landing mid-phrase is not a change in
        # meaning.
        self.flat = " ".join(self.text.replace("\n>", "\n").split())

    def test_names_its_sample_size_and_date(self):
        self.assertRegex(self.text, r"\bseven\b|\b7\b")
        self.assertRegex(self.text, r"20\d\d-\d\d-\d\d")

    def test_says_what_the_sample_does_not_cover(self):
        for gap in ("Hebrew", "news", "product page"):
            self.assertIn(gap, self.text, f"sample limits should name {gap}")

    def test_warns_against_generalizing_the_frequencies(self):
        # Distinctive words rather than a prose shape — the caveat can be
        # rewritten freely, it just cannot disappear.
        self.assertIn("anecdote", self.flat)
        self.assertRegex(self.flat, r'never as "N% of the web does X\."')

    def test_frequencies_are_not_stated_in_the_skill_as_percentages_of_the_web(self):
        skill = SKILL_MD.read_text(encoding="utf-8")
        self.assertNotRegex(skill, r"\d+ ?(of|/) ?7\b",
                            "raw sample counts belong in field-notes, with the caveat")


class TestWorkedReport(unittest.TestCase):
    """The report template is the skill's actual output shape. If it drifts
    from what SKILL.md tells people to produce, the skill contradicts itself."""

    def setUp(self):
        self.text = (ROOT / "references" / "examples.md").read_text(encoding="utf-8")

    def test_report_ranks_findings_the_way_the_skill_says_to(self):
        for level in ("Critical", "High", "Medium", "Low"):
            self.assertIn(f"### {level}", self.text,
                          f"worked report is missing the {level} band")

    def test_report_states_what_could_not_be_checked(self):
        self.assertIn("What I could not check", self.text)

    def test_report_admits_sampling_rather_than_implying_full_coverage(self):
        flat = " ".join(self.text.split())
        self.assertRegex(flat, r"looked at one[^.]{0,60}eleven")

    def test_skill_points_at_the_worked_report(self):
        skill = SKILL_MD.read_text(encoding="utf-8")
        self.assertRegex(skill, r"examples\.md.{0,40}§6|§6.{0,60}report")


class TestReadme(unittest.TestCase):
    def test_readme_lists_every_reference_file(self):
        # The README's table is how someone decides whether this skill covers
        # their problem. A reference it doesn't mention is one nobody opens.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for ref in sorted((ROOT / "references").glob("*.md")):
            self.assertIn(f"references/{ref.name}", readme,
                          f"README does not mention {ref.name}")


class TestAgentSkillAgreement(unittest.TestCase):
    """The agents ship in the same package as the skill and carry their own
    copy of the checklist. When the skill is corrected and they are not, the
    package contradicts itself — and the agent is what actually runs."""

    def setUp(self):
        self.auditor = (AGENTS / "seo-page-auditor.md").read_text(encoding="utf-8")

    def test_auditor_marks_dead_rich_result_types(self):
        # Assert the correction is present rather than that the claim is
        # absent. Absence-testing prose with a regex fails on word order —
        # "Dead for rich results: FAQPage" reads the opposite way round from
        # "FAQPage is dead" and means the same thing.
        line = next((l for l in self.auditor.splitlines()
                     if "FAQPage" in l and "Dead for rich results" in l), None)
        self.assertIsNotNone(
            line, "auditor must list FAQPage under dead rich-result types")
        self.assertIn("2026", self.auditor)

    def test_auditor_does_not_treat_top_10_as_predicting_citation(self):
        self.assertRegex(
            self.auditor, r"(76%|not the predictor|entry ticket)",
            "auditor must carry the corrected top-10 framing")

    def test_auditor_warns_against_regex_reading_of_html(self):
        # Minified HTML drops optional quotes, so a quote-assuming search
        # reports present tags as missing — a one-directional error that
        # always lands as a false finding.
        flat = " ".join(self.auditor.split())
        self.assertRegex(flat, r"(lang=en|name=viewport|rel=canonical)")
        self.assertRegex(flat, r"(unconfirmed|not.{0,12}absent|parse)")

    def test_auditor_resolves_a_canonical_before_reporting_it(self):
        # A non-self-referencing canonical is consolidation as often as a bug.
        flat = " ".join(self.auditor.split())
        self.assertIn("Resolve a canonical before reporting it", flat)
        self.assertIn("deliberate consolidation", flat)
        self.assertIn("contradicts the sitemap", flat)

    def test_auditor_checks_ai_retrieval_crawlers(self):
        for bot in ("OAI-SearchBot", "PerplexityBot"):
            self.assertIn(bot, self.auditor,
                          "auditor should check whether AI engines can fetch the page")

    def test_auditor_carries_the_schema_citation_correction(self):
        # Same reasoning: the previous version of this test matched the
        # correction itself, since "do not claim schema improves AI citation"
        # contains the phrase it was scanning for.
        self.assertRegex(
            self.auditor,
            r"[Dd]o not claim schema improves AI citation",
            "auditor must carry the schema/citation correction verbatim")


class TestTheGatesAgreeEverywhere(unittest.TestCase):
    """"The gates" is the skill's organizing idea — "nothing else matters until
    these pass". It was defined three incompatible ways: five items in
    SKILL.md, all of section A plus D in the checklist, and all six sections in
    the auditor. The same missing canonical was "cannot rank" or a Medium
    finding depending only on which file got read."""

    def test_skill_names_exactly_five_gates(self):
        section = SKILL_MD.read_text(encoding="utf-8").split("## The gates")[1]
        section = section.split("\n## ")[0]
        numbered = re.findall(r"^\d+\. \*\*", section, re.MULTILINE)
        self.assertEqual(len(numbered), 5, "SKILL.md should list five gates")

    def test_checklist_gates_are_items_not_whole_sections(self):
        flat = " ".join((ROOT / "references" / "audit-checklist.md")
                        .read_text(encoding="utf-8").split())
        self.assertIn("gates** are five specific items, not whole sections", flat)
        # The four gate items in section A carry the label; the others must not.
        for item in ("A1", "A2", "A3", "A8"):
            self.assertRegex(flat, item + r"\.[^|]{0,90}\(GATE\.\)", item)

    def test_checklist_says_a_missing_canonical_still_ranks(self):
        flat = " ".join((ROOT / "references" / "audit-checklist.md")
                        .read_text(encoding="utf-8").split())
        self.assertRegex(flat, r"no canonical still ranks|canonical still ranks")
        self.assertRegex(flat, r"sitemap[^.]{0,60}still ranks|not an entry requirement")

    def test_auditor_does_not_call_six_sections_the_gate(self):
        flat = " ".join((AGENTS / "seo-page-auditor.md")
                        .read_text(encoding="utf-8").split())
        self.assertNotIn("Sections 1–6 are the gate", flat)
        self.assertIn("five items, not six sections", flat)

    def test_the_cli_gates_the_same_five(self):
        sys.path.insert(0, str(ROOT / "tools-seo-audit-cli" / "scripts"))
        from seo_aeo.models import GATE_ITEMS
        self.assertEqual(set(GATE_ITEMS),
                         {"A1", "A2", "A3", "A8", "D1", "D2", "D3", "D4"})


class TestSamplingIsOperationalized(unittest.TestCase):
    """"Cluster by template and audit a representative" was stated three times
    and never defined — no grouping method, no count per cluster, no rule for
    picking the representative. That leaves the decision that matters to
    whoever reads it."""

    def setUp(self):
        self.flat = " ".join(SKILL_MD.read_text(encoding="utf-8").split())

    def test_says_how_many_pages_per_cluster(self):
        self.assertIn("Audit three per cluster", self.flat)

    def test_says_which_pages_to_pick(self):
        for token in ("newest", "oldest", "most content"):
            self.assertTrue(token in self.flat, f"missing {token!r}")

    def test_says_how_to_group(self):
        self.assertRegex(self.flat, r"route file|path shape")

    def test_covers_pages_that_have_no_cluster(self):
        self.assertRegex(self.flat, r"singleton|homepage, pricing, contact")


class TestPastedComponentReview(unittest.TestCase):
    def test_names_the_div_onclick_bug(self):
        flat = " ".join(SKILL_MD.read_text(encoding="utf-8").split())
        self.assertIn("<div onClick>", flat)
        # The reason it matters: crawlers follow hrefs, not click handlers.
        self.assertRegex(flat, r"does not fire click handlers|not fire click")


class TestRtlGuidanceIsOperationalized(unittest.TestCase):
    """The portal/dir-inheritance bug was named in SKILL.md and examples.md and
    missing from both artifacts meant to run an exhaustive RTL check, which is
    where it would actually get looked for."""

    def test_every_rtl_artifact_covers_the_portal_bug(self):
        for path in (SKILL_MD,
                     ROOT / "references" / "audit-checklist.md",
                     AGENTS / "seo-page-auditor.md"):
            flat = " ".join(path.read_text(encoding="utf-8").split())
            self.assertTrue(
                "portal" in flat.lower() or "document.body" in flat,
                f"{path.name} should cover portaled overlays")

    def test_the_checklist_and_auditor_cover_the_layout_traps(self):
        # assertTrue rather than assertIn: assertIn dumps the whole file into
        # the failure message, which buries the one word that is missing.
        for path in (ROOT / "references" / "audit-checklist.md",
                     AGENTS / "seo-page-auditor.md"):
            flat = " ".join(path.read_text(encoding="utf-8").split())
            for token in ("-inline-start", "mirror", 'dir="ltr"'):
                self.assertTrue(token in flat, f"{path.name} missing {token!r}")


class TestFrameworkGuidance(unittest.TestCase):
    """A sitemap.xml written to a framework project's repo root is not served.
    The fix looks applied and changes nothing, which is worse than no fix."""

    def setUp(self):
        self.flat = " ".join(SKILL_MD.read_text(encoding="utf-8").split())

    def test_names_where_a_static_sitemap_actually_goes(self):
        self.assertRegex(self.flat, r"public/")
        self.assertRegex(self.flat, r"static/")
        self.assertRegex(self.flat, r"not served")

    def test_names_where_head_tags_come_from_per_framework(self):
        for token in ("generateMetadata", "svelte:head", "useHead", "next/head"):
            self.assertIn(token, self.flat, token)

    def test_says_a_route_fix_affects_more_pages_than_were_audited(self):
        self.assertRegex(self.flat, r"route file[^|]{0,200}more pages")


class TestNoDevUrlsInSource(unittest.TestCase):
    """A canonical pointing at someone's laptop is worse than no canonical.
    The skill, the fixer agent, and the CLI all have to refuse it — the CLI
    wrote one before this was checked."""

    def test_skill_and_fixer_both_refuse_dev_urls(self):
        for path in (SKILL_MD, AGENTS / "seo-fixer.md"):
            flat = " ".join(path.read_text(encoding="utf-8").split())
            self.assertRegex(flat, r"localhost:\d+",
                             f"{path.name} should name the address this is about")
            self.assertIn("TODO", flat, path.name)


class TestAgents(unittest.TestCase):
    """The agents are optional (Claude Code only) but must stay loadable."""

    def test_agents_have_valid_frontmatter(self):
        for agent in AGENTS.glob("*.md"):
            fm = frontmatter(agent)
            self.assertIn("name", fm)
            self.assertTrue(NAME_RE.fullmatch(fm["name"]), agent.name)

    def test_auditor_does_not_probe_for_exposed_files(self):
        # Requesting /.env or /.git/config is unauthorized scanning of a host
        # that may not belong to the person asking, and is not an SEO check.
        text = (AGENTS / "seo-page-auditor.md").read_text(encoding="utf-8")
        self.assertNotRegex(
            text, r"(try|check|request|fetch)\s+`?/\.(env|git)",
            "auditor must not instruct probing for exposed config files")

    def test_auditor_cannot_write(self):
        # The read-only guarantee is the whole reason the split exists.
        fm = frontmatter(AGENTS / "seo-page-auditor.md")
        for forbidden in ("Edit", "Write"):
            self.assertNotIn(forbidden, fm.get("tools", ""),
                             "the auditor must stay read-only")


if __name__ == "__main__":
    unittest.main(verbosity=2)

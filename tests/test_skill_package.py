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
        # a Desktop user with an instruction they cannot follow.
        for path in [SKILL_MD] + list((ROOT / "references").glob("*.md")):
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

    def test_llms_txt_not_sold_as_a_lever(self):
        # Check every mention, not just the first — the first is the
        # volatile-facts table, the claim itself lives further down.
        self.assertIn("llms.txt", self.text)
        self.assertRegex(self.text, r"llms\.txt.{0,900}?(not a citation lever|"
                                    r"no major provider has confirmed)")


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


class TestAgents(unittest.TestCase):
    """The agents are optional (Claude Code only) but must stay loadable."""

    def test_agents_have_valid_frontmatter(self):
        for agent in AGENTS.glob("*.md"):
            fm = frontmatter(agent)
            self.assertIn("name", fm)
            self.assertTrue(NAME_RE.fullmatch(fm["name"]), agent.name)

    def test_auditor_cannot_write(self):
        # The read-only guarantee is the whole reason the split exists.
        fm = frontmatter(AGENTS / "seo-page-auditor.md")
        for forbidden in ("Edit", "Write"):
            self.assertNotIn(forbidden, fm.get("tools", ""),
                             "the auditor must stay read-only")


if __name__ == "__main__":
    unittest.main(verbosity=2)

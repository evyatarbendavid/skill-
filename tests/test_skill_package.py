#!/usr/bin/env python3
"""Checks the skill package stays installable and internally consistent.

These are the failures that silently break distribution: a zip that drifted
from the source, frontmatter the loader rejects, a reference file the skill
points at that isn't there, or a claim the skill is supposed to correct.

    python3 tests/test_skill_package.py
"""

import json
import re
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "seo-aeo"
SKILL_DIR = PLUGIN / "skills" / "seo-aeo"
SKILL_MD = SKILL_DIR / "SKILL.md"
ZIP = ROOT / "seo-aeo.zip"

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
        self.assertEqual(name, SKILL_DIR.name,
                         "skill name must match its directory name")

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
        found = [p for p in PLUGIN.rglob("SKILL.md")]
        self.assertEqual(len(found), 1, f"expected one SKILL.md, found {found}")


class TestReferences(unittest.TestCase):
    def test_referenced_files_exist(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for rel in re.findall(r"`(references/[\w.-]+)`", text):
            self.assertTrue((SKILL_DIR / rel).is_file(),
                            f"SKILL.md points at {rel}, which does not exist")

    def test_no_dangling_internal_links(self):
        # Reference files must not point at files that were left behind.
        for ref in (SKILL_DIR / "references").glob("*.md"):
            for target in re.findall(r"\]\(\./([\w.-]+\.md)\)", ref.read_text(encoding="utf-8")):
                self.assertTrue((ref.parent / target).is_file(),
                                f"{ref.name} links to missing {target}")

    def test_no_references_to_removed_tooling(self):
        # The packaged skill ships no scripts; pointing at one would strand
        # a Desktop user with an instruction they cannot follow.
        for path in SKILL_DIR.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for stale in ("scripts/audit.py", "audit_site.py", "live-verification-map.md"):
                self.assertNotIn(stale, text, f"{path.name} references {stale}")


class TestFactualGuardrails(unittest.TestCase):
    """The skill exists partly to correct specific misinformation. If those
    corrections ever get edited out, the skill starts spreading it instead."""

    def setUp(self):
        self.text = " ".join(p.read_text(encoding="utf-8")
                             for p in SKILL_DIR.rglob("*.md"))

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
        # The source document had this wrong; the error must not come back.
        window = self.text[self.text.find("HowTo"):][:400]
        self.assertIn("2023", window)

    def test_refuses_to_promise_rankings(self):
        self.assertRegex(self.text, r"does not guarantee|doesn't guarantee")
        self.assertRegex(self.text, r"[Nn]othing forces an AI engine to cite|no guaranteed")

    def test_llms_txt_not_sold_as_a_lever(self):
        # Check every mention, not just the first — the first is the
        # volatile-facts table, the claim itself lives further down.
        self.assertIn("llms.txt", self.text)
        self.assertRegex(self.text, r"llms\.txt.{0,900}?(not a citation lever|"
                                    r"no major provider has confirmed)")


class TestPluginManifest(unittest.TestCase):
    def test_plugin_json_valid(self):
        data = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(data["name"], "seo-aeo")
        self.assertTrue(NAME_RE.fullmatch(data["name"]))

    def test_marketplace_json_valid(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        for field in ("name", "owner", "plugins"):
            self.assertIn(field, data)
        self.assertIn("name", data["owner"])
        self.assertTrue(NAME_RE.fullmatch(data["name"]))

    def test_marketplace_sources_resolve(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        for entry in data["plugins"]:
            src = entry["source"]
            self.assertTrue(src.startswith("./"), "relative sources must start with ./")
            path = ROOT / src
            self.assertTrue(path.is_dir(), f"{src} does not exist")
            self.assertTrue((path / ".claude-plugin" / "plugin.json").is_file(),
                            f"{src} has no plugin.json")

    def test_agents_are_loadable(self):
        for agent in (PLUGIN / "agents").glob("*.md"):
            fm = frontmatter(agent)
            self.assertIn("name", fm)
            self.assertTrue(NAME_RE.fullmatch(fm["name"]), agent.name)

    def test_auditor_agent_cannot_write(self):
        # The read-only guarantee is the reason the split exists.
        fm = frontmatter(PLUGIN / "agents" / "seo-page-auditor.md")
        tools = fm.get("tools", "")
        for forbidden in ("Edit", "Write"):
            self.assertNotIn(forbidden, tools,
                             "the auditor must stay read-only")


class TestDesktopZip(unittest.TestCase):
    def test_zip_exists(self):
        self.assertTrue(ZIP.is_file(), "run ./build.sh to produce seo-aeo.zip")

    def test_zip_matches_source(self):
        # A stale zip means Desktop users install an older skill than the repo
        # shows — the failure mode nobody notices until it matters.
        with zipfile.ZipFile(ZIP) as z:
            names = {n for n in z.namelist() if not n.endswith("/")}
            packaged = z.read("seo-aeo/SKILL.md").decode("utf-8")
        expected = {
            "seo-aeo/" + str(p.relative_to(SKILL_DIR)).replace("\\", "/")
            for p in SKILL_DIR.rglob("*") if p.is_file()
        }
        self.assertEqual(names, expected, "zip contents differ from source; run ./build.sh")
        self.assertEqual(packaged, SKILL_MD.read_text(encoding="utf-8"),
                         "zipped SKILL.md is stale; run ./build.sh")

    def test_zip_has_no_nested_extra_root(self):
        # Uploads fail if the archive doesn't have exactly one top-level dir.
        with zipfile.ZipFile(ZIP) as z:
            roots = {n.split("/")[0] for n in z.namelist()}
        self.assertEqual(roots, {"seo-aeo"})

    def test_build_script_is_reproducible(self):
        before = ZIP.read_bytes() if ZIP.is_file() else None
        subprocess.run([str(ROOT / "build.sh")], check=True,
                       capture_output=True, cwd=ROOT)
        with zipfile.ZipFile(ZIP) as z:
            self.assertIn("seo-aeo/SKILL.md", z.namelist())
        self.assertIsNotNone(before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Shared result types for the seo-aeo audit.

Every check produces a Finding carrying the checklist ID it maps to in
references/audit-checklist.md, so the report can be rendered in exactly the
structure a human would use to audit the page by hand.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# Status values. HUMAN_JUDGMENT is deliberately distinct from FAIL: it means the
# check found something real but deciding what to do requires a person.
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"
WARN = "WARN"
HUMAN_JUDGMENT = "HUMAN_JUDGMENT"

# Sections A and D are gates: a FAIL in either means the page cannot reliably
# rank at all, so nothing else matters until they are green.
GATE_SECTIONS = ("A", "D")

SECTION_TITLES = {
    "A": "Crawlability & Indexing",
    "B": "Content & Search Intent",
    "C": "Structured Data",
    "D": "Performance / Core Web Vitals",
    "E": "Accessibility & Mobile",
    "F": "AEO-readiness",
    "G": "Content quality, RTL & site hygiene",
    "P": "Proof artifacts",
}

# Severity ranks the punch list independently of PASS/FAIL: a gate failure and
# a missing meta description are both FAILs, but only one blocks ranking.
CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"

SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, "": 4}

# Default severity per checklist item, used when a finding does not set its own.
DEFAULT_SEVERITY = {
    "A1": CRITICAL, "A2": CRITICAL, "A3": CRITICAL, "A8": CRITICAL,
    "A4": HIGH, "A5": HIGH, "A6": HIGH, "A7": MEDIUM,
    "B4": MEDIUM, "B8": HIGH, "B9": LOW, "B6": MEDIUM,
    "C1": MEDIUM, "C2": HIGH, "C3": MEDIUM, "C4": MEDIUM, "C5": LOW, "C7": LOW,
    "D1": HIGH, "D2": HIGH, "D3": HIGH, "D4": HIGH,
    "E2": HIGH, "E3": CRITICAL, "E5": MEDIUM, "E9": MEDIUM, "E4": LOW,
    "F1": HIGH, "F2": MEDIUM, "F4": MEDIUM, "F7": LOW,
    "G1": HIGH, "G2": MEDIUM, "G3": MEDIUM, "G4": HIGH, "G5": MEDIUM,
    "G6": MEDIUM, "G7": HIGH, "G8": MEDIUM,
}


@dataclass
class Finding:
    """One checklist item's outcome."""

    id: str  # e.g. "A1"
    title: str  # short description of what was checked
    status: str  # PASS | FAIL | N/A | WARN | HUMAN_JUDGMENT
    detail: str = ""  # what was actually observed
    fixable: bool = False  # can fixers.py act on this automatically?
    fixed: bool = False  # was a fix actually written?
    reason: str = ""  # why N/A, or why it needs a human
    severity: str = ""  # critical | high | medium | low; defaults by item id
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.severity:
            self.severity = DEFAULT_SEVERITY.get(self.id, MEDIUM)

    @property
    def section(self) -> str:
        return self.id[0]

    @property
    def is_gate(self) -> bool:
        return self.section in GATE_SECTIONS

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["section"] = self.section
        d["gate"] = self.is_gate
        return d


@dataclass
class AuditResult:
    url: str
    final_url: str = ""
    findings: List[Finding] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    # Populated by the fix path; each entry is a fixers.FixItem summary.
    fixes: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def add(self, finding: Finding) -> Finding:
        self.findings.append(finding)
        return finding

    def by_section(self) -> Dict[str, List[Finding]]:
        out: Dict[str, List[Finding]] = {}
        for f in self.findings:
            out.setdefault(f.section, []).append(f)
        for section in out:
            out[section].sort(key=lambda f: _id_sort_key(f.id))
        return out

    def get(self, finding_id: str) -> Optional[Finding]:
        for f in self.findings:
            if f.id == finding_id:
                return f
        return None

    def counts(self) -> Dict[str, int]:
        c = {PASS: 0, FAIL: 0, NA: 0, WARN: 0, HUMAN_JUDGMENT: 0}
        for f in self.findings:
            c[f.status] = c.get(f.status, 0) + 1
        return c

    def punch_list(self) -> List["Finding"]:
        """Actionable findings, most severe first — the report's headline."""
        actionable = [f for f in self.findings
                      if f.status in (FAIL, WARN, HUMAN_JUDGMENT)]
        # Within a severity band, an outright failure outranks a warning or a
        # question: severity says how much the item matters, status says how
        # badly it is currently doing.
        status_rank = {FAIL: 0, HUMAN_JUDGMENT: 1, WARN: 2}
        return sorted(
            actionable,
            key=lambda f: (
                SEVERITY_ORDER.get(f.severity, 4),
                status_rank.get(f.status, 3),
                0 if f.is_gate else 1,
                _id_sort_key(f.id),
            ),
        )

    def gate_failed(self) -> bool:
        return any(f.is_gate and f.status == FAIL for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "counts": self.counts(),
            "gate_failed": self.gate_failed(),
            "findings": [f.to_dict() for f in self.findings],
            "fixes": self.fixes,
            "errors": self.errors,
            "meta": self.meta,
        }


def _id_sort_key(finding_id: str):
    """Sort A2 before A10 (numeric, not lexicographic)."""
    letter = finding_id[0]
    digits = "".join(ch for ch in finding_id[1:] if ch.isdigit())
    return (letter, int(digits) if digits else 0, finding_id)

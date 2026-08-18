"""Render an AuditResult in the shape of the manual checklist.

Findings are grouped by checklist section (A-F, P), gates first, so the output
reads like the audit a person would run by hand — and so a failure that blocks
ranking entirely never gets buried under cosmetic warnings.
"""

import json
import sys
from typing import List

from .models import (
    FAIL,
    GATE_SECTIONS,
    HUMAN_JUDGMENT,
    NA,
    PASS,
    SECTION_TITLES,
    WARN,
    AuditResult,
    Finding,
)

# Plain-ASCII markers: terminals and CI logs mangle box-drawing characters.
_MARKERS = {
    PASS: "PASS",
    FAIL: "FAIL",
    NA: "n/a ",
    WARN: "WARN",
    HUMAN_JUDGMENT: "ASK ",
}

_RULE = "-" * 72


def _supports_color(stream) -> bool:
    return hasattr(stream, "isatty") and stream.isatty()


def _colorize(text: str, status: str, enabled: bool) -> str:
    if not enabled:
        return text
    codes = {
        PASS: "\033[32m",
        FAIL: "\033[31m",
        WARN: "\033[33m",
        HUMAN_JUDGMENT: "\033[36m",
        NA: "\033[90m",
    }
    code = codes.get(status)
    return f"{code}{text}\033[0m" if code else text


def _wrap(text: str, width: int, indent: str) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current = indent
    for word in words:
        # Wrap only once the line has real content, so a single long word still
        # gets its own line rather than an empty one.
        if current.strip() and len(current) + len(word) > width:
            lines.append(current.rstrip())
            current = indent
        current += word + " "
    if current.strip():
        lines.append(current.rstrip())
    return lines


def _render_finding(finding: Finding, color: bool) -> List[str]:
    marker = _colorize(f"[{_MARKERS.get(finding.status, finding.status)}]",
                       finding.status, color)
    head = f"  {marker} {finding.id:<4} {finding.title}"
    lines = [head]

    detail = finding.detail or ""
    if finding.reason:
        detail = f"{detail} ({finding.reason})" if detail else finding.reason
    if detail:
        lines.extend(_wrap(detail, 72, " " * 13))
    if finding.fixed:
        lines.append(" " * 13 + "-> fixed")
    elif finding.fixable and finding.status == FAIL:
        lines.append(" " * 13 + "-> auto-fixable: re-run with --fix --local-dir PATH")
    return lines


def render_text(result: AuditResult, stream=None) -> str:
    stream = stream or sys.stdout
    color = _supports_color(stream)
    out: List[str] = []

    out.append("")
    out.append(f"SEO + AEO audit: {result.url}")
    if result.final_url and result.final_url != result.url:
        out.append(f"  final URL: {result.final_url}")
    out.append(_RULE)

    sections = result.by_section()
    # Gates first — a FAIL there means nothing below it can help yet.
    order = [s for s in GATE_SECTIONS if s in sections]
    order += [s for s in sorted(sections) if s not in GATE_SECTIONS]

    for section in order:
        findings = sections[section]
        title = SECTION_TITLES.get(section, section)
        gate = "  [GATE]" if section in GATE_SECTIONS else ""
        out.append("")
        out.append(f"{section}. {title}{gate}")
        for finding in findings:
            out.extend(_render_finding(finding, color))

    out.append("")
    out.append(_RULE)
    counts = result.counts()
    out.append(
        "Summary: "
        + f"{counts.get(PASS, 0)} pass, "
        + f"{counts.get(FAIL, 0)} fail, "
        + f"{counts.get(WARN, 0)} warn, "
        + f"{counts.get(HUMAN_JUDGMENT, 0)} need a decision, "
        + f"{counts.get(NA, 0)} not applicable"
    )

    if result.gate_failed():
        out.append(
            _colorize(
                "GATE FAILED — this page cannot reliably rank until sections "
                "A and D are clean. Fix those before anything else.",
                FAIL,
                color,
            )
        )

    asks = [f for f in result.findings if f.status == HUMAN_JUDGMENT]
    if asks:
        out.append("")
        out.append("Needs your decision (not guessed at):")
        for finding in asks:
            out.append(f"  {finding.id}: {finding.reason or finding.detail}")

    if result.fixes:
        applied = [f for f in result.fixes if f.get("applied")]
        planned = [f for f in result.fixes if not f.get("applied")]
        out.append("")
        if applied:
            out.append(f"Fixes written ({len(applied)}):")
            for fix in applied:
                out.append(f"  {fix['finding_id']}: {fix['summary']}")
                out.append(f"    -> {fix['path']}")
        if planned:
            out.append(f"Fixes planned but NOT written ({len(planned)}) — add --apply:")
            for fix in planned:
                out.append(f"  {fix['finding_id']}: {fix['summary']}")
                out.append(f"    -> {fix['path']}")

        placeholders = [f for f in result.fixes if f.get("placeholders")]
        if placeholders:
            out.append("")
            out.append("TODO placeholders left for you (values only you know):")
            for fix in placeholders:
                for field_path in fix["placeholders"]:
                    out.append(f"  {fix['path']}: {field_path}")

    refusals = result.meta.get("fix_refusals") or []
    if refusals:
        out.append("")
        out.append("Fixes deliberately not attempted:")
        for refusal in refusals:
            out.append(f"  {refusal['finding_id']}: {refusal['reason']}")

    if result.errors:
        out.append("")
        out.append("Checks that could not run:")
        for error in result.errors:
            out.append(f"  {error}")

    out.append("")
    out.append(
        "Thresholds and deprecation facts in this report come from the skill's "
        "static reference. Re-verify anything date-sensitive against "
        "web.dev and developers.google.com before acting on it."
    )
    out.append("")
    return "\n".join(out)


def render_json(result: AuditResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


def render_diffs(result: AuditResult) -> str:
    """Full unified diffs for planned fixes, so a human can review before apply."""
    if not result.fixes:
        return ""
    chunks = []
    for fix in result.fixes:
        if not fix.get("diff"):
            continue
        chunks.append(f"# {fix['finding_id']}: {fix['summary']}")
        chunks.append(fix["diff"])
    return "\n".join(chunks)

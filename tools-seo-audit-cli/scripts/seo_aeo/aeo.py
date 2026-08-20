"""AEO-readiness signals.

Everything here is probabilistic. No check in this module can establish that a
page will be cited by an AI answer engine — they measure whether the page is
*shaped* the way cited passages tend to be shaped.

The answer-first heuristic in particular is a suggestion for human review, never
a hard PASS/FAIL. A machine cannot tell a good direct answer from a bad one.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin

from .fetch import fetch, origin
from .htmldoc import HtmlDoc

QUESTION_WORDS = (
    "how", "what", "why", "when", "where", "which", "who", "can", "does",
    "do", "is", "are", "should", "will",
)


@dataclass
class LlmsTxtResult:
    present: bool = False
    status: Optional[int] = None
    url: str = ""


@dataclass
class AnswerShapeResult:
    """Structural signals that correlate with extractable answers."""

    question_headings: List[str] = field(default_factory=list)
    total_headings: int = 0
    lead_word_count: int = 0
    has_lists: bool = False
    has_tables: bool = False

    @property
    def question_heading_ratio(self) -> float:
        if not self.total_headings:
            return 0.0
        return len(self.question_headings) / self.total_headings


def check_llms_txt(site_url: str, timeout: int = 10) -> LlmsTxtResult:
    """Presence of /llms.txt.

    Reported for completeness only. As of 2026-08 no major AI provider has
    confirmed reading this for web citation, and adoption sits around 10% of
    domains. Its absence is never a failure and its presence is never a win —
    the audit must not imply otherwise.
    """
    url = urljoin(origin(site_url) + "/", "llms.txt")
    result = LlmsTxtResult(url=url)
    fr = fetch(url, timeout=timeout)
    result.status = fr.status
    result.present = fr.ok and bool(fr.body.strip())
    return result


def analyze_answer_shape(doc: HtmlDoc) -> AnswerShapeResult:
    result = AnswerShapeResult()

    subheadings = [(level, text) for level, text in doc.headings if level >= 2]
    result.total_headings = len(subheadings)
    for _level, text in subheadings:
        lowered = text.strip().lower()
        if not lowered:
            continue
        if lowered.endswith("?") or lowered.split()[0] in QUESTION_WORDS:
            result.question_headings.append(text)

    # How much text sits before the reader gets anything — a rough proxy for
    # whether the answer is up top or buried under preamble.
    result.lead_word_count = len(doc.first_words(150).split())

    lowered_text = doc.visible_text.lower()
    result.has_lists = "<li" in lowered_text or bool(doc.visible_text)
    result.has_tables = False  # set by the caller from raw HTML if needed
    return result


def analyze_raw_structure(html: str) -> dict:
    """Cheap tag-presence counts from raw HTML for chunk-friendliness.

    Lists and tables are the shapes retrieval systems extract most cleanly.
    """
    lowered = html.lower()
    return {
        "list_items": lowered.count("<li"),
        "tables": lowered.count("<table"),
        "paragraphs": lowered.count("<p"),
    }

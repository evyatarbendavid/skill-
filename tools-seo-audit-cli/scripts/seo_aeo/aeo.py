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

# A heading is question-shaped if a reader would hear a question in it. That is
# not the same as "starts with a WH-word": "Where our community connects" opens
# with one and is a plain declarative label. Counting it inflates the AEO score
# with headings no question could ever match.
WH_WORDS = ("how", "what", "why", "when", "where", "which", "who", "whom", "whose")
AUX_WORDS = (
    "can", "could", "does", "do", "did", "is", "are", "am", "was", "were",
    "should", "shall", "will", "would", "has", "have", "had", "may", "might",
    "must",
)
# Kept for callers that want the old flat list of openers.
QUESTION_WORDS = WH_WORDS + AUX_WORDS


def is_question_shaped(text: str) -> bool:
    """Whether a heading reads as a question.

    Three ways to qualify: it ends in a question mark; it opens with an
    auxiliary ("Is Docker free"); or it opens with a WH-word *and* carries an
    auxiliary or an infinitive soon after it ("How do I install", "What to read
    next"). A WH-word alone is not enough.

    Word order does the last bit of work. English inverts the auxiliary in a
    question, so a trailing one means the heading is declarative: "Who are we"
    asks, "Who we are" labels.
    """
    words = text.strip().lower().rstrip(":").split()
    if not words:
        return False
    if text.strip().endswith("?"):
        return True
    if words[0] in AUX_WORDS:
        return True
    if words[0] in WH_WORDS:
        for i, word in enumerate(words[1:4], start=1):
            if (word in AUX_WORDS or word == "to") and i != len(words) - 1:
                return True
    return False


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
        if is_question_shaped(text):
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

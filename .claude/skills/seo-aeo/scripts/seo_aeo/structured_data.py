"""JSON-LD extraction and validation.

Rules mirror references/structured-data-schemas.md — keep the two in sync.

We validate *required properties per type*, which is what actually gates
rich-result eligibility. We do not attempt full Schema.org validation; the Rich
Results Test is the authority and the report says so.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Required properties per Google's documented requirements. Recommended-but-not-
# required properties are reported separately as suggestions, never as failures.
REQUIRED_PROPS: Dict[str, List[str]] = {
    "Article": ["headline", "image", "datePublished", "author"],
    "BlogPosting": ["headline", "image", "datePublished", "author"],
    "NewsArticle": ["headline", "image", "datePublished", "author"],
    "Organization": ["name", "url"],
    "Person": ["name"],
    "BreadcrumbList": ["itemListElement"],
    "WebSite": ["name", "url"],
}

RECOMMENDED_PROPS: Dict[str, List[str]] = {
    "Article": ["dateModified", "publisher", "mainEntityOfPage"],
    "BlogPosting": ["dateModified", "publisher", "mainEntityOfPage"],
    "NewsArticle": ["dateModified", "publisher", "mainEntityOfPage"],
    "Organization": ["logo", "sameAs"],
    "Person": ["url", "jobTitle", "sameAs", "description"],
    "BreadcrumbList": [],
    "WebSite": [],
}

ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "Report"}

# Types that are still valid Schema.org vocabulary but no longer produce any
# Google rich result. Present => informational note, never a failure.
DEAD_RICH_RESULT_TYPES = {
    "FAQPage": "FAQ rich results were restricted Aug 2023 and fully removed May 2026",
    "HowTo": "HowTo rich results were deprecated Aug/Sep 2023",
    "ClaimReview": "retired June 2025",
    "Course": "Course Info rich result retired June 2025",
    "SpecialAnnouncement": "retired June 2025",
    "Vehicle": "Vehicle Listing retired June 2025",
    "Occupation": "Estimated Salary retired June 2025",
}


@dataclass
class BlockResult:
    types: List[str] = field(default_factory=list)
    missing_required: Dict[str, List[str]] = field(default_factory=dict)
    missing_recommended: Dict[str, List[str]] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    raw_index: int = 0

    @property
    def valid(self) -> bool:
        return not self.missing_required


@dataclass
class StructuredDataResult:
    blocks: List[BlockResult] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    types_present: List[str] = field(default_factory=list)
    raw_count: int = 0

    @property
    def has_any(self) -> bool:
        return bool(self.blocks)

    @property
    def all_valid(self) -> bool:
        return bool(self.blocks) and all(b.valid for b in self.blocks)

    def has_type(self, *names: str) -> bool:
        present = set(self.types_present)
        return any(n in present for n in names)

    def has_article(self) -> bool:
        return bool(ARTICLE_TYPES & set(self.types_present))

    def missing_summary(self) -> List[str]:
        out = []
        for block in self.blocks:
            for typ, missing in block.missing_required.items():
                out.append(f"{typ}: missing {', '.join(missing)}")
        return out


def _types_of(node: Dict[str, Any]) -> List[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [t for t in raw if isinstance(t, str)]
    return []


def _iter_entities(node: Any, depth: int = 0):
    """Yield every dict that carries an @type, walking @graph and nested nodes.

    Depth-limited: deeply nested markup is legal but we only need the entities
    that Google would treat as top-level candidates.
    """
    if depth > 6:
        return
    if isinstance(node, list):
        for item in node:
            yield from _iter_entities(item, depth + 1)
        return
    if not isinstance(node, dict):
        return
    if "@graph" in node:
        yield from _iter_entities(node["@graph"], depth + 1)
    if _types_of(node):
        yield node
    for key, value in node.items():
        if key in ("@graph", "@context", "@type"):
            continue
        if isinstance(value, (dict, list)):
            yield from _iter_entities(value, depth + 1)


def _has_prop(entity: Dict[str, Any], prop: str) -> bool:
    value = entity.get(prop)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate_entity(entity: Dict[str, Any], block: BlockResult) -> None:
    for typ in _types_of(entity):
        if typ not in block.types:
            block.types.append(typ)

        if typ in DEAD_RICH_RESULT_TYPES:
            block.notes.append(
                f"{typ} present — valid vocabulary, but no rich result: "
                f"{DEAD_RICH_RESULT_TYPES[typ]}. Fine to keep; not a ranking lever."
            )

        required = REQUIRED_PROPS.get(typ)
        if required:
            missing = [p for p in required if not _has_prop(entity, p)]
            if missing:
                block.missing_required.setdefault(typ, []).extend(missing)

        recommended = RECOMMENDED_PROPS.get(typ)
        if recommended:
            missing_rec = [p for p in recommended if not _has_prop(entity, p)]
            if missing_rec:
                block.missing_recommended.setdefault(typ, []).extend(missing_rec)

        # Article author as a bare string still validates for Google, but a
        # Person object is materially stronger for E-E-A-T. Worth saying.
        if typ in ARTICLE_TYPES and isinstance(entity.get("author"), str):
            block.notes.append(
                "author is a plain string; a nested Person object with url/"
                "jobTitle/sameAs is a stronger E-E-A-T signal."
            )

        if typ == "BreadcrumbList":
            items = entity.get("itemListElement")
            if isinstance(items, list):
                for i, item in enumerate(items, start=1):
                    if not isinstance(item, dict):
                        continue
                    if not _has_prop(item, "position"):
                        block.notes.append(f"BreadcrumbList item {i} is missing 'position'.")
                    if not _has_prop(item, "name"):
                        block.notes.append(f"BreadcrumbList item {i} is missing 'name'.")


def analyze(jsonld_raw: List[str]) -> StructuredDataResult:
    result = StructuredDataResult(raw_count=len(jsonld_raw))

    for index, blob in enumerate(jsonld_raw):
        try:
            data = json.loads(blob)
        except json.JSONDecodeError as exc:
            # Unparsable JSON-LD is invisible to Google — a real finding, but it
            # must not stop us analyzing the other blocks.
            result.parse_errors.append(f"block {index + 1}: invalid JSON ({exc})")
            continue

        block = BlockResult(raw_index=index)
        entities = list(_iter_entities(data))
        if not entities:
            block.notes.append("block contains no entity with an @type")
        for entity in entities:
            validate_entity(entity, block)

        # De-duplicate accumulated property lists.
        for bucket in (block.missing_required, block.missing_recommended):
            for key in bucket:
                bucket[key] = sorted(set(bucket[key]))
        block.notes = list(dict.fromkeys(block.notes))

        result.blocks.append(block)
        for typ in block.types:
            if typ not in result.types_present:
                result.types_present.append(typ)

    return result

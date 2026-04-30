import re

from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from dog_core.dog_index import DogIndex, SearchEntry, ensure_index
from dog_core.models import DogDocument, PrimitiveType


DEFAULT_MIN_SCORE = 40.0

SECTION_WEIGHTS: dict[str, float] = {
    "Condition": 1.05,
    "Outcome": 1.05,
    "State": 1.0,
    "Events": 1.0,
    "Fields": 1.0,
    "Description": 0.95,
    "Actors": 0.9,
    "Behaviors": 0.9,
    "Components": 0.9,
    "Data": 0.9,
    "Notes": 0.55,
}


class SearchResult(BaseModel):
    """A single search result."""

    name: str
    primitive_type: PrimitiveType
    file_path: str
    score: float
    snippet: str
    is_exact_match: bool = False
    name_distance: int = 0
    match_kinds: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.primitive_type.value,
            "file": self.file_path,
            "score": round(self.score, 2),
            "snippet": self.snippet,
            "matches": self.match_kinds,
            "exact": self.is_exact_match,
        }


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def _extract_snippet(query: str, content: str) -> str:
    """Extract a contextual snippet around the query match."""
    query_lower = query.lower()
    content_lower = content.lower()
    idx = content_lower.find(query_lower)

    if idx >= 0:
        start = max(0, idx - 40)
        end = min(len(content), idx + len(query) + 40)
        snippet = content[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        return snippet

    snippet = content[:120].strip()
    if len(content) > 120:
        snippet += "..."
    return snippet


def _score_name(query: str, entry: SearchEntry) -> tuple[float, list[str]]:
    query_norm = DogIndex.normalize_name(query)
    kinds: list[str] = []

    if query_norm == entry.normalized_name:
        return 100.0, ["exact_name"]

    doc_tokens = _tokens(entry.document.name)
    query_tokens = _tokens(query)
    exact_token_score = 0.0
    if query_tokens and query_tokens.issubset(doc_tokens):
        exact_token_score = 88.0
        kinds.append("name_token")
    elif query_norm and query_norm in entry.normalized_name:
        exact_token_score = 82.0
        kinds.append("name_substring")

    raw_fuzzy_score = max(
        fuzz.token_set_ratio(query, entry.document.name),
        fuzz.partial_ratio(query.lower(), entry.document.name.lower()),
    )
    fuzzy_score = raw_fuzzy_score * 0.9 if raw_fuzzy_score >= 55 else 0.0
    if fuzzy_score:
        kinds.append("fuzzy_name")

    return max(exact_token_score, fuzzy_score), kinds


def _score_sections(query: str, entry: SearchEntry) -> tuple[float, str, list[str]]:
    query_norm = query.lower()
    query_tokens = _tokens(query)
    best_score = 0.0
    best_snippet = ""
    best_kinds: list[str] = []

    for section_name, content in entry.sections.items():
        if not content:
            continue

        content_lower = content.lower()
        content_tokens = _tokens(content)
        weight = SECTION_WEIGHTS.get(section_name, 0.75)
        kinds: list[str] = []

        exact_score = 0.0
        if query_norm and query_norm in content_lower:
            exact_score = 82.0
            kinds.append(f"section:{section_name}:phrase")
        elif query_tokens and query_tokens.issubset(content_tokens):
            exact_score = 72.0
            kinds.append(f"section:{section_name}:token")

        raw_fuzzy_score = fuzz.WRatio(query, content)
        fuzzy_score = raw_fuzzy_score * 0.72 if raw_fuzzy_score >= 62 else 0.0
        if fuzzy_score:
            kinds.append(f"section:{section_name}:fuzzy")

        score = min(100.0, max(exact_score, fuzzy_score) * weight)
        if score > best_score:
            best_score = score
            best_snippet = _extract_snippet(query, content)
            best_kinds = kinds

    return best_score, best_snippet, best_kinds


def _score_references(query: str, entry: SearchEntry) -> tuple[float, list[str]]:
    best_score = 0.0
    kinds: list[str] = []
    query_norm = DogIndex.normalize_name(query)

    for ref in entry.references:
        ref_norm = DogIndex.normalize_name(ref.name)
        if query_norm == ref_norm:
            best_score = max(best_score, 86.0)
            kinds.append("reference_exact")
        elif query_norm and query_norm in ref_norm:
            best_score = max(best_score, 72.0)
            kinds.append("reference_substring")
        else:
            fuzzy_score = fuzz.token_set_ratio(query, ref.name) * 0.7
            if fuzzy_score >= 45:
                best_score = max(best_score, fuzzy_score)
                kinds.append("reference_fuzzy")

    return best_score, kinds


def _calculate_score(query: str, entry: SearchEntry) -> tuple[float, str, bool, int, list[str]]:
    """Calculate local hybrid relevance score on a 0-100 scale."""
    doc = entry.document
    header_snippet = f"# {doc.primitive_type.value}: {doc.name}"
    query_norm = DogIndex.normalize_name(query)
    is_exact_match = query_norm == entry.normalized_name
    name_distance = Levenshtein.distance(query_norm, entry.normalized_name)

    name_score, name_kinds = _score_name(query, entry)
    section_score, section_snippet, section_kinds = _score_sections(query, entry)
    ref_score, ref_kinds = _score_references(query, entry)

    candidates = [
        (name_score, header_snippet, name_kinds),
        (section_score, section_snippet, section_kinds),
        (ref_score, header_snippet, ref_kinds),
    ]
    score, snippet, kinds = max(candidates, key=lambda item: item[0])

    all_kinds = list(dict.fromkeys([*name_kinds, *section_kinds, *ref_kinds]))
    return min(score, 100.0), snippet or header_snippet, is_exact_match, name_distance, all_kinds or kinds


async def search_documents(
    index_or_docs: DogIndex | list[DogDocument],
    query: str,
    type_filter: PrimitiveType | None = None,
    limit: int = 10,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[SearchResult]:
    """Search documents for a query string."""
    index = ensure_index(index_or_docs)
    results: list[SearchResult] = []

    for entry in index.search_entries:
        doc = entry.document
        if type_filter and doc.primitive_type != type_filter:
            continue

        score, snippet, is_exact_match, name_distance, match_kinds = _calculate_score(query, entry)
        if score < min_score:
            continue

        results.append(
            SearchResult(
                name=doc.name,
                primitive_type=doc.primitive_type,
                file_path=str(doc.file_path),
                score=score,
                snippet=snippet,
                is_exact_match=is_exact_match,
                name_distance=name_distance,
                match_kinds=match_kinds,
            )
        )

    results.sort(
        key=lambda r: (
            -int(r.is_exact_match),
            -r.score,
            r.name_distance,
            r.primitive_type.value,
            r.name.lower(),
            r.file_path,
        )
    )
    return results[:limit]

from pydantic import BaseModel
from rapidfuzz import fuzz

from dog_core.models import DogDocument, PrimitiveType


class SearchResult(BaseModel):
    """A single search result."""

    name: str
    primitive_type: PrimitiveType
    file_path: str
    score: float
    snippet: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.primitive_type.value,
            "file": self.file_path,
            "score": self.score,
            "snippet": self.snippet,
        }


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

    # No exact match, use content start as snippet
    snippet = content[:80].strip()
    if len(content) > 80:
        snippet += "..."
    return snippet


def _score_name(query: str, doc: DogDocument) -> float:
    """Score based on name matching using multiple strategies."""
    # Exact match (case-insensitive)
    if query.lower() == doc.name.lower():
        return 100.0

    # Token-based matching for multi-word queries
    token_score = fuzz.token_set_ratio(query, doc.name)

    # Partial ratio for substring matches
    partial_score = fuzz.partial_ratio(query.lower(), doc.name.lower())

    return max(token_score, partial_score)


def _score_sections(query: str, doc: DogDocument) -> tuple[float, str]:
    """Score based on section content matching."""
    best_score = 0.0
    best_snippet = ""

    for section in doc.sections:
        # Use WRatio which combines multiple strategies intelligently
        content_score = fuzz.WRatio(query, section.content)

        if content_score > best_score:
            best_score = content_score
            best_snippet = _extract_snippet(query, section.content)

    return best_score, best_snippet


def _score_references(query: str, doc: DogDocument) -> float:
    """Score based on reference matching."""
    best_score = 0.0
    for ref in doc.references:
        ref_score = fuzz.token_set_ratio(query, ref.name)
        best_score = max(best_score, ref_score)
    return best_score


def _calculate_score(query: str, doc: DogDocument) -> tuple[float, str]:
    """Calculate relevance score using RapidFuzz fuzzy matching.

    Uses multiple matching strategies:
    - Exact match for names (highest priority)
    - Token-based matching for flexible word order
    - Partial matching for substring matches

    Returns (score, snippet) tuple. Score is 0-100, higher = more relevant.
    """
    header_snippet = f"# {doc.primitive_type.value}: {doc.name}"
    name_score = _score_name(query, doc)
    section_score, section_snippet = _score_sections(query, doc)
    ref_score = _score_references(query, doc)

    # Name matches get priority - boost by 20% over content matches
    boosted_name_score = name_score * 1.2 if name_score > 0 else 0

    # Return best score with appropriate snippet (cap at 100)
    if boosted_name_score >= section_score and boosted_name_score >= ref_score:
        return min(boosted_name_score, 100.0), header_snippet
    if section_score >= ref_score:
        return section_score, section_snippet
    return ref_score, header_snippet


async def search_documents(
    docs: list[DogDocument],
    query: str,
    type_filter: PrimitiveType | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    """Search documents for a query string.

    Args:
        docs: List of parsed DogDocuments to search
        query: Search query string
        type_filter: Optional filter by primitive type
        limit: Maximum number of results to return

    Returns:
        List of SearchResult sorted by relevance
    """
    results: list[SearchResult] = []

    for doc in docs:
        # Apply type filter
        if type_filter and doc.primitive_type != type_filter:
            continue

        score, snippet = _calculate_score(query, doc)

        results.append(
            SearchResult(
                name=doc.name,
                primitive_type=doc.primitive_type,
                file_path=str(doc.file_path),
                score=score,
                snippet=snippet or f"# {doc.primitive_type.value}: {doc.name}",
            )
        )

    # Sort by score descending and return top k
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]

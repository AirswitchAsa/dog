from pydantic import BaseModel, Field

from dog_core.dog_index import AmbiguousLookupError, DogIndex, ensure_index
from dog_core.models import DogDocument, PrimitiveType


class ResolvedReference(BaseModel):
    """A reference with resolution status."""

    name: str
    ref_type: PrimitiveType
    resolved: bool
    file_path: str | None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.ref_type.value,
            "resolved": self.resolved,
            "file": self.file_path,
        }


class GetResult(BaseModel):
    """Result of getting a document with resolved references."""

    name: str
    primitive_type: PrimitiveType
    file_path: str
    sections: list[dict]
    references: list[ResolvedReference]
    raw_content: str
    expanded_documents: list[dict] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.primitive_type.value,
            "file": self.file_path,
            "sections": self.sections,
            "references": [r.to_dict() for r in self.references],
            "raw": self.raw_content,
            "expanded_documents": self.expanded_documents,
        }

    def to_text(self) -> str:
        """Format as readable text output."""
        lines = [self.raw_content.strip(), ""]

        if self.references:
            resolved = [r for r in self.references if r.resolved]
            unresolved = [r for r in self.references if not r.resolved]

            if resolved:
                lines.append("--- Resolved References ---")
                for ref in resolved:
                    lines.append(f"  {ref.ref_type.value}: {ref.name} -> {ref.file_path}")
                lines.append("")

            if unresolved:
                lines.append("--- Unresolved References ---")
                for ref in unresolved:
                    lines.append(f"  {ref.ref_type.value}: {ref.name}")
                lines.append("")

        return "\n".join(lines)


def _document_to_dict(doc: DogDocument, index: DogIndex) -> dict:
    return {
        "name": doc.name,
        "type": doc.primitive_type.value,
        "file": str(doc.file_path),
        "sections": [{"name": s.name, "content": s.content} for s in doc.sections],
        "references": [
            ResolvedReference(
                name=ref.reference.name,
                ref_type=ref.reference.ref_type,
                resolved=ref.target is not None,
                file_path=str(ref.target.file_path) if ref.target else None,
            ).to_dict()
            for ref in index.references_from(doc)
        ],
        "raw": doc.raw_content,
    }


def _resolve_references(index: DogIndex, doc: DogDocument) -> list[ResolvedReference]:
    resolved_refs: list[ResolvedReference] = []
    for occurrence in index.references_from(doc):
        resolved_refs.append(
            ResolvedReference(
                name=occurrence.reference.name,
                ref_type=occurrence.reference.ref_type,
                resolved=occurrence.target is not None,
                file_path=str(occurrence.target.file_path) if occurrence.target else None,
            )
        )
    return resolved_refs


def _expand_referenced_documents(index: DogIndex, target: DogDocument, depth: int) -> list[dict]:
    if depth <= 0:
        return []

    expanded: list[dict] = []
    seen = {index.key_for(target)}
    queue: list[tuple[DogDocument, int]] = [(target, 0)]

    while queue:
        doc, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue

        for occurrence in index.references_from(doc):
            ref_doc = occurrence.target
            if ref_doc is None:
                continue
            key = index.key_for(ref_doc)
            if key in seen:
                continue
            seen.add(key)
            expanded.append(_document_to_dict(ref_doc, index))
            queue.append((ref_doc, current_depth + 1))

    return expanded


async def get_document(
    index_or_docs: DogIndex | list[DogDocument],
    name: str,
    type_filter: PrimitiveType | None = None,
    depth: int = 0,
) -> GetResult | None:
    """Get a document by name with resolved references.

    Args:
        docs: List of parsed DogDocuments
        name: Name of the primitive to find
        type_filter: Optional filter by primitive type

    Returns:
        GetResult if found, None otherwise
    """
    index = ensure_index(index_or_docs)
    try:
        target = index.resolve(name, type_filter)
    except AmbiguousLookupError:
        raise

    if target is None:
        return None

    return GetResult(
        name=target.name,
        primitive_type=target.primitive_type,
        file_path=str(target.file_path),
        sections=[{"name": s.name, "content": s.content} for s in target.sections],
        references=_resolve_references(index, target),
        raw_content=target.raw_content,
        expanded_documents=_expand_referenced_documents(index, target, depth),
    )


async def list_documents(
    index_or_docs: DogIndex | list[DogDocument],
    type_filter: PrimitiveType | None = None,
) -> list[dict]:
    """List all documents, optionally filtered by type.

    Args:
        docs: List of parsed DogDocuments
        type_filter: Optional filter by primitive type

    Returns:
        List of document summaries
    """
    index = ensure_index(index_or_docs)
    results = [
        {
            "name": doc.name,
            "type": doc.primitive_type.value,
            "file": str(doc.file_path),
        }
        for doc in index.documents_of_type(type_filter)
    ]

    # Sort by type then name
    results.sort(key=lambda x: (x["type"], x["name"]))
    return results

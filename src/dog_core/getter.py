from pydantic import BaseModel

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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.primitive_type.value,
            "file": self.file_path,
            "sections": self.sections,
            "references": [r.to_dict() for r in self.references],
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


async def get_document(
    docs: list[DogDocument],
    name: str,
    type_filter: PrimitiveType | None = None,
) -> GetResult | None:
    """Get a document by name with resolved references.

    Args:
        docs: List of parsed DogDocuments
        name: Name of the primitive to find
        type_filter: Optional filter by primitive type

    Returns:
        GetResult if found, None otherwise
    """
    # Build index for reference resolution
    doc_index: dict[tuple[PrimitiveType, str], DogDocument] = {}
    for doc in docs:
        doc_index[(doc.primitive_type, doc.name)] = doc
        # Also index by name only for fuzzy matching
        doc_index[(doc.primitive_type, doc.name.lower())] = doc

    # Find the target document
    target: DogDocument | None = None
    name_lower = name.lower()

    for doc in docs:
        if type_filter and doc.primitive_type != type_filter:
            continue

        if doc.name.lower() == name_lower:
            target = doc
            break

    if target is None:
        return None

    # Resolve references
    resolved_refs: list[ResolvedReference] = []
    for ref in target.references:
        # Try to find the referenced document
        ref_doc = doc_index.get((ref.ref_type, ref.name))
        if ref_doc is None:
            ref_doc = doc_index.get((ref.ref_type, ref.name.lower()))

        resolved_refs.append(
            ResolvedReference(
                name=ref.name,
                ref_type=ref.ref_type,
                resolved=ref_doc is not None,
                file_path=str(ref_doc.file_path) if ref_doc else None,
            )
        )

    return GetResult(
        name=target.name,
        primitive_type=target.primitive_type,
        file_path=str(target.file_path),
        sections=[{"name": s.name, "content": s.content} for s in target.sections],
        references=resolved_refs,
        raw_content=target.raw_content,
    )


async def list_documents(
    docs: list[DogDocument],
    type_filter: PrimitiveType | None = None,
) -> list[dict]:
    """List all documents, optionally filtered by type.

    Args:
        docs: List of parsed DogDocuments
        type_filter: Optional filter by primitive type

    Returns:
        List of document summaries
    """
    results = []
    for doc in docs:
        if type_filter and doc.primitive_type != type_filter:
            continue

        results.append(
            {
                "name": doc.name,
                "type": doc.primitive_type.value,
                "file": str(doc.file_path),
            }
        )

    # Sort by type then name
    results.sort(key=lambda x: (x["type"], x["name"]))
    return results

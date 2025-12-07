from pydantic import BaseModel

from dog_core.models import DogDocument, PrimitiveType, parse_primitive_query


class RefResult(BaseModel):
    """A document that references the target."""

    name: str
    primitive_type: PrimitiveType
    file_path: str
    line_numbers: list[int]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.primitive_type.value,
            "file": self.file_path,
            "lines": self.line_numbers,
        }


class RefsResult(BaseModel):
    """Result of finding reverse references."""

    target_name: str
    target_type: PrimitiveType | None
    referencing_docs: list[RefResult]

    def to_dict(self) -> dict:
        return {
            "target": self.target_name,
            "target_type": self.target_type.value if self.target_type else None,
            "referenced_by": [r.to_dict() for r in self.referencing_docs],
            "count": len(self.referencing_docs),
        }

    def to_text(self) -> str:
        """Format as readable text output."""
        if self.target_type:
            header = f"References to {self.target_type.value}: {self.target_name}"
        else:
            header = f"References to: {self.target_name}"

        lines = [header, "=" * len(header), ""]

        if not self.referencing_docs:
            lines.append("No references found.")
            return "\n".join(lines)

        for ref in self.referencing_docs:
            lines.append(f"{ref.primitive_type.value}: {ref.name}")
            lines.append(f"  File: {ref.file_path}")
            lines.append(f"  Lines: {', '.join(str(ln) for ln in ref.line_numbers)}")
            lines.append("")

        lines.append(f"Total: {len(self.referencing_docs)} document(s)")
        return "\n".join(lines)


async def find_refs(
    docs: list[DogDocument],
    query: str,
) -> RefsResult:
    """Find all documents that reference a given primitive.

    Args:
        docs: List of parsed DogDocuments
        query: Name of the primitive (with optional sigil prefix)

    Returns:
        RefsResult with all referencing documents
    """
    target_name, target_type = parse_primitive_query(query)
    target_name_lower = target_name.lower()

    referencing_docs: list[RefResult] = []

    for doc in docs:
        # Collect references to the target from this document
        matching_lines: list[int] = []

        for ref in doc.references:
            # Match by name (case-insensitive)
            if ref.name.lower() != target_name_lower:
                continue

            # If type filter specified, must match
            if target_type and ref.ref_type != target_type:
                continue

            matching_lines.append(ref.line_number)

        if matching_lines:
            referencing_docs.append(
                RefResult(
                    name=doc.name,
                    primitive_type=doc.primitive_type,
                    file_path=str(doc.file_path),
                    line_numbers=sorted(set(matching_lines)),
                )
            )

    # Sort by type then name
    referencing_docs.sort(key=lambda x: (x.primitive_type.value, x.name))

    return RefsResult(
        target_name=target_name,
        target_type=target_type,
        referencing_docs=referencing_docs,
    )

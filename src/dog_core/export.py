from dog_core.models import DogDocument, PrimitiveType


async def export_documents(
    docs: list[DogDocument],
    type_filter: PrimitiveType | None = None,
    include_raw: bool = True,
) -> list[dict]:
    """Export all documents as a list of dictionaries.

    Args:
        docs: List of parsed DogDocuments
        type_filter: Optional filter by primitive type
        include_raw: Whether to include raw markdown content

    Returns:
        List of document dictionaries suitable for JSON serialization
    """
    results: list[dict] = []

    for doc in docs:
        if type_filter and doc.primitive_type != type_filter:
            continue

        doc_dict: dict = {
            "name": doc.name,
            "type": doc.primitive_type.value,
            "file": str(doc.file_path),
            "sections": [{"name": s.name, "content": s.content} for s in doc.sections],
            "references": [
                {
                    "name": r.name,
                    "type": r.ref_type.value,
                    "line": r.line_number,
                }
                for r in doc.references
            ],
        }

        if include_raw:
            doc_dict["raw"] = doc.raw_content

        results.append(doc_dict)

    # Sort by type then name
    results.sort(key=lambda x: (x["type"], x["name"]))

    return results

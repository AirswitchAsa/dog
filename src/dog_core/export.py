from dog_core.dog_index import DogIndex, ensure_index
from dog_core.models import DogDocument, PrimitiveType


async def export_documents(
    index_or_docs: DogIndex | list[DogDocument],
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
    index = ensure_index(index_or_docs)
    results: list[dict] = []

    for doc in index.documents_of_type(type_filter):
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

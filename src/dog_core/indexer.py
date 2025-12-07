import asyncio
from pathlib import Path

from dog_core.models import DogDocument, PrimitiveType


def _generate_index_content(docs: list[DogDocument], project_name: str) -> str:
    """Generate the content for an index.dog.md file.

    Args:
        docs: List of parsed DogDocuments (excluding the index itself)
        project_name: Name for the Project

    Returns:
        Formatted index.dog.md content
    """
    # Group documents by type
    by_type: dict[PrimitiveType, list[str]] = {ptype: [] for ptype in PrimitiveType}

    for doc in docs:
        # Skip Project type documents (we're generating a new one)
        if doc.primitive_type != PrimitiveType.PROJECT:
            by_type[doc.primitive_type].append(doc.name)

    # Sort names within each type
    for names in by_type.values():
        names.sort()

    # Build the index content
    lines = [
        f"# Project: {project_name}",
        "",
        "## Description",
        "",
        f"Project index for {project_name}.",
        "",
    ]

    # Add each section if it has entries
    section_map = [
        (PrimitiveType.ACTOR, "Actors"),
        (PrimitiveType.BEHAVIOR, "Behaviors"),
        (PrimitiveType.COMPONENT, "Components"),
        (PrimitiveType.DATA, "Data"),
    ]

    for ptype, section_name in section_map:
        names = by_type[ptype]
        if names:
            lines.append(f"## {section_name}")
            lines.append("")
            for name in names:
                lines.append(f"- {name}")
            lines.append("")

    # Add Notes section placeholder
    lines.append("## Notes")
    lines.append("")
    lines.append("- Auto-generated index")
    lines.append("")

    return "\n".join(lines)


async def generate_index(docs: list[DogDocument], project_name: str, output_path: Path) -> str:
    """Generate an index.dog.md file.

    Args:
        docs: List of parsed DogDocuments to index
        project_name: Name for the Project
        output_path: Path where index.dog.md will be written

    Returns:
        Generated content
    """
    # Filter out any existing index from the docs
    filtered_docs = [doc for doc in docs if doc.file_path.name != "index.dog.md"]

    content = _generate_index_content(filtered_docs, project_name)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, output_path.write_text, content)

    return content

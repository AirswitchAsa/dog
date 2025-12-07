import asyncio
from pathlib import Path

from dog_core.models import DogDocument, PrimitiveType


def _generate_index_content(docs: list[DogDocument], project_name: str, output_path: Path) -> str:
    """Generate the content for an index.dog.md file.

    Args:
        docs: List of parsed DogDocuments (excluding the index itself)
        project_name: Name for the Project
        output_path: Path where index.dog.md will be written (for relative paths)

    Returns:
        Formatted index.dog.md content
    """
    # Group documents by type, storing (name, relative_path) tuples
    by_type: dict[PrimitiveType, list[tuple[str, str]]] = {ptype: [] for ptype in PrimitiveType}

    output_dir = output_path.parent

    for doc in docs:
        # Skip Project type documents (we're generating a new one)
        if doc.primitive_type != PrimitiveType.PROJECT:
            # Calculate relative path from index location to doc
            try:
                relative_path = doc.file_path.relative_to(output_dir)
            except ValueError:
                # If not relative, use absolute path
                relative_path = doc.file_path
            by_type[doc.primitive_type].append((doc.name, str(relative_path)))

    # Sort by name within each type
    for entries in by_type.values():
        entries.sort(key=lambda x: x[0])

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
        entries = by_type[ptype]
        if entries:
            lines.append(f"## {section_name}")
            lines.append("")
            for name, rel_path in entries:
                lines.append(f"- [{name}]({rel_path})")
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

    content = _generate_index_content(filtered_docs, project_name, output_path)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, output_path.write_text, content)

    return content

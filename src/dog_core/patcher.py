import asyncio
import re
from pathlib import Path

from pydantic import BaseModel

from dog_core.models import ALLOWED_SECTIONS, DogDocument, PrimitiveType


class PatchData(BaseModel):
    """Data structure for patch operations."""

    sections: dict[str, str] = {}  # section_name -> new_content


class PatchResult(BaseModel):
    """Result of a patch operation."""

    file_path: str
    updated_sections: list[str]
    success: bool
    error: str | None = None


def _update_section(content: str, section_name: str, new_content: str) -> tuple[str, bool]:
    """Update a specific section in the markdown content.

    Returns (new_content, was_updated)
    """
    # Pattern to match ## SectionName followed by content until next ## or end
    # This handles the section header and all content up to the next section
    pattern = rf"(## {re.escape(section_name)}\n\n)(.*?)(?=\n## |\Z)"

    def replace(match: re.Match[str]) -> str:
        header = match.group(1)
        return f"{header}{new_content.strip()}\n"

    new_text, count = re.subn(pattern, replace, content, flags=re.DOTALL)

    return new_text, count > 0


def _add_section(content: str, section_name: str, new_content: str) -> str:
    """Add a new section to the markdown content.

    Adds the section before Notes (if present) or at the end.
    """
    notes_pattern = r"\n## Notes\n"
    notes_match = re.search(notes_pattern, content)

    section_text = f"\n## {section_name}\n\n{new_content.strip()}\n"

    if notes_match:
        # Insert before Notes
        return content[: notes_match.start()] + section_text + content[notes_match.start() :]

    # Add at end, ensuring proper spacing
    if not content.endswith("\n"):
        content += "\n"
    return content + section_text


async def patch_document(
    docs: list[DogDocument],
    name: str,
    patch: PatchData,
    type_filter: PrimitiveType | None = None,
) -> PatchResult:
    """Patch a document with new section content.

    Args:
        docs: List of parsed DogDocuments
        name: Name of the primitive to patch
        patch: Patch data with section updates
        type_filter: Optional filter by primitive type

    Returns:
        PatchResult with outcome
    """
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
        return PatchResult(
            file_path="",
            updated_sections=[],
            success=False,
            error=f"Document not found: {name}",
        )

    # Validate patch has sections to update
    if not patch.sections:
        return PatchResult(
            file_path=str(target.file_path),
            updated_sections=[],
            success=False,
            error="No sections provided to update",
        )

    # Validate sections are allowed for this primitive type
    allowed = ALLOWED_SECTIONS[target.primitive_type]
    for section_name in patch.sections:
        if section_name not in allowed:
            return PatchResult(
                file_path=str(target.file_path),
                updated_sections=[],
                success=False,
                error=f"Section '{section_name}' not allowed for {target.primitive_type.value}. "
                f"Allowed: {', '.join(sorted(allowed))}",
            )

    # Apply patches to content
    content = target.raw_content
    updated: list[str] = []

    for section_name, new_content in patch.sections.items():
        new_text, was_updated = _update_section(content, section_name, new_content)
        if was_updated:
            content = new_text
            updated.append(section_name)
        else:
            # Section doesn't exist, add it
            content = _add_section(content, section_name, new_content)
            updated.append(section_name)

    # Write back to file
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: Path(target.file_path).write_text(content))

    return PatchResult(
        file_path=str(target.file_path),
        updated_sections=updated,
        success=True,
    )

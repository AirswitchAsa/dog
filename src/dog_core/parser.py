import asyncio
import re
from pathlib import Path

import marko
from marko.md_renderer import MarkdownRenderer

from dog_core.models import DogDocument, InlineReference, PrimitiveType, Section


class ParseError(Exception):
    """Raised when a .dog.md file cannot be parsed."""

    pass


def _extract_text(element: object) -> str:
    """Recursively extract raw text from a marko element."""
    if hasattr(element, "children"):
        children = getattr(element, "children")  # noqa: B009
        if isinstance(children, str):
            return children
        return "".join(_extract_text(child) for child in children)
    return ""


def _parse_header(line: str) -> tuple[PrimitiveType, str] | None:
    """Parse a level-1 header to extract primitive type and name.

    Expected format: # Type: Name
    """
    match = re.match(r"^#\s+(Project|Actor|Behavior|Component|Data):\s+(.+)$", line)
    if not match:
        return None

    type_str, name = match.groups()
    return PrimitiveType(type_str), name.strip()


def _find_line_number(content: str, search_text: str, start_line: int = 1) -> int:
    """Find the line number where search_text first appears."""
    lines = content.split("\n")
    for i, line in enumerate(lines[start_line - 1 :], start=start_line):
        if search_text in line:
            return i
    return start_line


def _extract_references(content: str) -> list[InlineReference]:
    """Extract inline references from markdown content.

    Reference syntax (using sigils inside backticks):
    - `@name` -> Actor
    - `!name` -> Behavior
    - `#name` -> Component
    - `&name` -> Data
    """
    references: list[InlineReference] = []
    lines = content.split("\n")

    # Pattern matches backtick-wrapped sigil references
    # Supports names with spaces, hyphens, underscores
    sigil_pattern = re.compile(r"`([@!#&])([^`]+)`")

    sigil_map = {
        "@": PrimitiveType.ACTOR,
        "!": PrimitiveType.BEHAVIOR,
        "#": PrimitiveType.COMPONENT,
        "&": PrimitiveType.DATA,
    }

    for line_num, line in enumerate(lines, start=1):
        for match in sigil_pattern.finditer(line):
            sigil = match.group(1)
            name = match.group(2).strip()
            references.append(
                InlineReference(
                    name=name,
                    ref_type=sigil_map[sigil],
                    line_number=line_num,
                )
            )

    return references


def _parse_content(content: str, file_path: Path) -> DogDocument:
    """Parse markdown content into a DogDocument."""
    lines = content.split("\n")

    # Find and parse the H1 header
    header_result = None
    header_line = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("# "):
            header_result = _parse_header(line)
            header_line = i + 1
            break

    if header_result is None:
        raise ParseError(
            f"{file_path}: Missing or invalid header. "
            "Expected format: # Type: Name (where Type is Project, Actor, Behavior, Component, or Data)"
        )

    primitive_type, name = header_result

    # Parse sections using marko
    doc = marko.parse(content)
    renderer = MarkdownRenderer()

    sections: list[Section] = []
    current_section: Section | None = None

    for element in doc.children:
        if isinstance(element, marko.block.Heading) and element.level == 2:
            # Save previous section
            if current_section is not None:
                sections.append(current_section)

            section_name = _extract_text(element).strip()
            section_line = _find_line_number(content, f"## {section_name}", header_line)
            current_section = Section(name=section_name, content="", line_number=section_line)
        elif current_section is not None:
            # Accumulate content under current section
            rendered = renderer.render(element)
            current_section = Section(
                name=current_section.name,
                content=(current_section.content + rendered).strip(),
                line_number=current_section.line_number,
            )

    # Don't forget the last section
    if current_section is not None:
        sections.append(current_section)

    # Extract inline references
    references = _extract_references(content)

    return DogDocument(
        file_path=file_path,
        primitive_type=primitive_type,
        name=name,
        sections=sections,
        references=references,
        raw_content=content,
    )


async def parse_document(path: Path) -> DogDocument:
    """Parse a .dog.md file into a DogDocument.

    Args:
        path: Path to the .dog.md file

    Returns:
        Parsed DogDocument

    Raises:
        ParseError: If the file cannot be parsed
    """
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, path.read_text)
    return _parse_content(content, path)


async def parse_documents(paths: list[Path]) -> list[DogDocument]:
    """Parse multiple .dog.md files concurrently.

    Args:
        paths: List of paths to .dog.md files

    Returns:
        List of parsed DogDocuments
    """
    tasks = [parse_document(path) for path in paths]
    return await asyncio.gather(*tasks)

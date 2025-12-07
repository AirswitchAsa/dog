import asyncio
import re
from pathlib import Path


def _normalize_content(content: str) -> str:
    """Normalize markdown content whitespace and indentation.

    Normalizations:
    - Trim trailing whitespace from each line
    - Normalize to single blank line between sections
    - Ensure consistent list indentation (2 spaces)
    - Ensure single newline at end of file
    """
    lines = content.split("\n")
    result: list[str] = []
    prev_blank = False

    for line in lines:
        # Trim trailing whitespace
        line = line.rstrip()

        # Track blank lines to collapse multiple blanks into one
        is_blank = len(line) == 0

        if is_blank:
            if not prev_blank and result:
                result.append("")
            prev_blank = True
            continue

        prev_blank = False

        # Normalize list indentation (convert tabs to 2 spaces, normalize indent levels)
        if re.match(r"^\s*[-*+]\s", line):
            # Count leading whitespace
            stripped = line.lstrip()
            indent_chars = len(line) - len(stripped)
            # Convert to 2-space indent levels
            indent_level = indent_chars // 2 if indent_chars > 0 else 0
            line = "  " * indent_level + stripped

        result.append(line)

    # Remove trailing blank lines
    while result and result[-1] == "":
        result.pop()

    # Ensure single newline at end
    return "\n".join(result) + "\n"


async def format_content(content: str) -> str:
    """Format markdown content asynchronously.

    Args:
        content: Raw markdown content

    Returns:
        Formatted markdown content
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _normalize_content, content)


async def format_file(path: Path) -> tuple[bool, str]:
    """Format a .dog.md file.

    Args:
        path: Path to the file

    Returns:
        Tuple of (was_changed, formatted_content)
    """
    loop = asyncio.get_event_loop()
    original = await loop.run_in_executor(None, path.read_text)
    formatted = await format_content(original)

    return original != formatted, formatted


async def format_file_in_place(path: Path) -> bool:
    """Format a .dog.md file in place.

    Args:
        path: Path to the file

    Returns:
        True if the file was modified, False if already formatted
    """
    changed, formatted = await format_file(path)

    if changed:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, path.write_text, formatted)

    return changed

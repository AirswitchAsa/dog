import asyncio
from pathlib import Path


async def find_dog_files(path: Path) -> list[Path]:
    """Find all .dog.md files in the given path.

    Args:
        path: A file path or directory path to search

    Returns:
        List of paths to .dog.md files, sorted alphabetically
    """
    if path.is_file():
        if path.name.endswith(".dog.md"):
            return [path]
        return []

    if not path.is_dir():
        return []

    # Run glob in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    files = await loop.run_in_executor(None, lambda: list(path.rglob("*.dog.md")))

    return sorted(files)

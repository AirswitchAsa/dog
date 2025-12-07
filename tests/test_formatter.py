from pathlib import Path

import pytest

from dog_core import format_content, format_file, format_file_in_place


class TestFormatContent:
    @pytest.mark.asyncio
    async def test_trim_trailing_whitespace(self) -> None:
        content = "# Actor: User   \n\n## Description   \n\nSome text   \n"
        result = await format_content(content)
        lines = result.split("\n")
        for line in lines[:-1]:  # Last line is empty after final newline
            assert not line.endswith(" ")

    @pytest.mark.asyncio
    async def test_collapse_multiple_blank_lines(self) -> None:
        content = "# Actor: User\n\n\n\n## Description\n\nText"
        result = await format_content(content)
        assert "\n\n\n" not in result

    @pytest.mark.asyncio
    async def test_ensure_trailing_newline(self) -> None:
        content = "# Actor: User"
        result = await format_content(content)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    @pytest.mark.asyncio
    async def test_normalize_list_indentation(self) -> None:
        content = "# Actor: User\n\n## Notes\n\n- Item 1\n    - Nested item\n"
        result = await format_content(content)
        assert "  - Nested item" in result

    @pytest.mark.asyncio
    async def test_already_formatted(self) -> None:
        content = "# Actor: User\n\n## Description\n\nSome text\n"
        result = await format_content(content)
        assert result == content


class TestFormatFile:
    @pytest.mark.asyncio
    async def test_detect_changes(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.dog.md"
        file_path.write_text("# Actor: User   \n\nText")

        changed, formatted = await format_file(file_path)
        assert changed is True
        assert "User   " not in formatted

    @pytest.mark.asyncio
    async def test_no_changes_needed(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.dog.md"
        content = "# Actor: User\n\n## Description\n\nText\n"
        file_path.write_text(content)

        changed, formatted = await format_file(file_path)
        assert changed is False
        assert formatted == content


class TestFormatFileInPlace:
    @pytest.mark.asyncio
    async def test_modifies_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.dog.md"
        file_path.write_text("# Actor: User   \n\nText")

        changed = await format_file_in_place(file_path)
        assert changed is True

        new_content = file_path.read_text()
        assert "User   " not in new_content
        assert new_content.endswith("\n")

    @pytest.mark.asyncio
    async def test_no_modification_when_formatted(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.dog.md"
        content = "# Actor: User\n\n## Description\n\nText\n"
        file_path.write_text(content)

        changed = await format_file_in_place(file_path)
        assert changed is False
        assert file_path.read_text() == content

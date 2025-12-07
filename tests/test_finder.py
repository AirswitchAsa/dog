from pathlib import Path

import pytest

from dog_core import find_dog_files


class TestFindDogFiles:
    @pytest.mark.asyncio
    async def test_find_in_directory(self, tmp_dog_dir: Path) -> None:
        files = await find_dog_files(tmp_dog_dir)
        assert len(files) == 2
        names = {f.name for f in files}
        assert "user.dog.md" in names
        assert "login.dog.md" in names

    @pytest.mark.asyncio
    async def test_find_single_file(self, tmp_dog_dir: Path) -> None:
        file_path = tmp_dog_dir / "user.dog.md"
        files = await find_dog_files(file_path)
        assert len(files) == 1
        assert files[0] == file_path

    @pytest.mark.asyncio
    async def test_find_non_dog_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "readme.md"
        file_path.write_text("# Readme")
        files = await find_dog_files(file_path)
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_find_in_empty_directory(self, tmp_path: Path) -> None:
        files = await find_dog_files(tmp_path)
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_find_nested_files(self, tmp_path: Path) -> None:
        nested = tmp_path / "docs" / "actors"
        nested.mkdir(parents=True)
        (nested / "user.dog.md").write_text("# Actor: User\n")

        files = await find_dog_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "user.dog.md"

    @pytest.mark.asyncio
    async def test_find_nonexistent_path(self, tmp_path: Path) -> None:
        files = await find_dog_files(tmp_path / "nonexistent")
        assert len(files) == 0

from pathlib import Path

import pytest

from dog_core import DogDocument, PrimitiveType, generate_index


def make_doc(name: str, ptype: PrimitiveType, base_path: Path | None = None) -> DogDocument:
    """Helper to create test documents."""
    file_path = Path(f"/test/{name.lower()}.dog.md") if base_path is None else base_path / f"{name.lower()}.dog.md"
    return DogDocument(
        file_path=file_path,
        primitive_type=ptype,
        name=name,
        sections=[],
        references=[],
        raw_content=f"# {ptype.value}: {name}\n",
    )


class TestGenerateIndex:
    @pytest.mark.asyncio
    async def test_generates_index_file(self, tmp_path: Path) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Admin", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR),
            make_doc("AuthService", PrimitiveType.COMPONENT),
            make_doc("Credentials", PrimitiveType.DATA),
        ]

        output_path = tmp_path / "index.dog.md"
        content = await generate_index(docs, "TestProject", output_path)

        assert output_path.exists()
        assert content == output_path.read_text()

    @pytest.mark.asyncio
    async def test_index_header(self, tmp_path: Path) -> None:
        docs = [make_doc("User", PrimitiveType.ACTOR)]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "MyApp", output_path)

        assert content.startswith("# Project: MyApp\n")

    @pytest.mark.asyncio
    async def test_index_lists_actors(self, tmp_path: Path) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR, tmp_path),
            make_doc("Admin", PrimitiveType.ACTOR, tmp_path),
        ]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "## Actors" in content
        assert "[Admin]" in content
        assert "[User]" in content

    @pytest.mark.asyncio
    async def test_index_lists_behaviors(self, tmp_path: Path) -> None:
        docs = [
            make_doc("Login", PrimitiveType.BEHAVIOR, tmp_path),
            make_doc("Logout", PrimitiveType.BEHAVIOR, tmp_path),
        ]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "## Behaviors" in content
        assert "[Login]" in content
        assert "[Logout]" in content

    @pytest.mark.asyncio
    async def test_index_lists_components(self, tmp_path: Path) -> None:
        docs = [make_doc("AuthService", PrimitiveType.COMPONENT, tmp_path)]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "## Components" in content
        assert "[AuthService]" in content

    @pytest.mark.asyncio
    async def test_index_lists_data(self, tmp_path: Path) -> None:
        docs = [make_doc("Credentials", PrimitiveType.DATA, tmp_path)]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "## Data" in content
        assert "[Credentials]" in content

    @pytest.mark.asyncio
    async def test_index_excludes_existing_projects(self, tmp_path: Path) -> None:
        docs = [
            make_doc("OldProject", PrimitiveType.PROJECT),
            make_doc("User", PrimitiveType.ACTOR),
        ]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "NewProject", output_path)

        # Should not list OldProject in any section
        assert "OldProject" not in content.replace("# Project: NewProject", "")

    @pytest.mark.asyncio
    async def test_index_sorts_names(self, tmp_path: Path) -> None:
        docs = [
            make_doc("Zeta", PrimitiveType.ACTOR, tmp_path),
            make_doc("Alpha", PrimitiveType.ACTOR, tmp_path),
            make_doc("Beta", PrimitiveType.ACTOR, tmp_path),
        ]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        # Alpha should appear before Beta, Beta before Zeta
        alpha_pos = content.index("[Alpha]")
        beta_pos = content.index("[Beta]")
        zeta_pos = content.index("[Zeta]")

        assert alpha_pos < beta_pos < zeta_pos

    @pytest.mark.asyncio
    async def test_empty_docs(self, tmp_path: Path) -> None:
        output_path = tmp_path / "index.dog.md"
        content = await generate_index([], "EmptyProject", output_path)

        assert "# Project: EmptyProject" in content
        assert "## Description" in content

    @pytest.mark.asyncio
    async def test_index_includes_relative_links(self, tmp_path: Path) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR, tmp_path),
            make_doc("Login", PrimitiveType.BEHAVIOR, tmp_path),
        ]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "- [User](user.dog.md)" in content
        assert "- [Login](login.dog.md)" in content

    @pytest.mark.asyncio
    async def test_index_handles_nested_paths(self, tmp_path: Path) -> None:
        nested_dir = tmp_path / "actors"
        nested_dir.mkdir()
        docs = [make_doc("User", PrimitiveType.ACTOR, nested_dir)]
        output_path = tmp_path / "index.dog.md"

        content = await generate_index(docs, "Test", output_path)

        assert "- [User](actors/user.dog.md)" in content

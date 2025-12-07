from pathlib import Path

import pytest

from dog_core import DogDocument, InlineReference, PrimitiveType, Section, export_documents


def make_doc(
    name: str,
    ptype: PrimitiveType,
    sections: list[str] | None = None,
    references: list[tuple[str, PrimitiveType]] | None = None,
) -> DogDocument:
    """Helper to create test documents."""
    return DogDocument(
        file_path=Path(f"/test/{name.lower()}.dog.md"),
        primitive_type=ptype,
        name=name,
        sections=[
            Section(name=s, content="content", line_number=i + 2) for i, s in enumerate(sections or ["Description"])
        ],
        references=[InlineReference(name=n, ref_type=t, line_number=10) for n, t in (references or [])],
        raw_content=f"# {ptype.value}: {name}\n\n## Description\n\ncontent\n",
    )


class TestExportDocuments:
    @pytest.mark.asyncio
    async def test_export_basic(self) -> None:
        """Should export all documents."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR),
        ]

        result = await export_documents(docs)

        assert len(result) == 2
        # Should be sorted by type then name
        assert result[0]["name"] == "User"
        assert result[0]["type"] == "Actor"
        assert result[1]["name"] == "Login"
        assert result[1]["type"] == "Behavior"

    @pytest.mark.asyncio
    async def test_export_with_type_filter(self) -> None:
        """Should filter by type."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR),
            make_doc("Logout", PrimitiveType.BEHAVIOR),
        ]

        result = await export_documents(docs, type_filter=PrimitiveType.BEHAVIOR)

        assert len(result) == 2
        assert all(r["type"] == "Behavior" for r in result)

    @pytest.mark.asyncio
    async def test_export_includes_sections(self) -> None:
        """Should include section data."""
        docs = [
            make_doc("Login", PrimitiveType.BEHAVIOR, ["Condition", "Description", "Outcome"]),
        ]

        result = await export_documents(docs)

        assert len(result[0]["sections"]) == 3
        assert result[0]["sections"][0]["name"] == "Condition"
        assert result[0]["sections"][1]["name"] == "Description"
        assert result[0]["sections"][2]["name"] == "Outcome"

    @pytest.mark.asyncio
    async def test_export_includes_references(self) -> None:
        """Should include reference data."""
        docs = [
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                references=[("User", PrimitiveType.ACTOR), ("AuthService", PrimitiveType.COMPONENT)],
            ),
        ]

        result = await export_documents(docs)

        assert len(result[0]["references"]) == 2
        assert result[0]["references"][0]["name"] == "User"
        assert result[0]["references"][0]["type"] == "Actor"

    @pytest.mark.asyncio
    async def test_export_includes_raw(self) -> None:
        """Should include raw content by default."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
        ]

        result = await export_documents(docs, include_raw=True)

        assert "raw" in result[0]
        assert "# Actor: User" in result[0]["raw"]

    @pytest.mark.asyncio
    async def test_export_excludes_raw(self) -> None:
        """Should exclude raw content when requested."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
        ]

        result = await export_documents(docs, include_raw=False)

        assert "raw" not in result[0]

    @pytest.mark.asyncio
    async def test_export_empty(self) -> None:
        """Should handle empty doc list."""
        result = await export_documents([])

        assert result == []

    @pytest.mark.asyncio
    async def test_export_includes_file_path(self) -> None:
        """Should include file path."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
        ]

        result = await export_documents(docs)

        assert result[0]["file"] == "/test/user.dog.md"

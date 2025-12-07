from pathlib import Path

import pytest

from dog_core import DogDocument, InlineReference, PrimitiveType, Section, generate_graph


def make_doc(
    name: str,
    ptype: PrimitiveType,
    references: list[tuple[str, PrimitiveType]] | None = None,
) -> DogDocument:
    """Helper to create test documents."""
    return DogDocument(
        file_path=Path(f"/test/{name.lower()}.dog.md"),
        primitive_type=ptype,
        name=name,
        sections=[Section(name="Description", content="test", line_number=2)],
        references=[InlineReference(name=n, ref_type=t, line_number=10) for n, t in (references or [])],
        raw_content=f"# {ptype.value}: {name}\n",
    )


class TestGenerateGraph:
    @pytest.mark.asyncio
    async def test_basic_graph(self) -> None:
        """Should generate valid DOT output."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR)]),
        ]

        result = await generate_graph(docs)

        assert "digraph DOG {" in result
        assert '"@User"' in result
        assert '"!Login"' in result
        assert '"!Login" -> "@User"' in result
        assert "}" in result

    @pytest.mark.asyncio
    async def test_graph_colors(self) -> None:
        """Should include type-specific colors."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR),
            make_doc("AuthService", PrimitiveType.COMPONENT),
            make_doc("Credentials", PrimitiveType.DATA),
        ]

        result = await generate_graph(docs)

        # Check colors are present
        assert "#a22041" in result  # Actor color
        assert "#457b9d" in result  # Behavior color
        assert "#915c8b" in result  # Component color
        assert "#2a9d8f" in result  # Data color

    @pytest.mark.asyncio
    async def test_graph_with_root(self) -> None:
        """Should generate subgraph from root node."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR)]),
            make_doc("Logout", PrimitiveType.BEHAVIOR),  # Disconnected
            make_doc("Settings", PrimitiveType.BEHAVIOR),  # Disconnected
        ]

        result = await generate_graph(docs, root="!Login")

        # Should include Login and User (connected)
        assert '"!Login"' in result
        assert '"@User"' in result
        # Should not include disconnected nodes
        assert '"!Logout"' not in result
        assert '"!Settings"' not in result

    @pytest.mark.asyncio
    async def test_graph_root_not_found(self) -> None:
        """Should handle missing root gracefully."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
        ]

        result = await generate_graph(docs, root="!NonExistent")

        assert 'label="Not found: !NonExistent"' in result

    @pytest.mark.asyncio
    async def test_graph_no_duplicate_edges(self) -> None:
        """Should not create duplicate edges."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                [
                    ("User", PrimitiveType.ACTOR),
                    ("User", PrimitiveType.ACTOR),  # Duplicate ref
                ],
            ),
        ]

        result = await generate_graph(docs)

        # Should only have one edge
        assert result.count('"!Login" -> "@User"') == 1

    @pytest.mark.asyncio
    async def test_graph_only_resolved_edges(self) -> None:
        """Should only create edges to existing nodes."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                [
                    ("User", PrimitiveType.ACTOR),
                    ("NonExistent", PrimitiveType.COMPONENT),  # Missing
                ],
            ),
        ]

        result = await generate_graph(docs)

        assert '"!Login" -> "@User"' in result
        assert "NonExistent" not in result

    @pytest.mark.asyncio
    async def test_empty_graph(self) -> None:
        """Should handle empty doc list."""
        result = await generate_graph([])

        assert "digraph DOG {" in result
        assert "}" in result

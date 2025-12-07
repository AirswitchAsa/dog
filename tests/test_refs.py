from pathlib import Path

import pytest

from dog_core import DogDocument, InlineReference, PrimitiveType, Section, find_refs


def make_doc(
    name: str,
    ptype: PrimitiveType,
    references: list[tuple[str, PrimitiveType, int]] | None = None,
) -> DogDocument:
    """Helper to create test documents."""
    return DogDocument(
        file_path=Path(f"/test/{name.lower()}.dog.md"),
        primitive_type=ptype,
        name=name,
        sections=[Section(name="Description", content="test", line_number=2)],
        references=[InlineReference(name=n, ref_type=t, line_number=ln) for n, t, ln in (references or [])],
        raw_content=f"# {ptype.value}: {name}\n",
    )


class TestFindRefs:
    @pytest.mark.asyncio
    async def test_find_refs_basic(self) -> None:
        """Should find documents that reference the target."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR, 5)]),
            make_doc("Logout", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR, 7)]),
            make_doc("AuthService", PrimitiveType.COMPONENT),
        ]

        result = await find_refs(docs, "@User")

        assert result.target_name == "User"
        assert result.target_type == PrimitiveType.ACTOR
        assert len(result.referencing_docs) == 2
        assert result.referencing_docs[0].name == "Login"
        assert result.referencing_docs[1].name == "Logout"

    @pytest.mark.asyncio
    async def test_find_refs_no_type_filter(self) -> None:
        """Should find refs without type filter."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR, 5)]),
        ]

        result = await find_refs(docs, "User")

        assert result.target_name == "User"
        assert result.target_type is None
        assert len(result.referencing_docs) == 1

    @pytest.mark.asyncio
    async def test_find_refs_case_insensitive(self) -> None:
        """Should match references case-insensitively."""
        docs = [
            make_doc("AuthService", PrimitiveType.COMPONENT),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("authservice", PrimitiveType.COMPONENT, 5)]),
        ]

        result = await find_refs(docs, "#AuthService")

        assert len(result.referencing_docs) == 1
        assert result.referencing_docs[0].name == "Login"

    @pytest.mark.asyncio
    async def test_find_refs_no_matches(self) -> None:
        """Should return empty list when no refs found."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR),
        ]

        result = await find_refs(docs, "@User")

        assert len(result.referencing_docs) == 0

    @pytest.mark.asyncio
    async def test_find_refs_multiple_lines(self) -> None:
        """Should collect all line numbers for multiple refs in same doc."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                [
                    ("User", PrimitiveType.ACTOR, 5),
                    ("User", PrimitiveType.ACTOR, 10),
                    ("User", PrimitiveType.ACTOR, 15),
                ],
            ),
        ]

        result = await find_refs(docs, "@User")

        assert len(result.referencing_docs) == 1
        assert result.referencing_docs[0].line_numbers == [5, 10, 15]

    @pytest.mark.asyncio
    async def test_find_refs_type_filter(self) -> None:
        """Should only match refs with correct type when filter specified."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("User", PrimitiveType.DATA),  # Same name, different type
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                [
                    ("User", PrimitiveType.ACTOR, 5),
                    ("User", PrimitiveType.DATA, 10),
                ],
            ),
        ]

        result = await find_refs(docs, "@User")

        assert len(result.referencing_docs) == 1
        assert result.referencing_docs[0].line_numbers == [5]

    @pytest.mark.asyncio
    async def test_to_text_output(self) -> None:
        """Should format text output correctly."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR, 5)]),
        ]

        result = await find_refs(docs, "@User")
        text = result.to_text()

        assert "References to Actor: User" in text
        assert "Behavior: Login" in text
        assert "Lines: 5" in text
        assert "Total: 1 document(s)" in text

    @pytest.mark.asyncio
    async def test_to_dict_output(self) -> None:
        """Should format dict output correctly."""
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc("Login", PrimitiveType.BEHAVIOR, [("User", PrimitiveType.ACTOR, 5)]),
        ]

        result = await find_refs(docs, "@User")
        d = result.to_dict()

        assert d["target"] == "User"
        assert d["target_type"] == "Actor"
        assert d["count"] == 1
        assert len(d["referenced_by"]) == 1
        assert d["referenced_by"][0]["name"] == "Login"

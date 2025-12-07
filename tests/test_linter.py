from pathlib import Path

import pytest

from dog_core import (
    DogDocument,
    InlineReference,
    PrimitiveType,
    Section,
    lint_documents,
)


def make_doc(
    name: str,
    ptype: PrimitiveType,
    sections: list[str] | None = None,
    references: list[tuple[str, PrimitiveType]] | None = None,
    file_path: Path | None = None,
) -> DogDocument:
    """Helper to create test documents."""
    return DogDocument(
        file_path=file_path or Path(f"/test/{name.lower()}.dog.md"),
        primitive_type=ptype,
        name=name,
        sections=[Section(name=s, content="content", line_number=i + 2) for i, s in enumerate(sections or [])],
        references=[InlineReference(name=n, ref_type=t, line_number=10) for n, t in (references or [])],
        raw_content=f"# {ptype.value}: {name}\n",
    )


class TestLintDocuments:
    @pytest.mark.asyncio
    async def test_valid_documents(self) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR, ["Description", "Notes"]),
            make_doc("Login", PrimitiveType.BEHAVIOR, ["Condition", "Description"]),
        ]

        result = await lint_documents(docs)
        assert not result.has_errors
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_invalid_section(self) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR, ["Description", "InvalidSection"]),
        ]

        result = await lint_documents(docs)
        assert len(result.warnings) == 1
        assert "InvalidSection" in result.warnings[0].message
        assert "not allowed" in result.warnings[0].message

    @pytest.mark.asyncio
    async def test_valid_reference(self) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                references=[("User", PrimitiveType.ACTOR)],
            ),
        ]

        result = await lint_documents(docs)
        assert not result.has_errors
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_unknown_reference(self) -> None:
        docs = [
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                references=[("NonExistent", PrimitiveType.ACTOR)],
            ),
        ]

        result = await lint_documents(docs)
        assert len(result.warnings) == 1
        assert "Unknown" in result.warnings[0].message
        assert "NonExistent" in result.warnings[0].message

    @pytest.mark.asyncio
    async def test_wrong_reference_type(self) -> None:
        docs = [
            make_doc("User", PrimitiveType.ACTOR),
            make_doc(
                "Login",
                PrimitiveType.BEHAVIOR,
                # User is an Actor but referenced as Component
                references=[("User", PrimitiveType.COMPONENT)],
            ),
        ]

        result = await lint_documents(docs)
        assert result.has_errors
        assert len(result.errors) == 1
        assert "annotated as Component" in result.errors[0].message
        assert "exists as Actor" in result.errors[0].message

    @pytest.mark.asyncio
    async def test_project_allowed_sections(self) -> None:
        docs = [
            make_doc(
                "MyApp",
                PrimitiveType.PROJECT,
                ["Description", "Actors", "Behaviors", "Components", "Data", "Notes"],
            ),
        ]

        result = await lint_documents(docs)
        assert not result.has_errors
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_component_allowed_sections(self) -> None:
        docs = [
            make_doc(
                "Auth",
                PrimitiveType.COMPONENT,
                ["Description", "State", "Events", "Notes"],
            ),
        ]

        result = await lint_documents(docs)
        assert not result.has_errors
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_data_allowed_sections(self) -> None:
        docs = [
            make_doc(
                "Credentials",
                PrimitiveType.DATA,
                ["Description", "Fields", "Notes"],
            ),
        ]

        result = await lint_documents(docs)
        assert not result.has_errors
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_duplicate_file_names(self) -> None:
        """Duplicate file names should produce warnings."""
        docs = [
            make_doc(
                "User",
                PrimitiveType.ACTOR,
                file_path=Path("/docs/actors/user.dog.md"),
            ),
            make_doc(
                "UserData",
                PrimitiveType.DATA,
                file_path=Path("/docs/data/user.dog.md"),
            ),
        ]

        result = await lint_documents(docs)
        assert len(result.warnings) == 2
        assert "Duplicate file name 'user.dog.md'" in result.warnings[0].message
        assert "Duplicate file name 'user.dog.md'" in result.warnings[1].message

    @pytest.mark.asyncio
    async def test_no_duplicate_warning_for_unique_names(self) -> None:
        """Unique file names should not produce warnings."""
        docs = [
            make_doc(
                "User",
                PrimitiveType.ACTOR,
                file_path=Path("/docs/actors/user.dog.md"),
            ),
            make_doc(
                "Order",
                PrimitiveType.DATA,
                file_path=Path("/docs/data/order.dog.md"),
            ),
        ]

        result = await lint_documents(docs)
        assert len(result.warnings) == 0

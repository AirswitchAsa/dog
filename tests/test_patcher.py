from pathlib import Path

import pytest
import pytest_asyncio

from dog_core import PrimitiveType, parse_documents
from dog_core.patcher import PatchData, PatchResult, patch_document


@pytest_asyncio.fixture
async def parsed_docs(tmp_path: Path) -> list:
    """Create and parse sample documents for patcher testing."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Actor
    (docs_dir / "user.dog.md").write_text("""# Actor: User

## Description

A human user who interacts with the system.

## Notes

- Primary actor
""")

    # Behavior
    (docs_dir / "login.dog.md").write_text("""# Behavior: Login Flow

## Condition

- `@User` has credentials

## Description

The `@User` authenticates via `#AuthService`.

## Outcome

- Session created

## Notes

- Requires HTTPS
""")

    files = list(docs_dir.glob("*.dog.md"))
    return await parse_documents(files)


class TestPatchData:
    def test_empty_sections(self) -> None:
        patch = PatchData()
        assert patch.sections == {}

    def test_with_sections(self) -> None:
        patch = PatchData(sections={"Description": "New content"})
        assert patch.sections["Description"] == "New content"


class TestPatchResult:
    def test_success_result(self) -> None:
        result = PatchResult(
            file_path="/path/to/file.dog.md",
            updated_sections=["Description"],
            success=True,
        )
        assert result.success is True
        assert result.error is None
        assert "Description" in result.updated_sections

    def test_error_result(self) -> None:
        result = PatchResult(
            file_path="",
            updated_sections=[],
            success=False,
            error="Document not found",
        )
        assert result.success is False
        assert result.error == "Document not found"


class TestPatchDocument:
    @pytest.mark.asyncio
    async def test_patch_existing_section(self, parsed_docs: list) -> None:
        patch = PatchData(sections={"Description": "Updated description"})
        result = await patch_document(parsed_docs, "User", patch)

        assert result.success is True
        assert "Description" in result.updated_sections

        # Verify file was updated
        content = Path(result.file_path).read_text()
        assert "Updated description" in content

    @pytest.mark.asyncio
    async def test_patch_with_type_filter(self, parsed_docs: list) -> None:
        patch = PatchData(sections={"Description": "Filtered update"})
        result = await patch_document(parsed_docs, "User", patch, type_filter=PrimitiveType.ACTOR)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_patch_wrong_type_filter(self, parsed_docs: list) -> None:
        patch = PatchData(sections={"Description": "Should fail"})
        result = await patch_document(parsed_docs, "User", patch, type_filter=PrimitiveType.COMPONENT)

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_patch_not_found(self, parsed_docs: list) -> None:
        patch = PatchData(sections={"Description": "test"})
        result = await patch_document(parsed_docs, "NonExistent", patch)

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_patch_invalid_section(self, parsed_docs: list) -> None:
        # Actors only allow Description and Notes
        patch = PatchData(sections={"Outcome": "Invalid for Actor"})
        result = await patch_document(parsed_docs, "User", patch)

        assert result.success is False
        assert result.error is not None
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_patch_empty_sections(self, parsed_docs: list) -> None:
        # Empty sections dict should fail
        patch = PatchData(sections={})
        result = await patch_document(parsed_docs, "User", patch)

        assert result.success is False
        assert result.error is not None
        assert "no sections" in result.error.lower()

    @pytest.mark.asyncio
    async def test_patch_multiple_sections(self, parsed_docs: list) -> None:
        patch = PatchData(
            sections={
                "Description": "New description",
                "Notes": "New notes",
            }
        )
        result = await patch_document(parsed_docs, "User", patch)

        assert result.success is True
        assert "Description" in result.updated_sections
        assert "Notes" in result.updated_sections

    @pytest.mark.asyncio
    async def test_patch_behavior_sections(self, parsed_docs: list) -> None:
        # Behaviors allow Condition, Description, Outcome, Notes
        patch = PatchData(
            sections={
                "Outcome": "Updated outcome",
            }
        )
        result = await patch_document(parsed_docs, "Login Flow", patch)

        assert result.success is True
        assert "Outcome" in result.updated_sections

    @pytest.mark.asyncio
    async def test_patch_case_insensitive(self, parsed_docs: list) -> None:
        patch = PatchData(sections={"Description": "Case test"})
        result = await patch_document(parsed_docs, "user", patch)

        assert result.success is True

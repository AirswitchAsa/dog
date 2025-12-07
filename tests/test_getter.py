from pathlib import Path

import pytest
import pytest_asyncio

from dog_core import PrimitiveType, parse_documents
from dog_core.getter import GetResult, ResolvedReference, get_document, list_documents


@pytest_asyncio.fixture
async def parsed_docs(tmp_path: Path) -> list:
    """Create and parse sample documents for getter testing."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Actor
    (docs_dir / "user.dog.md").write_text("""# Actor: User

## Description

A human user who interacts with the system.

## Notes

- Primary actor
""")

    # Component
    (docs_dir / "auth.dog.md").write_text("""# Component: AuthService

## Description

Handles authentication and authorization.

## State

- authenticated: boolean

## Notes

- Uses JWT tokens
""")

    # Behavior with references
    (docs_dir / "login.dog.md").write_text("""# Behavior: Login Flow

## Condition

- `@User` has credentials

## Description

The `@User` authenticates via `#AuthService` using `&Credentials`.

## Outcome

- Session created

## Notes

- Requires HTTPS
""")

    # Data
    (docs_dir / "credentials.dog.md").write_text("""# Data: Credentials

## Description

User login credentials.

## Fields

- username: string
- password: string

## Notes

- Passwords are hashed
""")

    files = list(docs_dir.glob("*.dog.md"))
    return await parse_documents(files)


class TestResolvedReference:
    def test_to_dict_resolved(self) -> None:
        ref = ResolvedReference(
            name="User",
            ref_type=PrimitiveType.ACTOR,
            resolved=True,
            file_path="/path/to/user.dog.md",
        )
        d = ref.to_dict()
        assert d["name"] == "User"
        assert d["type"] == "Actor"
        assert d["resolved"] is True
        assert d["file"] == "/path/to/user.dog.md"

    def test_to_dict_unresolved(self) -> None:
        ref = ResolvedReference(
            name="Unknown",
            ref_type=PrimitiveType.ACTOR,
            resolved=False,
            file_path=None,
        )
        d = ref.to_dict()
        assert d["name"] == "Unknown"
        assert d["resolved"] is False
        assert d["file"] is None


class TestGetResult:
    def test_to_dict(self) -> None:
        result = GetResult(
            name="Test",
            primitive_type=PrimitiveType.ACTOR,
            file_path="/path/to/test.dog.md",
            sections=[{"name": "Description", "content": "Test desc"}],
            references=[
                ResolvedReference(
                    name="Other",
                    ref_type=PrimitiveType.COMPONENT,
                    resolved=True,
                    file_path="/path/to/other.dog.md",
                )
            ],
            raw_content="# Actor: Test\n\n## Description\n\nTest desc",
        )
        d = result.to_dict()
        assert d["name"] == "Test"
        assert d["type"] == "Actor"
        assert d["file"] == "/path/to/test.dog.md"
        assert len(d["sections"]) == 1
        assert len(d["references"]) == 1
        assert d["content"] == "# Actor: Test\n\n## Description\n\nTest desc"

    def test_to_text_with_references(self) -> None:
        result = GetResult(
            name="Test",
            primitive_type=PrimitiveType.ACTOR,
            file_path="/path/to/test.dog.md",
            sections=[{"name": "Description", "content": "Test desc"}],
            references=[
                ResolvedReference(
                    name="Resolved",
                    ref_type=PrimitiveType.COMPONENT,
                    resolved=True,
                    file_path="/path/to/resolved.dog.md",
                ),
                ResolvedReference(
                    name="Unresolved",
                    ref_type=PrimitiveType.ACTOR,
                    resolved=False,
                    file_path=None,
                ),
            ],
            raw_content="# Actor: Test\n\n## Description\n\nTest desc",
        )
        text = result.to_text()
        assert "# Actor: Test" in text
        assert "Resolved References" in text
        assert "Unresolved References" in text
        assert "Resolved" in text
        assert "Unresolved" in text

    def test_to_text_no_references(self) -> None:
        result = GetResult(
            name="Test",
            primitive_type=PrimitiveType.ACTOR,
            file_path="/path/to/test.dog.md",
            sections=[],
            references=[],
            raw_content="# Actor: Test",
        )
        text = result.to_text()
        assert "# Actor: Test" in text
        assert "References" not in text


class TestGetDocument:
    @pytest.mark.asyncio
    async def test_get_by_exact_name(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "User")
        assert result is not None
        assert result.name == "User"
        assert result.primitive_type == PrimitiveType.ACTOR

    @pytest.mark.asyncio
    async def test_get_case_insensitive(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "user")
        assert result is not None
        assert result.name == "User"

    @pytest.mark.asyncio
    async def test_get_with_type_filter(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "User", type_filter=PrimitiveType.ACTOR)
        assert result is not None
        assert result.primitive_type == PrimitiveType.ACTOR

    @pytest.mark.asyncio
    async def test_get_with_wrong_type_filter(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "User", type_filter=PrimitiveType.COMPONENT)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_not_found(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "NonExistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_resolved_references(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "Login Flow")
        assert result is not None

        # Should have references to User, AuthService, Credentials
        ref_names = [r.name for r in result.references]
        assert "User" in ref_names
        assert "AuthService" in ref_names
        assert "Credentials" in ref_names

        # All should be resolved since they exist
        for ref in result.references:
            assert ref.resolved is True
            assert ref.file_path is not None

    @pytest.mark.asyncio
    async def test_get_with_unresolved_references(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "unresolved"
        docs_dir.mkdir()

        # Behavior referencing non-existent primitives
        (docs_dir / "orphan.dog.md").write_text("""# Behavior: Orphan

## Description

References `@NonExistent` actor and `#MissingComponent`.

## Outcome

- Nothing
""")

        files = list(docs_dir.glob("*.dog.md"))
        docs = await parse_documents(files)

        result = await get_document(docs, "Orphan")
        assert result is not None

        # References should be unresolved
        for ref in result.references:
            assert ref.resolved is False
            assert ref.file_path is None

    @pytest.mark.asyncio
    async def test_get_includes_sections(self, parsed_docs: list) -> None:
        result = await get_document(parsed_docs, "AuthService")
        assert result is not None

        section_names = [s["name"] for s in result.sections]
        assert "Description" in section_names
        assert "State" in section_names
        assert "Notes" in section_names


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_list_all(self, parsed_docs: list) -> None:
        results = await list_documents(parsed_docs)
        assert len(results) == 4  # User, AuthService, Login Flow, Credentials

    @pytest.mark.asyncio
    async def test_list_by_type(self, parsed_docs: list) -> None:
        results = await list_documents(parsed_docs, type_filter=PrimitiveType.ACTOR)
        assert len(results) == 1
        assert results[0]["name"] == "User"
        assert results[0]["type"] == "Actor"

    @pytest.mark.asyncio
    async def test_list_sorted(self, parsed_docs: list) -> None:
        results = await list_documents(parsed_docs)
        # Should be sorted by type, then name
        types = [r["type"] for r in results]
        # Verify it's sorted
        assert types == sorted(types)

    @pytest.mark.asyncio
    async def test_list_empty_with_filter(self, parsed_docs: list) -> None:
        results = await list_documents(parsed_docs, type_filter=PrimitiveType.PROJECT)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_list_result_structure(self, parsed_docs: list) -> None:
        results = await list_documents(parsed_docs)
        for r in results:
            assert "name" in r
            assert "type" in r
            assert "file" in r

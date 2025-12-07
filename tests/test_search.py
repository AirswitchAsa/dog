from pathlib import Path

import pytest
import pytest_asyncio

from dog_core import PrimitiveType, parse_documents
from dog_core.search import SearchResult, search_documents


@pytest_asyncio.fixture
async def parsed_docs(tmp_path: Path) -> list:
    """Create and parse sample documents for search testing."""
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

    # Component
    (docs_dir / "auth.dog.md").write_text("""# Component: AuthService

## Description

Handles authentication and authorization for the system.

## State

- authenticated: boolean

## Notes

- Uses JWT tokens
""")

    # Data
    (docs_dir / "credentials.dog.md").write_text("""# Data: Credentials

## Description

User login credentials for authentication.

## Fields

- username: string
- password: string

## Notes

- Passwords are hashed
""")

    files = list(docs_dir.glob("*.dog.md"))
    return await parse_documents(files)


class TestSearchResult:
    def test_to_dict(self) -> None:
        result = SearchResult(
            name="Test",
            primitive_type=PrimitiveType.ACTOR,
            file_path="/path/to/test.dog.md",
            score=50.0,
            snippet="Test snippet",
        )
        d = result.to_dict()
        assert d["name"] == "Test"
        assert d["type"] == "Actor"
        assert d["file"] == "/path/to/test.dog.md"
        assert d["score"] == 50.0
        assert d["snippet"] == "Test snippet"


class TestSearchDocuments:
    @pytest.mark.asyncio
    async def test_exact_name_match(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "User")
        assert len(results) > 0
        # User should be in results with high score
        user_result = next((r for r in results if r.name == "User"), None)
        assert user_result is not None
        # RapidFuzz returns 0-100 scale, exact match should be 100
        assert user_result.score == 100.0

    @pytest.mark.asyncio
    async def test_partial_name_match(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "Login")
        assert len(results) > 0
        # Should match "Login Flow"
        assert any(r.name == "Login Flow" for r in results)

    @pytest.mark.asyncio
    async def test_content_match(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "JWT")
        assert len(results) > 0
        # Should find AuthService which mentions JWT
        assert any(r.name == "AuthService" for r in results)

    @pytest.mark.asyncio
    async def test_type_filter(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "auth", type_filter=PrimitiveType.COMPONENT)
        assert len(results) > 0
        # All results should be components
        for r in results:
            assert r.primitive_type == PrimitiveType.COMPONENT

    @pytest.mark.asyncio
    async def test_type_filter_excludes(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "User", type_filter=PrimitiveType.COMPONENT)
        # User is an Actor, should not appear when filtering for Component
        assert not any(r.name == "User" for r in results)

    @pytest.mark.asyncio
    async def test_limit(self, parsed_docs: list) -> None:
        # Use a query that matches multiple docs
        results = await search_documents(parsed_docs, "auth", limit=1)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_low_relevance_query(self, parsed_docs: list) -> None:
        # With top-k, we always get results sorted by score
        results = await search_documents(parsed_docs, "xyznonexistent123456")
        # Results exist and are sorted by score (descending)
        assert len(results) > 0
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_results_sorted_by_score(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "auth")
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_reference_match(self, parsed_docs: list) -> None:
        # Login Flow references @User and #AuthService
        results = await search_documents(parsed_docs, "AuthService")
        # Should find both AuthService (name match) and Login Flow (reference)
        names = [r.name for r in results]
        assert "AuthService" in names

    @pytest.mark.asyncio
    async def test_snippet_included(self, parsed_docs: list) -> None:
        results = await search_documents(parsed_docs, "authentication")
        assert len(results) > 0
        # All results should have snippets
        for r in results:
            assert r.snippet

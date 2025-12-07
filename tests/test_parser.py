from pathlib import Path

import pytest

from dog_core import PrimitiveType, parse_document
from dog_core.parser import ParseError, _extract_references, _parse_header


class TestParseHeader:
    def test_valid_project(self) -> None:
        result = _parse_header("# Project: MyApp")
        assert result == (PrimitiveType.PROJECT, "MyApp")

    def test_valid_actor(self) -> None:
        result = _parse_header("# Actor: User")
        assert result == (PrimitiveType.ACTOR, "User")

    def test_valid_behavior(self) -> None:
        result = _parse_header("# Behavior: Login Flow")
        assert result == (PrimitiveType.BEHAVIOR, "Login Flow")

    def test_valid_component(self) -> None:
        result = _parse_header("# Component: AuthService")
        assert result == (PrimitiveType.COMPONENT, "AuthService")

    def test_valid_data(self) -> None:
        result = _parse_header("# Data: UserCredentials")
        assert result == (PrimitiveType.DATA, "UserCredentials")

    def test_invalid_type(self) -> None:
        result = _parse_header("# Unknown: Something")
        assert result is None

    def test_missing_colon(self) -> None:
        result = _parse_header("# Actor User")
        assert result is None

    def test_h2_header(self) -> None:
        result = _parse_header("## Actor: User")
        assert result is None


class TestExtractReferences:
    def test_actor_reference(self) -> None:
        refs = _extract_references("The `@User` logs in.")
        assert len(refs) == 1
        assert refs[0].name == "User"
        assert refs[0].ref_type == PrimitiveType.ACTOR

    def test_behavior_reference(self) -> None:
        refs = _extract_references("Triggers `!Login Flow`.")
        assert len(refs) == 1
        assert refs[0].name == "Login Flow"
        assert refs[0].ref_type == PrimitiveType.BEHAVIOR

    def test_component_reference(self) -> None:
        refs = _extract_references("Uses `#AuthService`.")
        assert len(refs) == 1
        assert refs[0].name == "AuthService"
        assert refs[0].ref_type == PrimitiveType.COMPONENT

    def test_data_reference(self) -> None:
        refs = _extract_references("Stores `&UserCredentials`.")
        assert len(refs) == 1
        assert refs[0].name == "UserCredentials"
        assert refs[0].ref_type == PrimitiveType.DATA

    def test_multiple_references(self) -> None:
        content = "The `@User` submits `&Credentials` to `#AuthService`."
        refs = _extract_references(content)
        assert len(refs) == 3

        types = {r.ref_type for r in refs}
        assert PrimitiveType.ACTOR in types
        assert PrimitiveType.DATA in types
        assert PrimitiveType.COMPONENT in types

    def test_line_numbers(self) -> None:
        content = "Line 1\n`@User` on line 2\nLine 3\n`!Behavior` on line 4"
        refs = _extract_references(content)

        user_ref = next(r for r in refs if r.name == "User")
        behavior_ref = next(r for r in refs if r.name == "Behavior")

        assert user_ref.line_number == 2
        assert behavior_ref.line_number == 4

    def test_regular_backticks_ignored(self) -> None:
        refs = _extract_references("Use `code` and `another code` normally.")
        assert len(refs) == 0

    def test_regular_markdown_ignored(self) -> None:
        refs = _extract_references("Use *italic*, **bold**, and ***bold italic***.")
        assert len(refs) == 0


class TestParseDocument:
    @pytest.mark.asyncio
    async def test_parse_actor(self, tmp_path: Path, sample_actor: str) -> None:
        file_path = tmp_path / "user.dog.md"
        file_path.write_text(sample_actor)

        doc = await parse_document(file_path)

        assert doc.primitive_type == PrimitiveType.ACTOR
        assert doc.name == "User"
        assert len(doc.sections) == 2
        assert doc.sections[0].name == "Description"
        assert doc.sections[1].name == "Notes"

    @pytest.mark.asyncio
    async def test_parse_behavior_with_references(self, tmp_path: Path, sample_behavior: str) -> None:
        file_path = tmp_path / "login.dog.md"
        file_path.write_text(sample_behavior)

        doc = await parse_document(file_path)

        assert doc.primitive_type == PrimitiveType.BEHAVIOR
        assert doc.name == "Login"
        assert len(doc.sections) == 4

        # Check references were extracted
        ref_names = {r.name for r in doc.references}
        assert "User" in ref_names
        assert "AuthComponent" in ref_names
        assert "UserCredentials" in ref_names
        assert "Dashboard View" in ref_names

    @pytest.mark.asyncio
    async def test_parse_invalid_header(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.dog.md"
        file_path.write_text("# Invalid Header\n\nSome content")

        with pytest.raises(ParseError):
            await parse_document(file_path)

    @pytest.mark.asyncio
    async def test_parse_empty_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "empty.dog.md"
        file_path.write_text("")

        with pytest.raises(ParseError):
            await parse_document(file_path)

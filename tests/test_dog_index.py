from pathlib import Path

import pytest

from dog_core.dog_index import AmbiguousLookupError, DogIndex, PrimitiveKey, ensure_index
from dog_core.models import DogDocument, InlineReference, PrimitiveType, Section


def make_doc(
    name: str,
    ptype: PrimitiveType,
    file_path: Path,
    references: list[tuple[str, PrimitiveType, int]] | None = None,
) -> DogDocument:
    return DogDocument(
        file_path=file_path,
        primitive_type=ptype,
        name=name,
        sections=[Section(name="Description", content="content", line_number=3)],
        references=[InlineReference(name=n, ref_type=t, line_number=ln) for n, t, ln in (references or [])],
        raw_content=f"# {ptype.value}: {name}\n\n## Description\n\ncontent\n",
    )


class TestDogIndex:
    def test_normalization_helpers(self) -> None:
        assert DogIndex.normalize_name("  Login   Flow ") == "login flow"
        assert DogIndex.normalize_file_stem("login-flow.dog.md") == "login-flow"
        assert DogIndex.normalize_file_stem("guide.md") == "guide"
        assert DogIndex.sigil_for(PrimitiveType.COMPONENT) == "#"
        assert DogIndex.sigil_for(PrimitiveType.PROJECT) == ""

    @pytest.mark.asyncio
    async def test_from_path_loads_documents(self, tmp_path: Path) -> None:
        file_path = tmp_path / "user.dog.md"
        file_path.write_text("# Actor: User\n\n## Description\n\ncontent\n\n## Notes\n\nnote\n")

        index = await DogIndex.from_path(tmp_path)
        resolved = index.resolve("USER", PrimitiveType.ACTOR)

        assert len(index.documents) == 1
        assert resolved is not None
        assert resolved.name == "User"

    def test_lookup_graph_and_filters(self, tmp_path: Path) -> None:
        actor = make_doc("User", PrimitiveType.ACTOR, tmp_path / "user.dog.md")
        behavior = make_doc(
            "Login",
            PrimitiveType.BEHAVIOR,
            tmp_path / "login.dog.md",
            references=[("User", PrimitiveType.ACTOR, 8)],
        )

        index = DogIndex.from_documents([behavior, actor], root_path=tmp_path)

        assert index.root_path == tmp_path
        resolved_login = index.resolve("login")
        resolved_user = index.resolve_file_stem("user")
        assert resolved_login is not None
        assert resolved_user is not None
        assert resolved_login.name == "Login"
        assert resolved_user.name == "User"
        assert index.resolve("Missing") is None
        assert index.resolve_file_stem("missing") is None
        assert index.references_from(behavior)[0].target == actor
        assert index.references_to("User")[0].source == behavior
        assert index.references_to("User", PrimitiveType.ACTOR)[0].reference.line_number == 8
        assert index.documents_of_type(PrimitiveType.ACTOR) == [actor]
        assert index.by_key[PrimitiveKey(PrimitiveType.ACTOR, "user")] == [actor]
        assert ensure_index(index) is index
        assert len(ensure_index([actor]).documents) == 1

    def test_ambiguity_detection(self, tmp_path: Path) -> None:
        actor = make_doc("Thing", PrimitiveType.ACTOR, tmp_path / "same.dog.md")
        data = make_doc("Thing", PrimitiveType.DATA, tmp_path / "nested" / "same.dog.md")
        duplicate_actor = make_doc("Thing", PrimitiveType.ACTOR, tmp_path / "thing.dog.md")

        index = DogIndex.from_documents([actor, data, duplicate_actor])

        assert index.all_duplicates()
        assert index.ambiguous_names()
        assert index.ambiguous_file_stems()
        with pytest.raises(AmbiguousLookupError) as lookup_error:
            index.resolve("Thing")
        assert "Actor: Thing" in str(lookup_error.value)
        with pytest.raises(AmbiguousLookupError):
            index.resolve_file_stem("same")

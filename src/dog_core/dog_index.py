from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from dog_core.finder import find_dog_files
from dog_core.models import SIGIL_MAP, DogDocument, InlineReference, PrimitiveType
from dog_core.parser import parse_documents


@dataclass(frozen=True)
class PrimitiveKey:
    """Normalized identity for a DOG primitive."""

    primitive_type: PrimitiveType
    name: str


@dataclass(frozen=True)
class ReferenceOccurrence:
    """A reference emitted by one DOG document."""

    source: DogDocument
    reference: InlineReference
    target: DogDocument | None


@dataclass(frozen=True)
class SearchEntry:
    """Normalized fields used by the local searcher."""

    document: DogDocument
    normalized_name: str
    sections: dict[str, str]
    references: tuple[InlineReference, ...]


class AmbiguousLookupError(Exception):
    """Raised when a name resolves to multiple DOG primitives."""

    def __init__(self, name: str, matches: list[DogDocument]) -> None:
        self.name = name
        self.matches = matches
        labels = ", ".join(f"{doc.primitive_type.value}: {doc.name}" for doc in matches)
        super().__init__(f"Ambiguous primitive name '{name}': {labels}")


class DogIndex:
    """In-memory DOG knowledge model for one CLI invocation or server reload."""

    def __init__(self, root_path: Path, documents: list[DogDocument]) -> None:
        self.root_path = root_path
        self.documents = sorted(
            documents,
            key=lambda doc: (doc.primitive_type.value, self.normalize_name(doc.name), str(doc.file_path)),
        )
        self.by_key: dict[PrimitiveKey, list[DogDocument]] = defaultdict(list)
        self.by_name: dict[str, list[DogDocument]] = defaultdict(list)
        self.by_file_stem: dict[str, list[DogDocument]] = defaultdict(list)
        self.refs_from: dict[PrimitiveKey, list[ReferenceOccurrence]] = defaultdict(list)
        self.refs_to: dict[PrimitiveKey, list[ReferenceOccurrence]] = defaultdict(list)
        self.search_entries: list[SearchEntry] = []
        self._build()

    @classmethod
    async def from_path(cls, path: Path) -> DogIndex:
        files = await find_dog_files(path)
        documents = await parse_documents(files) if files else []
        return cls(path, documents)

    @classmethod
    def from_documents(cls, documents: list[DogDocument], root_path: Path | None = None) -> DogIndex:
        return cls(root_path or Path("."), documents)

    @staticmethod
    def normalize_name(name: str) -> str:
        return " ".join(name.strip().lower().split())

    @staticmethod
    def normalize_file_stem(path: Path | str) -> str:
        stem = Path(path).name
        if stem.endswith(".dog.md"):
            stem = stem[: -len(".dog.md")]
        elif stem.endswith(".md"):
            stem = stem[: -len(".md")]
        return DogIndex.normalize_name(stem)

    @staticmethod
    def sigil_for(primitive_type: PrimitiveType) -> str:
        for sigil, ptype in SIGIL_MAP.items():
            if ptype == primitive_type:
                return sigil
        return ""

    def key_for(self, doc: DogDocument) -> PrimitiveKey:
        return PrimitiveKey(doc.primitive_type, self.normalize_name(doc.name))

    def ref_key(self, ref: InlineReference) -> PrimitiveKey:
        return PrimitiveKey(ref.ref_type, self.normalize_name(ref.name))

    def _build(self) -> None:
        for doc in self.documents:
            key = self.key_for(doc)
            self.by_key[key].append(doc)
            self.by_name[key.name].append(doc)
            self.by_file_stem[self.normalize_file_stem(doc.file_path)].append(doc)
            self.search_entries.append(
                SearchEntry(
                    document=doc,
                    normalized_name=key.name,
                    sections={section.name: section.content for section in doc.sections},
                    references=tuple(doc.references),
                )
            )

        for doc in self.documents:
            source_key = self.key_for(doc)
            for ref in doc.references:
                target = self.resolve(ref.name, ref.ref_type, allow_ambiguous=True)
                occurrence = ReferenceOccurrence(source=doc, reference=ref, target=target)
                self.refs_from[source_key].append(occurrence)
                self.refs_to[self.ref_key(ref)].append(occurrence)

    def all_duplicates(self) -> list[tuple[PrimitiveKey, list[DogDocument]]]:
        return [(key, docs) for key, docs in self.by_key.items() if len(docs) > 1]

    def ambiguous_names(self) -> list[tuple[str, list[DogDocument]]]:
        return [(name, docs) for name, docs in self.by_name.items() if len(docs) > 1]

    def ambiguous_file_stems(self) -> list[tuple[str, list[DogDocument]]]:
        return [(stem, docs) for stem, docs in self.by_file_stem.items() if len(docs) > 1]

    def resolve(
        self,
        name: str,
        type_filter: PrimitiveType | None = None,
        *,
        allow_ambiguous: bool = False,
    ) -> DogDocument | None:
        normalized = self.normalize_name(name)
        matches = (
            list(self.by_key.get(PrimitiveKey(type_filter, normalized), []))
            if type_filter is not None
            else list(self.by_name.get(normalized, []))
        )

        if not matches:
            return None
        if len(matches) > 1 and not allow_ambiguous:
            raise AmbiguousLookupError(name, matches)
        return matches[0]

    def resolve_file_stem(self, file_stem: str) -> DogDocument | None:
        matches = list(self.by_file_stem.get(self.normalize_file_stem(file_stem), []))
        if not matches:
            return None
        if len(matches) > 1:
            raise AmbiguousLookupError(file_stem, matches)
        return matches[0]

    def resolve_reference(self, ref: InlineReference) -> DogDocument | None:
        return self.resolve(ref.name, ref.ref_type, allow_ambiguous=True)

    def references_from(self, doc: DogDocument) -> list[ReferenceOccurrence]:
        return list(self.refs_from.get(self.key_for(doc), []))

    def references_to(self, name: str, type_filter: PrimitiveType | None = None) -> list[ReferenceOccurrence]:
        normalized = self.normalize_name(name)
        if type_filter is not None:
            return list(self.refs_to.get(PrimitiveKey(type_filter, normalized), []))

        occurrences: list[ReferenceOccurrence] = []
        for key, refs in self.refs_to.items():
            if key.name == normalized:
                occurrences.extend(refs)
        return occurrences

    def documents_of_type(self, type_filter: PrimitiveType | None = None) -> list[DogDocument]:
        if type_filter is None:
            return list(self.documents)
        return [doc for doc in self.documents if doc.primitive_type == type_filter]


def ensure_index(index_or_docs: DogIndex | list[DogDocument]) -> DogIndex:
    if isinstance(index_or_docs, DogIndex):
        return index_or_docs
    return DogIndex.from_documents(index_or_docs)

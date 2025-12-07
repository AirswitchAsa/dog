from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class PrimitiveType(str, Enum):
    PROJECT = "Project"
    ACTOR = "Actor"
    BEHAVIOR = "Behavior"
    COMPONENT = "Component"
    DATA = "Data"


SIGIL_MAP: dict[str, PrimitiveType] = {
    "@": PrimitiveType.ACTOR,
    "!": PrimitiveType.BEHAVIOR,
    "#": PrimitiveType.COMPONENT,
    "&": PrimitiveType.DATA,
}


def parse_primitive_query(query: str) -> tuple[str, PrimitiveType | None]:
    """Parse a query string that may contain a primitive type sigil.

    Examples:
        "@User" -> ("User", PrimitiveType.ACTOR)
        "!Login" -> ("Login", PrimitiveType.BEHAVIOR)
        "User" -> ("User", None)
        "@" -> ("", PrimitiveType.ACTOR)  # for listing all of a type

    Returns:
        Tuple of (name, type_filter) where type_filter is None if no sigil present.
    """
    if query and query[0] in SIGIL_MAP:
        sigil = query[0]
        name = query[1:].strip()
        return name, SIGIL_MAP[sigil]
    return query, None


ALLOWED_SECTIONS: dict[PrimitiveType, set[str]] = {
    PrimitiveType.PROJECT: {
        "Description",
        "Actors",
        "Behaviors",
        "Components",
        "Data",
        "Notes",
    },
    PrimitiveType.ACTOR: {"Description", "Notes"},
    PrimitiveType.BEHAVIOR: {"Condition", "Description", "Outcome", "Notes"},
    PrimitiveType.COMPONENT: {"Description", "State", "Events", "Notes"},
    PrimitiveType.DATA: {"Description", "Fields", "Notes"},
}


class Section(BaseModel):
    name: str
    content: str
    line_number: int


class InlineReference(BaseModel):
    name: str
    ref_type: PrimitiveType
    line_number: int


class DogDocument(BaseModel):
    file_path: Path
    primitive_type: PrimitiveType
    name: str
    sections: list[Section]
    references: list[InlineReference]
    raw_content: str


class LintIssue(BaseModel):
    file_path: Path
    line_number: int | None
    message: str
    severity: Literal["error", "warning"]


class LintResult(BaseModel):
    issues: list[LintIssue]

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

from dog_core.finder import find_dog_files
from dog_core.formatter import format_content, format_file, format_file_in_place
from dog_core.getter import GetResult, ResolvedReference, get_document, list_documents
from dog_core.indexer import generate_index
from dog_core.linter import lint_documents
from dog_core.models import (
    ALLOWED_SECTIONS,
    DogDocument,
    InlineReference,
    LintIssue,
    LintResult,
    PrimitiveType,
    Section,
)
from dog_core.parser import ParseError, parse_document, parse_documents
from dog_core.search import SearchResult, search_documents


"""
dog-core package.
"""

__version__ = "2025.12.07"

__all__ = [
    "ALLOWED_SECTIONS",
    "DogDocument",
    "GetResult",
    "InlineReference",
    "LintIssue",
    "LintResult",
    "ParseError",
    "PrimitiveType",
    "ResolvedReference",
    "SearchResult",
    "Section",
    "find_dog_files",
    "format_content",
    "format_file",
    "format_file_in_place",
    "generate_index",
    "get_document",
    "lint_documents",
    "list_documents",
    "parse_document",
    "parse_documents",
    "search_documents",
]

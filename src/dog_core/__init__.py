from dog_core.export import export_documents
from dog_core.finder import find_dog_files
from dog_core.formatter import format_content, format_file, format_file_in_place
from dog_core.getter import GetResult, ResolvedReference, get_document, list_documents
from dog_core.graph import generate_graph
from dog_core.indexer import generate_index
from dog_core.linter import lint_documents
from dog_core.models import (
    ALLOWED_SECTIONS,
    SIGIL_MAP,
    DogDocument,
    InlineReference,
    LintIssue,
    LintResult,
    PrimitiveType,
    Section,
    parse_primitive_query,
)
from dog_core.parser import ParseError, parse_document, parse_documents
from dog_core.patcher import PatchData, PatchResult, patch_document
from dog_core.refs import RefResult, RefsResult, find_refs
from dog_core.search import SearchResult, search_documents
from dog_core.server import DocServer, create_server, run_server


"""
dog-core package.
"""

__version__ = "2025.12.7.post1"

__all__ = [
    "ALLOWED_SECTIONS",
    "SIGIL_MAP",
    "DocServer",
    "DogDocument",
    "GetResult",
    "InlineReference",
    "LintIssue",
    "LintResult",
    "ParseError",
    "PatchData",
    "PatchResult",
    "PrimitiveType",
    "RefResult",
    "RefsResult",
    "ResolvedReference",
    "SearchResult",
    "Section",
    "create_server",
    "export_documents",
    "find_dog_files",
    "find_refs",
    "format_content",
    "format_file",
    "format_file_in_place",
    "generate_graph",
    "generate_index",
    "get_document",
    "lint_documents",
    "list_documents",
    "parse_document",
    "parse_documents",
    "parse_primitive_query",
    "patch_document",
    "run_server",
    "search_documents",
]

from dog_core.dog_index import DogIndex, ensure_index
from dog_core.models import (
    ALLOWED_SECTIONS,
    DogDocument,
    LintIssue,
    LintResult,
    PrimitiveType,
)


REQUIRED_SECTIONS: dict[PrimitiveType, set[str]] = {
    PrimitiveType.PROJECT: {"Description", "Actors", "Behaviors", "Components", "Data", "Notes"},
    PrimitiveType.ACTOR: {"Description", "Notes"},
    PrimitiveType.BEHAVIOR: {"Condition", "Description", "Outcome", "Notes"},
    PrimitiveType.COMPONENT: {"Description", "State", "Events", "Notes"},
    PrimitiveType.DATA: {"Description", "Fields", "Notes"},
}


async def lint_documents(index_or_docs: DogIndex | list[DogDocument]) -> LintResult:  # noqa: C901
    """Lint a collection of DOG documents.

    Validates:
    - Sections are allowed for the primitive type
    - Inline references point to existing primitives
    - Referenced types match the annotation style
    - No duplicate file names (causes confusion in dog serve)

    Args:
        docs: List of parsed DogDocuments

    Returns:
        LintResult containing all issues found
    """
    index = ensure_index(index_or_docs)
    issues: list[LintIssue] = []

    # Check for duplicate file names
    for stem, docs in index.ambiguous_file_stems():
        for doc in docs:
            issues.append(
                LintIssue(
                    file_path=doc.file_path,
                    line_number=1,
                    message=f"Duplicate file name '{stem}.dog.md' also exists at: "
                    f"{', '.join(str(other.file_path) for other in docs if other.file_path != doc.file_path)}",
                    severity="warning",
                )
            )

    # Check for duplicate or cross-type names that make untyped lookup ambiguous.
    for normalized_name, docs in index.ambiguous_names():
        labels = ", ".join(f"{doc.primitive_type.value}: {doc.name} ({doc.file_path})" for doc in docs)
        for doc in docs:
            issues.append(
                LintIssue(
                    file_path=doc.file_path,
                    line_number=1,
                    message=f"Ambiguous primitive name '{normalized_name}': {labels}",
                    severity="error",
                )
            )

    # Validate each document
    for doc in index.documents:
        # Check sections
        allowed = ALLOWED_SECTIONS[doc.primitive_type]
        required = REQUIRED_SECTIONS[doc.primitive_type]
        sections_by_name = {section.name: section for section in doc.sections}

        for section_name in sorted(required - sections_by_name.keys()):
            issues.append(
                LintIssue(
                    file_path=doc.file_path,
                    line_number=1,
                    message=f"Missing required section '{section_name}' for {doc.primitive_type.value}",
                    severity="error",
                )
            )

        for section_name in sorted(required & sections_by_name.keys()):
            section = sections_by_name[section_name]
            if not section.content.strip():
                issues.append(
                    LintIssue(
                        file_path=doc.file_path,
                        line_number=section.line_number,
                        message=f"Required section '{section_name}' for {doc.primitive_type.value} is empty",
                        severity="error",
                    )
                )

        for section in doc.sections:
            if section.name not in allowed:
                issues.append(
                    LintIssue(
                        file_path=doc.file_path,
                        line_number=section.line_number,
                        message=f"Section '{section.name}' is not allowed for {doc.primitive_type.value}. "
                        f"Allowed sections: {', '.join(sorted(allowed))}",
                        severity="warning",
                    )
                )

        # Check inline references
        for ref in doc.references:
            if index.resolve_reference(ref) is None:
                # Check if the name exists as a different type
                found_type = None
                for candidate in index.by_name.get(index.normalize_name(ref.name), []):
                    if candidate.primitive_type != ref.ref_type:
                        found_type = candidate.primitive_type
                        break

                if found_type is not None:
                    issues.append(
                        LintIssue(
                            file_path=doc.file_path,
                            line_number=ref.line_number,
                            message=f"Reference '{ref.name}' is annotated as {ref.ref_type.value} "
                            f"but exists as {found_type.value}",
                            severity="error",
                        )
                    )
                else:
                    issues.append(
                        LintIssue(
                            file_path=doc.file_path,
                            line_number=ref.line_number,
                            message=f"Unknown {ref.ref_type.value} reference: '{ref.name}'",
                            severity="error",
                        )
                    )

    return LintResult(issues=issues)

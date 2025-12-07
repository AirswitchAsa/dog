from dog_core.models import (
    ALLOWED_SECTIONS,
    DogDocument,
    LintIssue,
    LintResult,
    PrimitiveType,
)


async def lint_documents(docs: list[DogDocument]) -> LintResult:
    """Lint a collection of DOG documents.

    Validates:
    - Sections are allowed for the primitive type
    - Inline references point to existing primitives
    - Referenced types match the annotation style

    Args:
        docs: List of parsed DogDocuments

    Returns:
        LintResult containing all issues found
    """
    issues: list[LintIssue] = []

    # Build index of all known primitives
    primitives: dict[PrimitiveType, set[str]] = {ptype: set() for ptype in PrimitiveType}

    for doc in docs:
        primitives[doc.primitive_type].add(doc.name)

    # Validate each document
    for doc in docs:
        # Check sections
        allowed = ALLOWED_SECTIONS[doc.primitive_type]
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
            if ref.name not in primitives[ref.ref_type]:
                # Check if the name exists as a different type
                found_type = None
                for ptype, names in primitives.items():
                    if ref.name in names:
                        found_type = ptype
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
                            severity="warning",
                        )
                    )

    return LintResult(issues=issues)

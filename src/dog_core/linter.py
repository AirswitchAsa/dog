from pathlib import Path

from dog_core.models import (
    ALLOWED_SECTIONS,
    DogDocument,
    LintIssue,
    LintResult,
    PrimitiveType,
)


async def lint_documents(docs: list[DogDocument]) -> LintResult:  # noqa: C901
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
    issues: list[LintIssue] = []

    # Build index of all known primitives
    primitives: dict[PrimitiveType, set[str]] = {ptype: set() for ptype in PrimitiveType}

    # Track file names to detect duplicates
    file_names: dict[str, list[str]] = {}  # name -> list of file paths

    for doc in docs:
        primitives[doc.primitive_type].add(doc.name)
        # Track by file stem (e.g., "user" from "user.dog.md")
        stem = doc.file_path.stem.removesuffix(".dog")
        if stem not in file_names:
            file_names[stem] = []
        file_names[stem].append(str(doc.file_path))

    # Check for duplicate file names
    for name, paths in file_names.items():
        if len(paths) > 1:
            for path in paths:
                issues.append(
                    LintIssue(
                        file_path=Path(path),
                        line_number=1,
                        message=f"Duplicate file name '{name}.dog.md' also exists at: "
                        f"{', '.join(p for p in paths if p != path)}",
                        severity="warning",
                    )
                )

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

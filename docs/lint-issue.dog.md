# Data: LintIssue

## Description

Represents a single validation issue found during linting. Contains location information and a human-readable message.

## Fields

- file_path: Path to the file with the issue
- line_number: line number where issue was found (optional)
- message: human-readable description of the issue
- severity: "error" or "warning"

## Notes

- Pydantic BaseModel for validation

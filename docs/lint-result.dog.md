# Data: LintResult

## Description

Contains the results of linting a collection of `&DogDocument` instances. Aggregates all issues found during validation.

## Fields

- issues: list of `&LintIssue` instances
- errors: computed property filtering severity="error"
- warnings: computed property filtering severity="warning"
- has_errors: boolean indicating if any errors exist

## Notes

- Pydantic BaseModel for validation

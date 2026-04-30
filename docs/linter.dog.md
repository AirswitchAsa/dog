# Component: Linter

## Description

Validates a `#DogIndex` against DOG specification rules. Checks section names and required sections per primitive type, validates inline references resolve to existing primitives with matching types, and detects ambiguous primitive identity.

## State

- index: `#DogIndex` being validated
- issues: list of `&LintIssue` instances

## Events

- validation_complete

## Notes

- Lint is strict by default
- Missing required sections produce errors
- Empty required sections produce errors
- Invalid section names produce warnings
- Type mismatches produce errors
- Unknown references produce errors
- Duplicate primitive names produce errors when lookup would be ambiguous

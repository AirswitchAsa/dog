# Component: Linter

## Description

Validates parsed `&DogDocument` instances against DOG specification rules. Checks section names against allowed lists per primitive type and validates inline references resolve to existing primitives with matching types.

## State

- primitives_index: mapping of primitive types to known names
- issues: list of `&LintIssue` instances

## Events

- validation_complete

## Notes

- Section violations produce warnings
- Type mismatches produce errors
- Unknown references produce warnings

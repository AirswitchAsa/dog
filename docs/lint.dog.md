# Behavior: Lint

## Condition

- `@User` has one or more `.dog.md` files to validate
- `@User` provides a path to a file or directory

## Description

The `@User` runs the `dog lint` command with a path argument. The `#CLI` builds a `#DogIndex` from all `.dog.md` files found at the path, then invokes `#Linter` for strict validation.

The `#Linter` checks:
- Section names are valid for each primitive type
- Required sections are present for each primitive type
- Required sections are not empty
- Primitive names are unique enough for unambiguous lookup
- Inline references (``` @actor ```, ``` !behavior ```, ``` #component ```, ``` &data ```) point to existing primitives
- Reference types match their sigil annotation
- File names do not create ambiguous serve routes

Results are displayed with file paths, line numbers, and severity levels (error/warning).

## Outcome

- Valid files: success message displayed
- Invalid files: errors and warnings listed with locations
- Exit code 0 if no errors, 1 if errors found
- JSON output available with `-o/--output json`

## Notes

- Lint is strict by default
- Unknown references produce errors
- Type mismatches (e.g., Actor referenced as Component) produce errors
- Missing required sections produce errors
- Empty required sections produce errors
- Orphaned but otherwise valid primitives may produce warnings

# Behavior: Lint

## Condition

- `@User` has one or more `.dog.md` files to validate
- `@User` provides a path to a file or directory

## Description

The `@User` runs the `dog lint` command with a path argument. The `#CLI` invokes `#Parser` to parse all `.dog.md` files found at the path, then passes the parsed `&DogDocument` instances to `#Linter` for validation.

The `#Linter` checks:
- Section names are valid for each primitive type
- Inline references (``` @actor ```, ``` !behavior ```, ``` #component ```, ``` &data ```) point to existing primitives
- Reference types match their sigil annotation

Results are displayed with file paths, line numbers, and severity levels (error/warning).

## Outcome

- Valid files: success message displayed
- Invalid files: errors and warnings listed with locations
- Exit code 0 if no errors, 1 if errors found

## Notes

- Unknown references produce warnings, not errors
- Type mismatches (e.g., Actor referenced as Component) produce errors

# Behavior: Get

## Condition

- `@User` wants to retrieve a specific DOG document by name
- `@User` provides the document name

## Description

The `@User` runs the `dog get` command with a document name. The `#CLI` invokes `#Getter` to find the matching `&DogDocument` and resolve all inline references.

Reference resolution shows:
- Resolved references with their file paths
- Unresolved references that point to missing documents

## Outcome

- Full document content displayed with resolved references
- Exit code 0 if found, 1 if not found
- Optional type filtering
- Supports text or JSON output formats

## Notes

- Name matching is case-insensitive
- Use `--type` to filter by primitive type
- Use `--output json` for programmatic consumption

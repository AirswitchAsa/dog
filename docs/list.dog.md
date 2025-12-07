# Behavior: List

## Condition

- `@User` wants to see all DOG documents in a directory
- `@User` optionally wants to filter by primitive type

## Description

The `@User` runs the `dog list` command. The `#CLI` invokes `#Getter` to enumerate all `&DogDocument` instances and group them by type.

## Outcome

- Documents displayed grouped by primitive type
- Each entry shows name and file path
- Optional type filtering
- Supports text or JSON output formats

## Notes

- Results are sorted by type, then by name
- Use `--type` to filter by primitive type
- Use `--output json` for programmatic consumption

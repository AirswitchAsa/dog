# Behavior: List

## Condition

- `@User` wants to see all DOG documents in a directory
- `@User` optionally wants to filter by primitive type

## Description

The `@User` runs the `dog list` command. The `#CLI` builds a `#DogIndex` and invokes `#Getter` to enumerate all `&DogDocument` instances and group them by type.

## Outcome

- JSON document list returned by default
- Text output available with `-o/--output text`
- Documents grouped by primitive type in text output
- Each entry shows name and file path
- Type filtering via sigil argument

## Notes

- Results are sorted by type, then by name
- Use sigil to filter by type: `@` (Actor), `!` (Behavior), `#` (Component), `&` (Data)

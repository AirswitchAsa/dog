# Behavior: Export

## Condition

- `@User` wants to export all DOG documents as structured JSON
- `@User` optionally filters by primitive type

## Description

The `@User` runs the `dog export` command. The `#CLI` exports all `&DogDocument` instances as a JSON array containing full document data.

Export includes for each document:
- name and type
- file path
- all sections with content
- all references with line numbers
- raw markdown content (optional)

## Outcome

- JSON object with documents array and count
- Documents sorted by type then name
- Type filtering via `--type` option with sigil
- Raw content can be excluded with `--no-raw`

## Notes

- Useful for feeding context to AI agents
- Example: `dog export -p docs/ > context.json`
- Always outputs JSON (no text format option)

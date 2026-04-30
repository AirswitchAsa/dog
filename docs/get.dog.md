# Behavior: Get

## Condition

- `@User` wants to retrieve a specific DOG document by name
- `@User` provides the document name

## Description

The `@User` runs the `dog get` command with a document name. The `#CLI` builds a `#DogIndex` and invokes `#Getter` to find the matching `&DogDocument` and resolve all inline references.

Reference resolution shows:
- Resolved references with their file paths
- Reference types and target primitive names
- Optional referenced documents expanded by depth

## Outcome

- JSON document context returned by default
- Text output available with `-o/--output text`
- Full document content included with resolved references
- Exit code 0 if found, 1 if not found
- Type filtering via sigil prefix
- Optional `--depth N` includes referenced documents up to N hops away

## Notes

- Name matching is case-insensitive
- Use sigil prefix to filter by type: @ (Actor), ! (Behavior), # (Component), & (Data)
- `--depth 0` returns only the requested document
- Reference expansion is intended for coding-agent context gathering

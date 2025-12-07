# Behavior: Refs

## Condition

- `@User` wants to find all documents that reference a specific primitive
- `@User` provides the target primitive name

## Description

The `@User` runs the `dog refs` command with a primitive name. The `#CLI` invokes the refs finder to scan all `&DogDocument` instances and identify which documents contain references to the target.

Reference discovery:
- Matches by name (case-insensitive)
- Collects line numbers for each reference occurrence
- Groups results by referencing document

## Outcome

- List of documents that reference the target
- Each result includes name, type, file path, and line numbers
- Type filtering via sigil prefix
- Supports text or JSON output formats

## Notes

- Critical for impact analysis: "What depends on this component?"
- Use sigil prefix to filter by type: @ (Actor), ! (Behavior), # (Component), & (Data)
- Use `--output json` for programmatic consumption

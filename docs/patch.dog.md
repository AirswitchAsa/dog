# Behavior: Patch

## Condition

- `@User` wants to update specific sections of a DOG document
- `@User` provides the document name and JSON patch data

## Description

The `@User` runs the `dog patch` command with a document name and JSON data. The `#CLI` invokes `#Patcher` to locate the matching `&DogDocument` and update the specified sections.

Patch data structure:
- sections: dict mapping section names to new content

The patcher will:
- Update existing sections with new content
- Add new sections if they don't exist (before Notes section)
- Validate that sections are allowed for the primitive type

## Outcome

- Document file updated in place
- List of updated sections displayed
- Exit code 0 if patched, 1 if error
- Type filtering via sigil prefix (@/!/#/&)

## Notes

- Name matching is case-insensitive
- Validates sections against ALLOWED_SECTIONS for primitive type
- Example: `dog patch "@User" --data '{"sections": {"Description": "New content"}}'`

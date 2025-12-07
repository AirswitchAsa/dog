# Data: ResolvedReference

## Description

Represents an inline reference with its resolution status.

## Fields

- name: referenced document name
- ref_type: expected primitive type (Actor, Behavior, Component, Data)
- resolved: boolean indicating if reference points to existing document
- file_path: path to referenced file (null if unresolved)

## Notes

- Pydantic BaseModel for validation
- Used by `&GetResult` to show reference status

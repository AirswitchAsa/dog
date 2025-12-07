# Component: Patcher

## Description

Updates DOG documents by patching specific sections. Handles section content replacement and addition. Used by `!Patch` behavior.

## State

- docs: list of parsed `&DogDocument` instances
- patch: `&PatchData` with sections to update
- target: matched document to patch

## Events

- patch_complete
- patch_error

## Notes

- Updates existing sections in place
- Adds new sections before Notes (or at end)
- Validates sections against ALLOWED_SECTIONS
- Async file write via run_in_executor

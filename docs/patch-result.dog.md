# Data: PatchResult

## Description

Result of a patch operation on a DOG document.

## Fields

- file_path: path to the patched file
- updated_sections: list of section names that were updated
- success: boolean indicating patch success
- error: error message if failed (null on success)

## Notes

- Pydantic BaseModel for validation
- Returned by `#Patcher` component

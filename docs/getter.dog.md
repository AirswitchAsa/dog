# Component: Getter

## Description

Retrieves DOG documents by name and resolves inline references. Provides document listing with optional type filtering. Used by `!Get` and `!List` behaviors.

## State

- docs: list of parsed `&DogDocument` instances
- doc_index: lookup table for reference resolution

## Events

- get_complete
- list_complete

## Notes

- Case-insensitive name matching
- Resolves references to existing documents
- Identifies unresolved references

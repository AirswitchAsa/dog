# Component: Getter

## Description

Retrieves DOG documents from the `#DogIndex` by name and resolves inline references. Provides document listing with optional type filtering. Used by `!Get` and `!List` behaviors.

## State

- index: `#DogIndex` containing parsed documents and lookup maps
- depth: optional reference expansion depth

## Events

- get_complete
- list_complete

## Notes

- Case-insensitive name matching
- Resolves references to existing documents
- Missing or mistyped references are expected to be caught by `!Lint`
- Can expand referenced documents for coding-agent context

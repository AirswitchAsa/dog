# Component: Formatter

## Description

Normalizes whitespace and indentation in `.dog.md` files. Produces consistent formatting without altering semantic content.

## State

- original_content: raw file content
- formatted_content: normalized content

## Events

- format_complete
- no_changes_needed

## Notes

- Pure function: same input always produces same output
- Async file I/O via run_in_executor

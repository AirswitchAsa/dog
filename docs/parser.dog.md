# Component: Parser

## Description

Parses `.dog.md` files into structured `&DogDocument` models. Uses the marko library for Markdown parsing. Extracts primitive type and name from H1 headers, sections from H2 headers, and inline references from content.

## State

- parsed_documents: list of `&DogDocument` instances

## Events

- parse_success
- parse_error

## Notes

- Async file I/O via run_in_executor
- Raises ParseError for invalid headers

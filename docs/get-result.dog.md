# Data: GetResult

## Description

Represents a retrieved document with its content and resolved references.

## Fields

- name: document name
- primitive_type: Actor, Behavior, Component, Data, or Project
- file_path: path to the source file
- sections: list of section name/content pairs
- references: list of `&ResolvedReference` instances
- raw_content: original markdown content

## Notes

- Pydantic BaseModel for validation
- Implements to_dict() for JSON serialization
- Implements to_text() for human-readable output

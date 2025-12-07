# Data: DogDocument

## Description

The primary data model representing a parsed `.dog.md` file. Contains all structural information extracted from the Markdown source.

## Fields

- file_path: Path to the source file
- primitive_type: PrimitiveType enum (Project, Actor, Behavior, Component, Data)
- name: name extracted from H1 header
- sections: list of Section instances
- references: list of InlineReference instances
- raw_content: original file content

## Notes

- Pydantic BaseModel for validation

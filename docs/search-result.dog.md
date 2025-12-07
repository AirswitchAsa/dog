# Data: SearchResult

## Description

Represents a single search result with relevance score and contextual snippet.

## Fields

- name: document name
- primitive_type: Actor, Behavior, Component, Data, or Project
- file_path: path to the source file
- score: relevance score (0-100, higher is better)
- snippet: contextual text snippet
- is_exact_match: boolean for exact name match (case-insensitive)
- name_distance: Levenshtein edit distance from query to name

## Notes

- Pydantic BaseModel for validation
- Implements to_dict() for JSON serialization

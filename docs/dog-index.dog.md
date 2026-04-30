# Component: DogIndex

## Description

In-memory knowledge model built once per CLI invocation or server reload. Owns the parsed `&DogDocument` collection, primitive lookup maps, reference graph, reverse-reference graph, and normalized search fields used by DOG commands.

## State

- root_path: file or directory used to discover DOG documents
- documents: list of parsed `&DogDocument` instances
- by_key: lookup by primitive type and normalized name
- by_name: lookup by normalized name for ambiguity detection
- by_file_stem: lookup by normalized file stem for serve routes and Markdown links
- refs_from: references emitted by each document
- refs_to: reverse references targeting each primitive
- search_entries: normalized fields used by `#Searcher`

## Events

- index_loaded
- index_rebuilt
- lookup_resolved
- lookup_ambiguous

## Notes

- Built in memory and discarded when a CLI command exits
- Does not require `.dog` cache files, a daemon, or persistent state
- Centralizes name normalization, type filtering, reference resolution, and ambiguity handling
- `!Serve` keeps one `#DogIndex` in memory while the web server is running and rebuilds it on file changes

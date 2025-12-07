# Component: Indexer

## Description

Generates Project index files from a collection of parsed `&DogDocument` instances. Groups primitives by type and produces a valid `index.dog.md` file.

## State

- documents: list of `&DogDocument` to index
- project_name: name for the Project header

## Events

- index_generated

## Notes

- Excludes existing index.dog.md from listings
- Sorts primitive names alphabetically

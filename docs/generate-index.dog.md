# Behavior: Generate Index

## Condition

- `@User` has `.dog.md` files to index
- `@User` provides a path and project name

## Description

The `@User` runs the `dog index` command with a path and `--name` option. The `#CLI` finds all `.dog.md` files, parses them with `#Parser`, and passes them to `#Indexer`.

The `#Indexer` generates an `index.dog.md` file containing:
- Project header with the specified name
- Description section
- Lists of all Actors, Behaviors, Components, and Data primitives
- Auto-generated notes

Existing `index.dog.md` files are excluded from the listing to avoid self-reference.

## Outcome

- `index.dog.md` is created or updated at the specified path
- All primitives are listed alphabetically by type
- Success message displayed with output path

## Notes

- Output file must be named `index.dog.md`

# Behavior: Format

## Condition

- `@User` has one or more `.dog.md` files to format
- `@User` provides a path to a file or directory

## Description

The `@User` runs the `dog format` command with a path argument. The `#CLI` finds all `.dog.md` files and passes them to `#Formatter` for whitespace normalization.

The `#Formatter` applies these normalizations:
- Trims trailing whitespace from each line
- Collapses multiple blank lines into single blank lines
- Normalizes list indentation to 2-space increments
- Ensures single newline at end of file

The `@User` can use `--check` flag to verify formatting without modifying files.

## Outcome

- Files are reformatted in place (unless `--check` is used)
- Changed files are listed in output
- Exit code 0 if all files formatted, 1 if `--check` finds unformatted files

## Notes

- Check mode is useful for CI pipelines

# Component: CLI

## Description

The command-line interface component built with Typer. Provides the `dog` command with subcommands for `!Lint`, `!Format`, `!Generate Index`, `!Search`, `!Get`, and `!List` operations. Handles argument parsing, user feedback, and exit codes.

## State

- path: target file or directory
- exit_code: operation result (0=success, 1=failure)
- output_format: text or json output mode

## Events

- lint_command
- format_command
- index_command
- search_command
- get_command
- list_command

## Notes

- Uses Typer for argument parsing and help generation
- Async operations run via asyncio.run()
- Search, get, and list commands support JSON output for programmatic use

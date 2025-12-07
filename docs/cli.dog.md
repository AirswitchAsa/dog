# Component: CLI

## Description

The command-line interface component built with Typer. Provides the `dog` command with subcommands for `!Lint`, `!Format`, `!Generate Index`, `!Search`, `!Get`, `!List`, `!Patch`, `!Refs`, `!Graph`, `!Export`, and `!Serve` operations. Handles argument parsing, user feedback, and exit codes.

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
- patch_command
- refs_command
- graph_command
- export_command
- serve_command

## Notes

- Uses Typer for argument parsing and help generation
- Async operations run via asyncio.run()
- Search, get, list commands support JSON output for programmatic use
- Type filtering uses sigil prefixes: @ (Actor), ! (Behavior), # (Component), & (Data)

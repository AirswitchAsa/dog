# Component: CLI

## Description

The command-line interface component built with Typer. Provides the `dog` command with subcommands for `!Lint`, `!Format`, `!Generate Index`, `!Search`, `!Get`, `!List`, `!Refs`, `!Graph`, `!Export`, and `!Serve` operations. Handles argument parsing, output formatting, user feedback, and exit codes.

## State

- path: target file or directory
- exit_code: operation result (0=success, 1=failure)
- output_format: json or text output mode
- index: per-invocation `#DogIndex` built from the target path

## Events

- lint_command
- format_command
- index_command
- search_command
- get_command
- list_command
- refs_command
- graph_command
- export_command
- serve_command

## Notes

- Uses Typer for argument parsing and help generation
- Async operations run via asyncio.run()
- Search, get, refs, and list default to JSON output for coding agents
- Search, get, refs, and list support `-o/--output text` for human-readable output
- Lint, format, generate index, graph, and serve keep their standard CLI-oriented defaults
- Each command invocation builds an in-memory `#DogIndex`; no persistent cache or daemon is required
- Type filtering uses sigil prefixes: @ (Actor), ! (Behavior), # (Component), & (Data)

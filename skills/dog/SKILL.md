---
name: dog
description: Use when a repository contains .dog.md files or the user asks for DOG documentation-first development. Guides coding agents to inspect DOG specs with the dog CLI from the dog-cli PyPI package, implement code to match documented behavior, maintain typed references, and validate docs with DOG quality gates.
metadata:
  short-description: DOG documentation-first development
---

# DOG

DOG (Documentation Oriented Grammar) is a Markdown-native specification format for coding agents and humans. In DOG repositories, `.dog.md` files are the source of truth for actors, behaviors, components, data, references, and validation rules.

## Bootstrap the CLI

Use the DOG CLI when possible. The PyPI package is `dog-cli`; the executable is `dog`.

Before relying on DOG commands, run the bundled bootstrap script:

```bash
scripts/ensure-dog.sh
```

In an installed skill, resolve the script path relative to this `SKILL.md`. If the script is not available, use this fallback order:

1. Existing executable: `dog`
2. Ephemeral PyPI execution: `uvx --from dog-cli dog`
3. Ask the user to install (in order of preference):
   - Prebuilt binary (macOS/Linux): `curl -fsSL https://raw.githubusercontent.com/AirswitchAsa/dog/main/scripts/install.sh | sh`
   - Persistent PyPI install: `uv tool install dog-cli`
   - Fallback: `pip install dog-cli`

Do not assume plain `uvx dog-cli` works; use `uvx --from dog-cli dog`.

## Core Workflow

When a repo contains `.dog.md` files:

1. Discover DOG docs: `rg --files -g '*.dog.md'`
2. List primitives: `dog list -p docs`
3. Search concepts: `dog search "<query>" -p docs`
4. Read relevant specs: `dog get "<name>" -p docs --depth 1`
5. Check impact before cross-cutting changes: `dog refs "<name>" -p docs`
6. Implement code to satisfy the documented behavior.
7. Update DOG docs when behavior changes.
8. Validate before finishing: `dog lint docs` and relevant project tests.

Prefer JSON output for agent reasoning. `search`, `get`, `list`, and `refs` return JSON by default. Use `-o text` only for human-readable summaries.

## DOG Rules

- Primitive headers use exactly one of: `# Project:`, `# Actor:`, `# Behavior:`, `# Component:`, `# Data:`.
- Typed inline references use backticks and sigils: `` `@Actor` ``, `` `!Behavior` ``, `` `#Component` ``, `` `&Data` ``.
- References are strict: only use a sigil when that primitive exists with that type.
- Required sections are strict:
  - Actor: `Description`, `Notes`
  - Behavior: `Condition`, `Description`, `Outcome`, `Notes`
  - Component: `Description`, `State`, `Events`, `Notes`
  - Data: `Description`, `Fields`, `Notes`
  - Project: `Description`, `Actors`, `Behaviors`, `Components`, `Data`, `Notes`
- Missing refs, mistyped refs, missing required sections, and empty required sections are errors.

## Command Hints

Read `references/cli.md` when you need exact command options, output behavior, or examples.

Useful commands:

```bash
dog search "authentication" -p docs
dog search "#AuthService" -p docs
dog search "rare term" -p docs --all
dog get "!Login" -p docs --depth 1
dog refs "#AuthService" -p docs
dog list "!" -p docs
dog lint docs
dog format --check docs
```

## Quality Gate

Before declaring DOG-related work complete:

```bash
dog lint docs
dog format --check docs
```

Also run the repository's normal tests, type checks, and linters when code changed.

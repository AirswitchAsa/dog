# Agent Workflow

DOG is designed to be the project knowledge layer that coding agents consult before they read code, and update before they write code.

## The idea

Most agent workflows look like this:

```text
read repo → write spec → read repo/spec → write plan → read repo/spec/plan → implement
```

Each step generates prose that is thrown away after the task. The agent re-derives the same understanding next time.

DOG replaces the disposable middle with a persistent concept graph:

```text
brainstorm change
  → update DOG concept docs
  → review the DOG docs diff
  → implement against that diff
  → dog lint
```

The DOG docs diff *is* the plan. Once a task ends, the concept graph is still useful — it reflects what the system means right now.

## Install the skill

Agents that support the [skills protocol](https://github.com/anthropics/skills) (Claude Code, Cursor, Codex via adapters, etc.) can install DOG once and pick it up automatically across projects:

```bash
npx skills add https://github.com/AirswitchAsa/dog/tree/main/skills/dog
```

The skill ([`skills/dog`](../../skills/dog/)) does three things:

1. Bootstraps the `dog` CLI — prefers an installed binary, falls back to `uvx --from dog-cli dog`.
2. Teaches the agent the primitive types, sigils, and required sections.
3. Tells the agent *when* to consult DOG (any repo with `.dog.md` files).

## Core agent loop

Once the skill is installed, the agent follows a consistent loop on any repo containing `.dog.md` files:

1. **Discover** — `rg --files -g '*.dog.md'`
2. **Orient** — `dog list -p docs` to see all primitives by type.
3. **Search** — `dog search "<query>" -p docs` for relevant concepts.
4. **Read** — `dog get "<name>" -p docs --depth 1` to inline directly referenced primitives.
5. **Impact** — `dog refs "<name>" -p docs` before any cross-cutting change.
6. **Implement** — code fulfils the documented behavior.
7. **Update docs** — when behavior, components, or data change, update the DOG primitives in the same diff.
8. **Validate** — `dog lint docs` and `dog format --check docs` are the quality gate.

JSON is the default output for `search`, `get`, `list`, `refs` — easy for the agent to reason over. `-o text` is for the human watching.

## Decision guide

| Situation                     | Action                                             |
| ----------------------------- | -------------------------------------------------- |
| Bug in the code, spec correct | Fix the code to match the spec.                    |
| Bug in the spec               | Fix the spec first, then the code.                 |
| Missing concept               | Document the primitive, then implement.            |
| Cross-cutting change          | Run `dog refs` to find every affected primitive.   |

## System-prompt fallback

For agents without skill support, paste this into the system prompt:

```markdown
You are the primary development agent for this codebase, combining expert software engineering with DOG methodology.

## CLI Reference

| Command  | Purpose                                   |
| -------- | ----------------------------------------- |
| `get`    | Read a primitive with resolved refs       |
| `search` | Find primitives with hybrid local search  |
| `list`   | List all primitives (filter: `@!#&`)      |
| `refs`   | Reverse lookup: what references this?     |
| `export` | Bulk export all docs as JSON              |
| `graph`  | DOT output for dependency visualization   |
| `lint`   | Validate structure/refs                   |
| `format` | Normalize whitespace                      |

Tips:
- `get`, `search`, `list`, `refs` return JSON by default; `-o text` for humans
- `dog get <name> --depth 1` includes directly referenced primitives
- `dog search <query> --all` includes low-confidence matches
- Sigil prefixes filter by type: `#`, `!`, `@`, `&`
- `refs` is essential for impact analysis before changes

## Workflow

1. Understand: `dog get` + `dog refs` to map dependencies
2. Design: document new behaviors before coding
3. Implement: code fulfills documented behavior
4. Validate: `dog lint docs` passes

Decision guide:
- Bug in code → fix code to match spec
- Bug in spec → fix spec, then code
- Missing docs → document first
- Cross-cutting change → use `dog refs` to find affected docs

Quality gate before completing any task: `dog lint docs` passes, code matches documented Behaviors, terminology is consistent.
```

## Reference discipline

DOG references are typed. Only use a sigil when the referenced primitive exists with that exact type:

- `@Name` only for Actor primitives
- `!Name` only for Behavior primitives
- `#Name` only for Component primitives
- `&Name` only for Data primitives

Missing primitives and mistyped references are lint errors. The lint pass is the contract that keeps the concept graph trustworthy across many edits by many agents.

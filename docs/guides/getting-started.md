# Getting Started

This guide walks you through creating your first DOG documentation. For installation options, see the [install guide](install.md).

## Quick install

```bash
pip install dog-cli
# or:
uv tool install dog-cli
```

## Your first document

A `.dog.md` file holds exactly one primitive. Create `user.dog.md`:

```markdown
# Actor: User

## Description

A human user of the system who interacts through the web interface.

## Notes

- Primary actor for most behaviors.
```

## Primitive types

DOG defines five primitive types. Each has a fixed set of required sections.

| Type      | Header           | Required sections                                                  | Sigil |
| --------- | ---------------- | ------------------------------------------------------------------ | ----- |
| Project   | `# Project: …`   | Description, Actors, Behaviors, Components, Data, Notes            |       |
| Actor     | `# Actor: …`     | Description, Notes                                                 | `@`   |
| Behavior  | `# Behavior: …`  | Condition, Description, Outcome, Notes                             | `!`   |
| Component | `# Component: …` | Description, State, Events, Notes                                  | `#`   |
| Data      | `# Data: …`      | Description, Fields, Notes                                         | `&`   |

## Cross-references

Link concepts using sigils inside backticks:

- `` `@User` `` references an Actor
- `` `!Login` `` references a Behavior
- `` `#AuthService` `` references a Component
- `` `&Credentials` `` references a Data primitive

References are typed: only use a sigil when the referenced primitive exists with that exact type. Mistyped or missing references are lint errors.

## Generate an index

Once you have several documents, generate a project index:

```bash
dog index docs/ --name "My Project"
```

This creates `index.dog.md` listing all your primitives by type.

## Validate

```bash
dog lint docs/
```

Use this as the quality gate before completing documentation changes.

## Browse in a browser

```bash
dog serve docs/
```

Open <http://localhost:8000> for a navigable view with color-coded references and hot-reload.

## Next steps

- [CLI reference](cli.md) — every command and flag
- [Agent workflow](agent-workflow.md) — how coding agents use DOG
- [Philosophy](philosophy.md) — design principles
- [Comparisons](comparisons.md) — DOG vs Gherkin, OpenAPI, C4, ADRs, Spec Kit, Kiro

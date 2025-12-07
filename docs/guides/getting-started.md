# Getting Started

This guide walks you through creating your first DOG documentation.

## Installation

```bash
pip install dog-cli
# or with uv
uv add dog-cli
```

## Your First Document

Create a file called `user.dog.md`:

```markdown
# Actor: User

## Description

A human user of the system who interacts through the web interface.

## Notes

- Primary actor for most behaviors
```

## Primitive Types

DOG defines five primitive types:

| Type | Purpose | Example |
|------|---------|---------|
| Project | Index of a doc set | `# Project: MyApp` |
| Actor | Who does things | `# Actor: User` |
| Behavior | What happens | `# Behavior: Login` |
| Component | System parts | `# Component: AuthService` |
| Data | Domain entities | `# Data: Credentials` |

## Cross-References

Link concepts using sigils inside backticks:

- `@User` references an Actor
- `!Login` references a Behavior
- `#AuthService` references a Component
- `&Credentials` references a Data

## Generate an Index

Once you have several documents, generate a project index:

```bash
dog index docs/ --name "My Project"
```

This creates `index.dog.md` listing all your primitives.

## Validate Your Docs

Check for structural issues and broken references:

```bash
dog lint docs/
```

## Browse in Browser

Start the documentation server:

```bash
dog serve docs/
```

Open http://localhost:8000 to see your docs with color-coded links.

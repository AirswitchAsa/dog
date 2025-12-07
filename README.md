# DOG


<p align="center">
  <img src="dog.png" alt="DOG" width="200">
</p>


**Documentation Oriented Grammar** — A Markdown-native format for system documentation that serves humans and AI agents alike.

Available on: [pypi](https://pypi.org/project/dog-cli/)

---

## Quick Start

### Installation

```bash
pip install dog
# or with uv
uv add dog
```

### Basic Usage

```bash
# Validate your docs
dog lint docs/

# Format files
dog format docs/

# Generate project index
dog index docs/ --name "My Project"

# Search for concepts
dog search "login" --path docs/

# Get a specific document
dog get "User" --path docs/

# List all documents
dog list --path docs/
```

### Example

See the [docs/](docs/) folder for a complete example of DOG documentation for this project.

---

## What is DOG?

`.dog.md` is a Markdown-native specification format. Each file defines exactly one primitive type — **Project**, **Actor**, **Behavior**, **Component**, or **Data** — using light structural conventions.

DOG serves as:

- **Human-readable system documentation**
- **A structured knowledge base for LLM agents**
- **A behavioral reference for AI-assisted testing**

### Primitive Types

| Type          | Purpose                                | Example                    |
| ------------- | -------------------------------------- | -------------------------- |
| **Project**   | Root index of a documentation set      | `# Project: MyApp`         |
| **Actor**     | User or service that initiates actions | `# Actor: User`            |
| **Behavior**  | System response or state transition    | `# Behavior: Login Flow`   |
| **Component** | Subsystem or UI element                | `# Component: AuthService` |
| **Data**      | Domain entity with fields              | `# Data: Credentials`      |

### Cross-References

Use sigils inside backticks to reference other concepts:

| Syntax               | Meaning             |
| -------------------- | ------------------- |
| `` `@User` ``        | Actor reference     |
| `` `!Login` ``       | Behavior reference  |
| `` `#AuthService` `` | Component reference |
| `` `&Credentials` `` | Data reference      |

---

## CLI Commands

### `dog lint <path>`

Validate `.dog.md` files for structure and reference errors.

```bash
dog lint docs/
dog lint my-behavior.dog.md
```

### `dog format <path>`

Format `.dog.md` files (normalize whitespace).

```bash
dog format docs/
dog format --check docs/  # Check without modifying
```

### `dog index <path> --name <name>`

Generate or update a Project index file (`index.dog.md`).

```bash
dog index docs/ --name "My Project"
```

### `dog search <query>`

Search documents using fuzzy matching. Returns top-k results sorted by relevance.

```bash
dog search "login"
dog search "auth" --type Component
dog search "user" --limit 5 --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--type`, `-t`   | Filter by primitive type           |
| `--limit`, `-l`  | Max results (default: 10)          |
| `--output`, `-o` | `text` or `json`                   |

### `dog get <name>`

Get a document by name with resolved references.

```bash
dog get "Login Flow"
dog get "User" --type Actor
dog get "AuthService" --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--type`, `-t`   | Filter by primitive type           |
| `--output`, `-o` | `text` or `json`                   |

### `dog list`

List all documents.

```bash
dog list
dog list --type Behavior
dog list --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--type`, `-t`   | Filter by primitive type           |
| `--output`, `-o` | `text` or `json`                   |

---

## File Format Reference

### Project

```markdown
# Project: <Name>

## Description
<freeform text>

## Actors
- <actor name>

## Behaviors
- <behavior name>

## Components
- <component name>

## Data
- <data name>

## Notes
- <annotation>
```

### Actor

```markdown
# Actor: <Name>

## Description
<free text>

## Notes
- <annotation>
```

### Behavior

```markdown
# Behavior: <Name>

## Condition
- <prerequisite>

## Description
<free text with `@actor`, `!behavior`, `#component`, `&data` references>

## Outcome
- <expected effect>

## Notes
- <annotation>
```

### Component

```markdown
# Component: <Name>

## Description
<free text>

## State
- <state field>

## Events
- <event name>

## Notes
- <annotation>
```

### Data

```markdown
# Data: <Name>

## Description
<free text>

## Fields
- field_name: <description>

## Notes
- <annotation>
```

---

## Design Principles

**Markdown-native** — No custom DSLs. Files render anywhere without special tooling.

**Light structure, high semantic value** — Predictable headings and cross-references that LLMs can reliably parse.

**Unified source of truth** — One place for product docs, concept definitions, developer references, and AI context.

**Flat taxonomy** — No hierarchies. Concepts link through explicit naming.

**Simple linting** — Validates references, sections, and naming. Deeper logic left to authors and AI reasoning.

---

## License

MIT

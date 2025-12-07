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
pip install dog-cli
# or with uv
uv add dog-cli
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
dog get "@User" --path docs/

# List all documents
dog list --path docs/

# Serve documentation in browser
dog serve docs/
```

## Agent System Prompt

Add this to your LLM agent's system prompt to enable DOG-driven development:

~~~markdown
---
name: dog-developer
description: >
  PRIMARY DEVELOPMENT AGENT for this codebase. Use for ALL development tasks:
  implementing features, fixing bugs, refactoring, code reviews, and architectural decisions.

  This agent enforces DOG (Documentation-Oriented Grammar)—a documentation-first methodology
  where .dog.md behavioral specifications are the source of truth. Code fulfills documentation,
  not the other way around.
model: opus
---

You are the primary development agent for this codebase, combining expert software engineering with DOG methodology.

## Why DOG?

DOG fills the gap between unstructured documentation (hard for LLMs to parse) and rigid schemas (can't capture behavioral flows). It's:
- **Markdown-native**: No special infrastructure, just `.dog.md` files
- **Structured enough**: LLMs can reliably extract knowledge
- **Human-readable**: Serves as actual documentation
- **Behavioral**: Captures flows, actors, and domain concepts—not just API contracts

The core insight: **describe system behavior as constraints first, then let implementation fulfill them.**

## DOG Primitives

Four types form a semantic graph via cross-references:

| Sigil | Type      | Purpose                           |
| ----- | --------- | --------------------------------- |
| `@`   | Actor     | Who initiates actions             |
| `!`   | Behavior  | What the system does (flows)      |
| `#`   | Component | How it's built (modules, APIs)    |
| `&`   | Data      | What's stored (entities, schemas) |

Example: "`@User` submits `&Order` to `#CartService`, triggering `!Checkout`"

## File Structure

Each `.dog.md` file defines ONE primitive. Key sections by type:

**Behavior** (most important—defines system contracts):
```markdown
# Behavior: <Name>

## Condition
- <what triggers this>

## Description
<what happens, with cross-references>

## Outcome
- <expected result>
```

**Component**: Description, State, Events
**Data**: Description, Fields
**Actor**: Description

## CLI Commands

```bash
dog search <query>       # Find primitives (use sigil prefix to filter: @, !, #, &)
dog get <name>           # Get specific primitive with resolved references
dog list [sigil]         # List all primitives, optionally by type
dog lint <path>          # Validate structure and references
dog patch <name> --data  # Update specific sections programmatically
dog index <path> --name  # Generate project index
```

Use `--output json` for structured data. Use `--path` to specify directory.

## Development Workflow

**For every task:**

1. **Understand first**: `dog search` and `dog list` to find relevant primitives
2. **Design against specs**: Identify which Behaviors your change affects; document new ones before coding
3. **Implement**: Write code that fulfills documented behavior
4. **Validate**: Run `dog lint` to check consistency

**When documentation doesn't exist**: Investigate the code, document what you find, then proceed.

**When fixing bugs**: Determine if the bug is code (doesn't match spec) or spec (spec is wrong). Fix the right one.

## Quality Gate

Before completing any task:
- Code implements documented Behaviors
- `dog lint` passes
- New Behaviors have Condition → Description → Outcome
- Cross-references resolve to existing primitives

You advocate for documentation-first development. If asked to implement without clear specs, clarify or document the expected behavior first.
~~~

---


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
dog search "#auth"              # Filter by Component type
dog search "user" --limit 5 --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--limit`, `-l`  | Max results (default: 10)          |
| `--output`, `-o` | `text` or `json`                   |

Use sigil prefixes to filter by type: `@` (Actor), `!` (Behavior), `#` (Component), `&` (Data).

### `dog get <name>`

Get a document by name with resolved references.

```bash
dog get "Login Flow"
dog get "@User"                 # Get Actor named User
dog get "#AuthService" --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--output`, `-o` | `text` or `json`                   |

Use sigil prefixes to filter by type: `@` (Actor), `!` (Behavior), `#` (Component), `&` (Data).

### `dog list`

List all documents.

```bash
dog list
dog list !                      # List only Behaviors
dog list --output json
```

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `--path`, `-p`   | Directory to search (default: `.`) |
| `--output`, `-o` | `text` or `json`                   |

Use sigil prefixes to filter by type: `@` (Actor), `!` (Behavior), `#` (Component), `&` (Data).

### `dog patch <name>`

Update specific sections of a DOG document programmatically.

```bash
dog patch "@User" --data '{"sections": {"Description": "Updated description"}}'
dog patch "Login" --data '{"sections": {"Outcome": "New outcome"}}'
```

| Option         | Description                        |
| -------------- | ---------------------------------- |
| `--path`, `-p` | Directory to search (default: `.`) |
| `--data`, `-d` | JSON patch data                    |

### `dog serve <path>`

Serve DOG documentation as HTML in the browser with hot-reload.

```bash
dog serve docs/
dog serve --host 0.0.0.0 --port 3000
dog serve docs/ --no-reload
```

| Option         | Description                         |
| -------------- | ----------------------------------- |
| `--host`, `-h` | Host to bind (default: `127.0.0.1`) |
| `--port`, `-P` | Port to bind (default: `8000`)      |
| `--no-reload`  | Disable hot-reload on file changes  |

Features:
- Color-coded reference links (red=Actor, blue=Behavior, purple=Component, green=Data)
- Renders `index.dog.md` as homepage when present
- Automatic favicon discovery (favicon.png or dog.png)
- Hot-reload on file changes

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

## Why DOG?

| Approach                | Trade-offs                                                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **RAG/Vector Search**   | Requires embeddings, chunking strategy, retrieval tuning. Context can be fragmented or miss cross-references.            |
| **Traditional Docs**    | Great for humans, but unstructured prose is hard for LLMs to reliably extract structured knowledge from.                 |
| **OpenAPI/JSON Schema** | Excellent for API contracts, but doesn't capture behavioral flows, actors, or domain concepts.                           |
| **DOG**                 | Markdown-native, no infra needed. Structured enough for LLM parsing, readable enough for humans. Single source of truth. |

DOG fills the gap between unstructured documentation and rigid schemas. It's lightweight enough to write by hand, structured enough to parse programmatically, and readable enough to serve as your actual documentation.

---


## License

MIT

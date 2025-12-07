# Philosophy

DOG (Documentation Oriented Grammar) is built on a few core principles.

## Markdown-Native

DOG files are just Markdown. They render beautifully in GitHub, VS Code, or any Markdown viewer without special tooling. The structure comes from conventions, not syntax.

## Light Structure, High Semantic Value

Rather than free-form prose or rigid schemas, DOG uses predictable headings and cross-references. This makes documents:
- Easy for humans to read and write
- Reliable for LLMs to parse and reason about
- Simple to validate with linting tools

## Unified Source of Truth

One place for:
- Product documentation
- Concept definitions
- Developer references
- AI context for code assistants

No more scattered wikis, stale READMEs, or out-of-sync specs.

## Flat Taxonomy

DOG avoids deep hierarchies. Instead, concepts link to each other through explicit naming with sigil references:
- `@Actor` for users or services
- `!Behavior` for actions and flows
- `#Component` for system parts
- `&Data` for domain entities

This creates a graph of interconnected concepts rather than a rigid tree.

## Designed for AI

The structured format makes DOG ideal for:
- Feeding context to LLM code assistants
- Automated testing based on behavior specs
- Generating documentation from code
- Keeping AI and human understanding aligned

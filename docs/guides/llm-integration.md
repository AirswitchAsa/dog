# LLM Integration

DOG is designed to work seamlessly with Large Language Models.

## Why DOG for LLMs?

Traditional documentation is optimized for human reading but poses challenges for LLMs:
- Unstructured prose requires interpretation
- Context gets lost across long documents
- Cross-references are implicit or missing
- No consistent format to parse

DOG solves these by providing:
- Predictable structure (same sections, same format)
- Explicit cross-references with sigils
- Type information (Actor, Behavior, Component, Data)
- Machine-readable output (JSON)

## Feeding Context to LLMs

Use the `dog get` command to retrieve structured context:

```bash
# Get a specific document with resolved references
dog get "@User" --output json

# Search for relevant concepts
dog search "authentication" --output json --limit 5
```

## Example Workflow

1. User asks about login functionality
2. Search DOG docs: `dog search "!login" --output json`
3. Get the behavior: `dog get "!Login" --output json`
4. Feed structured context to LLM with resolved references

## JSON Output Format

The JSON output includes:
- Document name and type
- All sections with content
- Resolved references (linked docs exist)
- Unresolved references (missing docs)

This gives LLMs complete context about a concept and its relationships.

## Updating Docs Programmatically

LLMs can update docs using the patch command:

```bash
dog patch "@User" --data '{"sections": {"Description": "Updated by AI"}}'
```

This enables AI-assisted documentation maintenance.

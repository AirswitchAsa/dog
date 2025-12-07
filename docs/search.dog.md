# Behavior: Search

## Condition

- `@User` wants to find DOG documents by name or content
- `@User` provides a search query

## Description

The `@User` runs the `dog search` command with a query string. The `#CLI` invokes `#Searcher` to search through all `&DogDocument` instances using RapidFuzz fuzzy matching. Returns top-k results sorted by relevance score (0-100).

Matching strategies:
- Exact name matches (100 score)
- Token-based matching (handles word reordering)
- Partial/substring matches
- Content matching in sections
- Reference matching (weighted lower)

## Outcome

- Top-k documents returned sorted by relevance
- Sorting: exact matches first, then by name distance, then by score
- Each result includes name, type, file path, score, and snippet
- Type filtering via sigil prefix
- Supports text or JSON output formats

## Notes

- Use sigil prefix to filter by type: @ (Actor), ! (Behavior), # (Component), & (Data)
- Use `--limit` to set k (default: 10)
- Use `--output json` for programmatic consumption
- Powered by RapidFuzz fuzzy string matching

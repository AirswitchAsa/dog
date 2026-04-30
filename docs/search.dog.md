# Behavior: Search

## Condition

- `@User` wants to find DOG documents by name or content
- `@User` provides a search query

## Description

The `@User` runs the `dog search` command with a query string. The `#CLI` builds a `#DogIndex` and invokes `#Searcher` to search indexed `&DogDocument` instances using hybrid local retrieval. Returns meaningful results sorted by relevance score (0-100).

Matching strategies:
- Exact primitive and name matches
- Exact token/content matches
- Fuzzy name matches
- Fuzzy section matches with section-aware weighting
- Reference matches through the `#DogIndex`
- Optional graph-aware expansion from high-confidence matches

## Outcome

- JSON results returned by default
- Text output available with `-o/--output text`
- Results below the default minimum relevance threshold are excluded
- Results sorted by exactness, relevance score, and tie-breakers
- Each result includes name, type, file path, score, snippet, and match metadata
- Type filtering via sigil prefix

## Notes

- Use sigil prefix to filter by type: @ (Actor), ! (Behavior), # (Component), & (Data)
- Use `--limit` to set k (default: 10)
- Use `--min-score` to override the default relevance threshold
- Use `--all` or `--min-score 0` to include low-confidence matches
- Semantic matching is local, stateless, dependency-light, and does not require embeddings or external model calls
- `dog search` complements exact source search tools such as rg; it is optimized for DOG primitive, section, and reference retrieval

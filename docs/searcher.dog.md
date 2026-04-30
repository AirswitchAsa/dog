# Component: Searcher

## Description

Provides hybrid local search across DOG documents using the `#DogIndex`. Calculates relevance scores based on primitive identity, exact text matches, fuzzy name matches, weighted section matches, references, and optional graph expansion. Returns only results that satisfy the configured relevance threshold.

## State

- index: `#DogIndex` containing parsed documents and lookup maps
- query: search string
- type_filter: optional primitive type filter
- limit: maximum results to return (top-k)
- min_score: minimum relevance score required for inclusion
- expand_refs: whether connected documents should be included from high-confidence hits

## Events

- search_complete

## Notes

- Uses local deterministic scoring; no embedding or model dependency is required
- Exact primitive/name matches outrank fuzzy and content matches
- Section weights prioritize names and behavioral sections over notes
- Reference matches use the `#DogIndex` graph
- Returns scores on 0-100 scale
- Results sorted by exactness, relevance score, and deterministic tie-breakers

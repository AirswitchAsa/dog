# Component: Searcher

## Description

Provides fuzzy search across DOG documents using RapidFuzz. Calculates relevance scores based on query matches in names, sections, and references. Returns top-k results sorted by score.

## State

- docs: list of parsed `&DogDocument` instances
- query: search string
- type_filter: optional primitive type filter
- limit: maximum results to return (top-k)

## Events

- search_complete

## Notes

- Uses RapidFuzz for fuzzy string matching
- Supports token-based matching (word reordering)
- Supports partial/substring matches
- Name matches boosted 20% over content matches
- Returns scores on 0-100 scale

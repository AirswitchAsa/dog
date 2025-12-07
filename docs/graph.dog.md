# Behavior: Graph

## Condition

- `@User` wants to visualize the dependency structure of DOG documentation
- `@User` optionally specifies a root node to generate a subgraph

## Description

The `@User` runs the `dog graph` command. The `#CLI` invokes the graph generator to build a DOT format dependency graph from all `&DogDocument` instances.

Graph generation:
- Creates nodes for each primitive with type-specific colors
- Creates edges from references between documents
- Optionally filters to connected subgraph from a root node
- Uses sigil prefixes in node identifiers (@, !, #, &)

Color scheme matches `!Serve` display:
- Actor: red (#a22041)
- Behavior: blue (#457b9d)
- Component: purple (#915c8b)
- Data: green (#2a9d8f)

## Outcome

- DOT format graph output to stdout
- Can be piped to graphviz: `dog graph | dot -Tpng -o graph.png`
- Subgraph mode includes only connected nodes from root
- Uses left-to-right layout (rankdir=LR)

## Notes

- Requires graphviz for rendering (dot, neato, etc.)
- Duplicate edges are filtered out
- Only includes edges to resolved references

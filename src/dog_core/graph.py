from dog_core.dog_index import AmbiguousLookupError, DogIndex, ensure_index
from dog_core.models import DogDocument, PrimitiveType, parse_primitive_query


# Colors matching the server's CSS variables
TYPE_COLORS: dict[PrimitiveType, str] = {
    PrimitiveType.ACTOR: "#a22041",
    PrimitiveType.BEHAVIOR: "#457b9d",
    PrimitiveType.COMPONENT: "#915c8b",
    PrimitiveType.DATA: "#2a9d8f",
    PrimitiveType.PROJECT: "#1d3557",
}

SIGIL_MAP_REVERSE: dict[PrimitiveType, str] = {
    PrimitiveType.ACTOR: "@",
    PrimitiveType.BEHAVIOR: "!",
    PrimitiveType.COMPONENT: "#",
    PrimitiveType.DATA: "&",
    PrimitiveType.PROJECT: "",
}


def _escape_dot_id(name: str, ptype: PrimitiveType) -> str:
    """Create a valid DOT identifier."""
    sigil = SIGIL_MAP_REVERSE.get(ptype, "")
    return f'"{sigil}{name}"'


async def generate_graph(  # noqa: C901
    index_or_docs: DogIndex | list[DogDocument],
    root: str | None = None,
) -> str:
    """Generate a DOT format dependency graph.

    Args:
        docs: List of parsed DogDocuments
        root: Optional root node to generate subgraph from (with optional sigil)

    Returns:
        DOT format graph string
    """
    index = ensure_index(index_or_docs)

    # If root specified, find it and only include connected nodes
    included_docs: list[DogDocument]
    if root:
        root_name, root_type = parse_primitive_query(root)

        # Find the root document
        try:
            root_doc = index.resolve(root_name, root_type)
        except AmbiguousLookupError:
            return f'digraph DOG {{\n  label="Ambiguous: {root}";\n}}\n'

        if root_doc is None:
            return f'digraph DOG {{\n  label="Not found: {root}";\n}}\n'

        # BFS to find all connected nodes
        visited = set()
        queue: list[DogDocument] = [root_doc]
        included_docs = []

        while queue:
            doc = queue.pop(0)
            key = index.key_for(doc)
            if key in visited:
                continue
            visited.add(key)
            included_docs.append(doc)

            # Add referenced docs to queue
            for occurrence in index.references_from(doc):
                ref_doc = occurrence.target
                if ref_doc is not None and index.key_for(ref_doc) not in visited:
                    queue.append(ref_doc)

            # Add docs that reference this one (reverse refs)
            for occurrence in index.references_to(doc.name, doc.primitive_type):
                other_doc = occurrence.source
                if index.key_for(other_doc) not in visited:
                    queue.append(other_doc)
    else:
        included_docs = list(index.documents)

    # Generate DOT
    lines = [
        "digraph DOG {",
        "  rankdir=LR;",
        "  node [shape=box, style=filled, fillcolor=white];",
        "",
    ]

    # Group nodes by type
    by_type: dict[PrimitiveType, list[DogDocument]] = {}
    for doc in included_docs:
        by_type.setdefault(doc.primitive_type, []).append(doc)

    # Add nodes
    for ptype, type_docs in by_type.items():
        color = TYPE_COLORS.get(ptype, "#666666")
        lines.append(f"  // {ptype.value}s")
        for doc in sorted(type_docs, key=lambda d: d.name):
            node_id = _escape_dot_id(doc.name, ptype)
            lines.append(f'  {node_id} [color="{color}", fontcolor="{color}"];')
        lines.append("")

    # Add edges
    lines.append("  // References")
    edges_added: set[tuple[str, str]] = set()

    for doc in included_docs:
        from_id = _escape_dot_id(doc.name, doc.primitive_type)
        for ref in doc.references:
            # Only add edge if target is in included docs
            target_doc = index.resolve_reference(ref)
            if target_doc is not None and target_doc in included_docs:
                to_id = _escape_dot_id(ref.name, ref.ref_type)
                edge = (from_id, to_id)
                if edge not in edges_added:
                    edges_added.add(edge)
                    lines.append(f"  {from_id} -> {to_id};")

    lines.append("}")

    return "\n".join(lines)

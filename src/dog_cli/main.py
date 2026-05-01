import asyncio
import json
from enum import Enum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Annotated

import typer

from dog_cli import __version__ as _fallback_version
from dog_core import (
    AmbiguousLookupError,
    DogIndex,
    ParseError,
    PrimitiveType,
    export_documents,
    find_dog_files,
    find_refs,
    format_file_in_place,
    generate_graph,
    generate_index,
    get_document,
    lint_documents,
    list_documents,
    parse_primitive_query,
    search_documents,
)


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


app = typer.Typer(
    name="dog",
    help="DOG (Documentation Oriented Grammar) CLI tool",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _resolve_version() -> str:
    try:
        return _pkg_version("dog-cli")
    except PackageNotFoundError:
        return _fallback_version


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dog {_resolve_version()}")
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show the version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """DOG (Documentation Oriented Grammar) CLI tool."""


def _json_echo(payload: dict) -> None:
    typer.echo(json.dumps(payload))


async def _load_index(path: Path) -> DogIndex:
    return await DogIndex.from_path(path)


@app.command()
def lint(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a .dog.md file or directory containing .dog.md files",
            exists=True,
        ),
    ],
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.text,
) -> None:
    """Validate .dog.md files for structure and reference errors."""

    async def _lint() -> int:
        try:
            index = await _load_index(path)
        except ParseError as e:
            if output == OutputFormat.json:
                _json_echo({"issues": [], "error": str(e)})
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            if output == OutputFormat.json:
                _json_echo({"issues": [], "error": "No .dog.md files found"})
            else:
                typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        if output == OutputFormat.text:
            typer.echo(f"Linting {len(index.documents)} file(s)...", err=True)

        result = await lint_documents(index)

        if output == OutputFormat.json:
            _json_echo(
                {
                    "issues": [
                        {
                            "file": str(issue.file_path),
                            "line": issue.line_number,
                            "message": issue.message,
                            "severity": issue.severity,
                        }
                        for issue in result.issues
                    ],
                    "errors": len(result.errors),
                    "warnings": len(result.warnings),
                }
            )
            return 1 if result.has_errors else 0

        # Print issues grouped by file
        for issue in result.issues:
            color = typer.colors.RED if issue.severity == "error" else typer.colors.YELLOW
            line_info = f":{issue.line_number}" if issue.line_number else ""
            typer.secho(
                f"{issue.file_path}{line_info}: [{issue.severity}] {issue.message}",
                fg=color,
            )

        # Summary
        error_count = len(result.errors)
        warning_count = len(result.warnings)

        if error_count == 0 and warning_count == 0:
            typer.secho("All files valid!", fg=typer.colors.GREEN)
            return 0

        typer.echo(f"\nFound {error_count} error(s), {warning_count} warning(s)")
        return 1 if error_count > 0 else 0

    exit_code = asyncio.run(_lint())
    raise typer.Exit(code=exit_code)


@app.command(name="format")
def format_cmd(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a .dog.md file or directory containing .dog.md files",
            exists=True,
        ),
    ],
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Check if files are formatted without modifying them",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.text,
) -> None:
    """Format .dog.md files (normalize whitespace and indentation)."""

    async def _format() -> int:
        files = await find_dog_files(path)

        if not files:
            if output == OutputFormat.json:
                _json_echo({"changed": [], "error": "No .dog.md files found"})
            else:
                typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        changed_files: list[str] = []

        for file_path in files:
            if check:
                from dog_core import format_file

                changed, _ = await format_file(file_path)
                if changed:
                    changed_files.append(str(file_path))
                    if output == OutputFormat.text:
                        typer.echo(f"Would reformat: {file_path}")
            else:
                changed = await format_file_in_place(file_path)
                if changed:
                    changed_files.append(str(file_path))
                    if output == OutputFormat.text:
                        typer.echo(f"Formatted: {file_path}")

        if output == OutputFormat.json:
            _json_echo(
                {
                    "check": check,
                    "changed": changed_files,
                    "count": len(changed_files),
                    "scanned": len(files),
                }
            )
            if check and changed_files:
                return 1
            return 0

        if check:
            if changed_files:
                typer.echo(f"\n{len(changed_files)} file(s) would be reformatted")
                return 1
            typer.secho("All files already formatted!", fg=typer.colors.GREEN)
            return 0

        if changed_files:
            typer.echo(f"\nFormatted {len(changed_files)} file(s)")
        else:
            typer.echo("All files already formatted")
        return 0

    exit_code = asyncio.run(_format())
    raise typer.Exit(code=exit_code)


@app.command()
def index(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to directory containing .dog.md files, or path to output index.dog.md file",
        ),
    ],
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Project name for the index",
        ),
    ],
) -> None:
    """Generate or update a Project index file (index.dog.md)."""

    async def _index() -> int:
        # Determine search path and output path
        if path.is_file():
            if not path.name.endswith("index.dog.md"):
                typer.secho(
                    "Output file must be named 'index.dog.md'",
                    fg=typer.colors.RED,
                    err=True,
                )
                return 1
            output_path = path
            search_path = path.parent
        else:
            if not path.exists():
                typer.secho(f"Directory does not exist: {path}", fg=typer.colors.RED, err=True)
                return 1
            search_path = path
            output_path = path / "index.dog.md"

        try:
            dog_index = await _load_index(search_path)
        except ParseError as e:
            typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not dog_index.documents:
            typer.echo(f"No .dog.md files found in {search_path}", err=True)

        await generate_index(dog_index.documents, name, output_path)
        typer.secho(f"Generated index: {output_path}", fg=typer.colors.GREEN)
        return 0

    exit_code = asyncio.run(_index())
    raise typer.Exit(code=exit_code)


@app.command()
def search(  # noqa: C901
    query: Annotated[
        str,
        typer.Argument(help="Search query string (use @/!/#/& prefix for type filter)"),
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum number of results",
        ),
    ] = 10,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.json,
    min_score: Annotated[
        float,
        typer.Option(
            "--min-score",
            help="Minimum relevance score to include",
        ),
    ] = 40.0,
    all_results: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Include low-confidence matches",
        ),
    ] = False,
) -> None:
    """Search DOG documents by name or content.

    Use primitive marks to filter by type:
      @query - Actor
      !query - Behavior
      #query - Component
      &query - Data
    """

    async def _search() -> int:  # noqa: C901
        # Parse primitive query for type filter
        actual_query, ptype = parse_primitive_query(query)

        try:
            index = await _load_index(path)
        except ParseError as e:
            if output == OutputFormat.json:
                _json_echo({"results": [], "error": str(e)})
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            if output == OutputFormat.json:
                _json_echo({"results": [], "error": "No .dog.md files found"})
            else:
                typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        threshold = 0.0 if all_results else min_score
        results = await search_documents(index, actual_query, type_filter=ptype, limit=limit, min_score=threshold)

        if output == OutputFormat.json:
            _json_echo({"results": [r.to_dict() for r in results]})
        else:
            if not results:
                typer.echo(f"No results found for '{query}'")
                return 0

            for r in results:
                typer.secho(f"{r.primitive_type.value}: {r.name}", fg=typer.colors.GREEN)
                typer.echo(f"  File: {r.file_path}")
                typer.echo(f"  {r.snippet}")
                typer.echo()

        return 0

    exit_code = asyncio.run(_search())
    raise typer.Exit(code=exit_code)


@app.command()
def get(  # noqa: C901
    name: Annotated[
        str,
        typer.Argument(help="Name of the primitive to get (use @/!/#/& prefix for type filter)"),
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.json,
    depth: Annotated[
        int,
        typer.Option(
            "--depth",
            help="Expand referenced documents up to N hops",
            min=0,
        ),
    ] = 0,
) -> None:
    """Get a DOG document by name with resolved references.

    Use primitive marks to filter by type:
      @name - Actor
      !name - Behavior
      #name - Component
      &name - Data
    """

    async def _get() -> int:  # noqa: C901
        # Parse primitive query for type filter
        actual_name, ptype = parse_primitive_query(name)

        if not actual_name:
            if output == OutputFormat.json:
                _json_echo({"error": "Name is required"})
            else:
                typer.secho("Name is required", fg=typer.colors.RED, err=True)
            return 1

        try:
            index = await _load_index(path)
        except ParseError as e:
            if output == OutputFormat.json:
                _json_echo({"error": str(e)})
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            if output == OutputFormat.json:
                _json_echo({"error": "No .dog.md files found"})
            else:
                typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        try:
            result = await get_document(index, actual_name, type_filter=ptype, depth=depth)
        except AmbiguousLookupError as e:
            if output == OutputFormat.json:
                _json_echo({"error": str(e)})
            else:
                typer.secho(str(e), fg=typer.colors.RED, err=True)
            return 1

        if result is None:
            if output == OutputFormat.json:
                _json_echo({"error": f"Not found: {name}"})
            else:
                typer.secho(f"Not found: {name}", fg=typer.colors.RED, err=True)
            return 1

        if output == OutputFormat.json:
            _json_echo(result.to_dict())
        else:
            typer.echo(result.to_text())

        return 0

    exit_code = asyncio.run(_get())
    raise typer.Exit(code=exit_code)


@app.command(name="list")
def list_cmd(  # noqa: C901
    type_filter: Annotated[
        str | None,
        typer.Argument(help="Type filter: @ (Actor), ! (Behavior), # (Component), & (Data)"),
    ] = None,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.json,
) -> None:
    """List all DOG documents.

    Use primitive marks to filter by type:
      @  - List Actors
      !  - List Behaviors
      #  - List Components
      &  - List Data
    """

    async def _list() -> int:  # noqa: C901
        # Parse type filter from sigil
        ptype: PrimitiveType | None = None
        if type_filter:
            _, ptype = parse_primitive_query(type_filter)
            if ptype is None:
                # Invalid filter - not a recognized sigil
                if output == OutputFormat.json:
                    _json_echo({"documents": [], "error": "Invalid filter. Use @, !, #, or &"})
                else:
                    typer.secho("Invalid filter. Use @, !, #, or &", fg=typer.colors.RED, err=True)
                return 1

        try:
            index = await _load_index(path)
        except ParseError as e:
            if output == OutputFormat.json:
                _json_echo({"documents": [], "error": str(e)})
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            if output == OutputFormat.json:
                _json_echo({"documents": []})
            else:
                typer.echo(f"No .dog.md files found in {path}")
            return 0

        results = await list_documents(index, type_filter=ptype)

        if output == OutputFormat.json:
            _json_echo({"documents": results})
        else:
            if not results:
                typer.echo("No documents found")
                return 0

            # Group by type
            by_type: dict[str, list[dict]] = {}
            for r in results:
                by_type.setdefault(r["type"], []).append(r)

            for ptype_name, items in by_type.items():
                typer.secho(f"\n{ptype_name}s:", fg=typer.colors.GREEN, bold=True)
                for item in items:
                    typer.echo(f"  {item['name']}")
                    typer.echo(f"    {item['file']}")

        return 0

    exit_code = asyncio.run(_list())
    raise typer.Exit(code=exit_code)


@app.command()
def refs(
    query: Annotated[
        str,
        typer.Argument(help="Name of the primitive to find references to (use @/!/#/& prefix for type filter)"),
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format",
        ),
    ] = OutputFormat.json,
) -> None:
    """Find all documents that reference a given primitive (reverse lookup).

    Use primitive marks to filter by type:
      @name - Actor
      !name - Behavior
      #name - Component
      &name - Data

    Example:
      dog refs "#AuthService"  # Find everything that references AuthService
    """

    async def _refs() -> int:
        try:
            index = await _load_index(path)
        except ParseError as e:
            if output == OutputFormat.json:
                _json_echo({"error": str(e)})
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            if output == OutputFormat.json:
                _json_echo({"error": "No .dog.md files found"})
            else:
                typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        result = await find_refs(index, query)

        if output == OutputFormat.json:
            _json_echo(result.to_dict())
        else:
            typer.echo(result.to_text())

        return 0

    exit_code = asyncio.run(_refs())
    raise typer.Exit(code=exit_code)


@app.command()
def graph(
    root: Annotated[
        str | None,
        typer.Argument(help="Optional root node to generate subgraph from (use @/!/#/& prefix)"),
    ] = None,
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Generate a DOT format dependency graph.

    Output can be piped to graphviz for rendering:
      dog graph | dot -Tpng -o graph.png
      dog graph "!Login" | dot -Tsvg -o login.svg

    Use primitive marks to filter root by type:
      @name - Actor
      !name - Behavior
      #name - Component
      &name - Data
    """

    async def _graph() -> int:
        try:
            index = await _load_index(path)
        except ParseError as e:
            typer.secho(f"Parse error: {e}", fg=typer.colors.RED, err=True)
            return 1

        if not index.documents:
            typer.echo(f"No .dog.md files found in {path}", err=True)
            return 1

        dot_output = await generate_graph(index, root=root)
        typer.echo(dot_output)

        return 0

    exit_code = asyncio.run(_graph())
    raise typer.Exit(code=exit_code)


@app.command(name="export")
def export_cmd(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
    type_filter: Annotated[
        str | None,
        typer.Option(
            "--type",
            "-t",
            help="Type filter: @ (Actor), ! (Behavior), # (Component), & (Data)",
        ),
    ] = None,
    no_raw: Annotated[
        bool,
        typer.Option(
            "--no-raw",
            help="Exclude raw markdown content from output",
        ),
    ] = False,
) -> None:
    """Export all DOG documents as JSON.

    Outputs a JSON array of all documents with their sections and references.
    Useful for feeding context to AI agents.

    Example:
      dog export -p docs/ > context.json
      dog export -t ! -p docs/  # Export only behaviors
    """

    async def _export() -> int:
        # Parse type filter from sigil
        ptype: PrimitiveType | None = None
        if type_filter:
            _, ptype = parse_primitive_query(type_filter)
            if ptype is None:
                typer.secho("Invalid filter. Use @, !, #, or &", fg=typer.colors.RED, err=True)
                return 1

        try:
            index = await _load_index(path)
        except ParseError as e:
            _json_echo({"documents": [], "error": str(e)})
            return 1

        if not index.documents:
            _json_echo({"documents": [], "error": "No .dog.md files found"})
            return 1

        results = await export_documents(index, type_filter=ptype, include_raw=not no_raw)
        _json_echo({"documents": results, "count": len(results)})

        return 0

    exit_code = asyncio.run(_export())
    raise typer.Exit(code=exit_code)


@app.command()
def serve(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to directory containing .dog.md files",
            exists=True,
        ),
    ] = Path("."),
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="Host to bind to",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-P",
            help="Port to bind to",
        ),
    ] = 8000,
    no_reload: Annotated[
        bool,
        typer.Option(
            "--no-reload",
            help="Disable hot-reload on file changes",
        ),
    ] = False,
) -> None:
    """Serve DOG documentation as HTML in the browser.

    Starts a local web server that renders .dog.md files as HTML pages
    with color-coded reference links. Hot-reload is enabled by default.
    """
    from dog_core.server import run_server

    typer.echo("Starting DOG documentation server...")
    typer.echo(f"Serving docs from: {path.resolve()}")
    typer.echo(f"Open http://{host}:{port} in your browser")
    if not no_reload:
        typer.echo("Hot-reload enabled - changes will be reflected automatically")
    typer.echo()

    asyncio.run(run_server(path, host=host, port=port, reload=not no_reload))


if __name__ == "__main__":
    app()

import asyncio
import json
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from dog_core import (
    ParseError,
    PatchData,
    PrimitiveType,
    find_dog_files,
    format_file_in_place,
    generate_index,
    get_document,
    lint_documents,
    list_documents,
    parse_documents,
    parse_primitive_query,
    patch_document,
    search_documents,
)


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


app = typer.Typer(
    name="dog",
    help="DOG (Documentation Oriented Grammar) CLI tool",
    no_args_is_help=True,
)


@app.command()
def lint(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a .dog.md file or directory containing .dog.md files",
            exists=True,
        ),
    ],
) -> None:
    """Validate .dog.md files for structure and reference errors."""

    async def _lint() -> int:
        files = await find_dog_files(path)

        if not files:
            typer.echo(f"No .dog.md files found in {path}")
            return 1

        typer.echo(f"Linting {len(files)} file(s)...")

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        result = await lint_documents(docs)

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
) -> None:
    """Format .dog.md files (normalize whitespace and indentation)."""

    async def _format() -> int:
        files = await find_dog_files(path)

        if not files:
            typer.echo(f"No .dog.md files found in {path}")
            return 1

        changed_count = 0

        for file_path in files:
            if check:
                # Just check, don't modify
                from dog_core import format_file

                changed, _ = await format_file(file_path)
                if changed:
                    typer.echo(f"Would reformat: {file_path}")
                    changed_count += 1
            else:
                changed = await format_file_in_place(file_path)
                if changed:
                    typer.echo(f"Formatted: {file_path}")
                    changed_count += 1

        if check:
            if changed_count > 0:
                typer.echo(f"\n{changed_count} file(s) would be reformatted")
                return 1
            typer.secho("All files already formatted!", fg=typer.colors.GREEN)
            return 0

        if changed_count > 0:
            typer.echo(f"\nFormatted {changed_count} file(s)")
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
                )
                return 1
            output_path = path
            search_path = path.parent
        else:
            if not path.exists():
                typer.secho(f"Directory does not exist: {path}", fg=typer.colors.RED)
                return 1
            search_path = path
            output_path = path / "index.dog.md"

        files = await find_dog_files(search_path)

        if not files:
            typer.echo(f"No .dog.md files found in {search_path}")

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        await generate_index(docs, name, output_path)
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
    ] = OutputFormat.text,
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

        files = await find_dog_files(path)

        if not files:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"results": [], "error": "No .dog.md files found"}))
            else:
                typer.echo(f"No .dog.md files found in {path}")
            return 1

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"results": [], "error": str(e)}))
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        results = await search_documents(docs, actual_query, type_filter=ptype, limit=limit)

        if output == OutputFormat.json:
            typer.echo(json.dumps({"results": [r.to_dict() for r in results]}))
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
    ] = OutputFormat.text,
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
                typer.echo(json.dumps({"error": "Name is required"}))
            else:
                typer.secho("Name is required", fg=typer.colors.RED)
            return 1

        files = await find_dog_files(path)

        if not files:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"error": "No .dog.md files found"}))
            else:
                typer.echo(f"No .dog.md files found in {path}")
            return 1

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"error": str(e)}))
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        result = await get_document(docs, actual_name, type_filter=ptype)

        if result is None:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"error": f"Not found: {name}"}))
            else:
                typer.secho(f"Not found: {name}", fg=typer.colors.RED)
            return 1

        if output == OutputFormat.json:
            typer.echo(json.dumps(result.to_dict()))
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
    ] = OutputFormat.text,
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
                    typer.echo(json.dumps({"documents": [], "error": "Invalid filter. Use @, !, #, or &"}))
                else:
                    typer.secho("Invalid filter. Use @, !, #, or &", fg=typer.colors.RED)
                return 1

        files = await find_dog_files(path)

        if not files:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"documents": []}))
            else:
                typer.echo(f"No .dog.md files found in {path}")
            return 0

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            if output == OutputFormat.json:
                typer.echo(json.dumps({"documents": [], "error": str(e)}))
            else:
                typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        results = await list_documents(docs, type_filter=ptype)

        if output == OutputFormat.json:
            typer.echo(json.dumps({"documents": results}))
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
def patch(
    name: Annotated[
        str,
        typer.Argument(help="Name of the primitive to patch (use @/!/#/& prefix for type filter)"),
    ],
    data: Annotated[
        str,
        typer.Option(
            "--data",
            "-d",
            help='JSON patch data, e.g. \'{"sections": {"Description": "New content"}}\'',
        ),
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to search in (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Patch a DOG document with JSON data to update specific sections.

    Use primitive marks to filter by type:
      @name - Actor
      !name - Behavior
      #name - Component
      &name - Data

    Example:
      dog patch "@User" --data '{"sections": {"Description": "Updated description"}}'
    """

    async def _patch() -> int:
        # Parse primitive query for type filter
        actual_name, ptype = parse_primitive_query(name)

        if not actual_name:
            typer.secho("Name is required", fg=typer.colors.RED)
            return 1

        # Parse JSON data
        try:
            patch_dict = json.loads(data)
            patch_data = PatchData(**patch_dict)
        except json.JSONDecodeError as e:
            typer.secho(f"Invalid JSON: {e}", fg=typer.colors.RED)
            return 1
        except ValueError as e:
            typer.secho(f"Invalid patch data: {e}", fg=typer.colors.RED)
            return 1

        files = await find_dog_files(path)

        if not files:
            typer.echo(f"No .dog.md files found in {path}")
            return 1

        try:
            docs = await parse_documents(files)
        except ParseError as e:
            typer.secho(f"Parse error: {e}", fg=typer.colors.RED)
            return 1

        result = await patch_document(docs, actual_name, patch_data, type_filter=ptype)

        if result.success:
            typer.secho(f"Patched: {result.file_path}", fg=typer.colors.GREEN)
            if result.updated_sections:
                typer.echo(f"Updated sections: {', '.join(result.updated_sections)}")
        else:
            typer.secho(f"Error: {result.error}", fg=typer.colors.RED)

        return 0 if result.success else 1

    exit_code = asyncio.run(_patch())
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
            "-h",
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

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from dog_core import (
    ParseError,
    find_dog_files,
    format_file_in_place,
    generate_index,
    lint_documents,
    parse_documents,
)


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


if __name__ == "__main__":
    app()

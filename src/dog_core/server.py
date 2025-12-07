"""FastAPI server for serving DOG documentation as HTML."""

import asyncio
import re
from collections.abc import Callable
from pathlib import Path

import marko
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from dog_core.finder import find_dog_files
from dog_core.models import SIGIL_MAP, DogDocument, PrimitiveType
from dog_core.parser import parse_documents


# Create a GFM-enabled markdown parser for table support
_md_parser = marko.Markdown(renderer=marko.html_renderer.HTMLRenderer)
_md_parser.use("gfm")


def _convert_md(text: str) -> str:
    """Convert markdown to HTML with GFM support (tables, etc.)."""
    return _md_parser(text)


# Reverse sigil map for type -> sigil lookup
TYPE_TO_SIGIL: dict[PrimitiveType, str] = {v: k for k, v in SIGIL_MAP.items()}

# HTML-escaped sigils for matching after marko conversion
ESCAPED_SIGIL_MAP: dict[str, PrimitiveType] = {
    "@": PrimitiveType.ACTOR,
    "!": PrimitiveType.BEHAVIOR,
    "#": PrimitiveType.COMPONENT,
    "&amp;": PrimitiveType.DATA,  # & is escaped to &amp; by marko
}


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --actor: #a22041;
            --behavior: #457b9d;
            --component: #915c8b;
            --data: #2a9d8f;
            --black: #000;
            --gray: #666;
            --light: #f8f8f8;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #fff;
            color: var(--black);
            font-size: 15px;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}
        .page {{
            max-width: 720px;
            margin: 0 auto;
            padding: 3rem 2rem 6rem;
        }}
        header {{
            margin-bottom: 4rem;
        }}
        header a {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: var(--black);
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}
        header img {{
            width: 24px;
            height: 24px;
        }}
        header a:hover {{
            opacity: 0.6;
        }}
        .content h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.1;
            margin-bottom: 2rem;
        }}
        .content h2 {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--gray);
            margin-top: 3rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #eee;
        }}
        .content p {{
            color: #333;
            margin-bottom: 1.25rem;
            max-width: 60ch;
        }}
        .content ul {{
            list-style: none;
            margin-bottom: 1.5rem;
        }}
        .content li {{
            padding: 0.4rem 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        .content li:last-child {{
            border-bottom: none;
        }}
        .content a {{
            color: var(--black);
            text-decoration: none;
            font-weight: 500;
            transition: opacity 0.15s;
        }}
        .content a:hover {{
            opacity: 0.5;
        }}
        .content code {{
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.85em;
            background: var(--light);
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-size: 0.9em;
        }}
        .content th, .content td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .content th {{
            font-weight: 600;
            color: var(--gray);
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .content tr:hover {{
            background: var(--light);
        }}
        .content a.ref-actor, a.ref-actor, .ref-actor {{ color: var(--actor); }}
        .content a.ref-behavior, a.ref-behavior, .ref-behavior {{ color: var(--behavior); }}
        .content a.ref-component, a.ref-component, .ref-component {{ color: var(--component); }}
        .content a.ref-data, a.ref-data, .ref-data {{ color: var(--data); }}
        .content a.ref-project, a.ref-project, .ref-project {{ color: var(--black); }}
    </style>
</head>
<body>
    <div class="page">
        <header>
            <a href="/">
                <img src="/favicon.png" alt="">
                <span>Documentation</span>
            </a>
        </header>
        <main class="content">
            {content}
        </main>
    </div>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --actor: #a22041;
            --behavior: #457b9d;
            --component: #915c8b;
            --data: #2a9d8f;
            --black: #000;
            --gray: #666;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #fff;
            color: var(--black);
            font-size: 15px;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}
        .page {{
            max-width: 720px;
            margin: 0 auto;
            padding: 3rem 2rem 6rem;
        }}
        header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 4rem;
        }}
        header img {{
            width: 40px;
            height: 40px;
        }}
        header h1 {{
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}
        h2 {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--gray);
            margin-top: 3rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #eee;
        }}
        .doc-list {{
            list-style: none;
        }}
        .doc-list li {{
            padding: 0.4rem 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        .doc-list li:last-child {{
            border-bottom: none;
        }}
        .doc-list a {{
            text-decoration: none;
            font-weight: 500;
            transition: opacity 0.15s;
        }}
        .doc-list a:hover {{
            opacity: 0.5;
        }}
        .content a.ref-actor, a.ref-actor, .ref-actor {{ color: var(--actor); }}
        .content a.ref-behavior, a.ref-behavior, .ref-behavior {{ color: var(--behavior); }}
        .content a.ref-component, a.ref-component, .ref-component {{ color: var(--component); }}
        .content a.ref-data, a.ref-data, .ref-data {{ color: var(--data); }}
        .content a.ref-project, a.ref-project, .ref-project {{ color: var(--black); }}
    </style>
</head>
<body>
    <div class="page">
        <header>
            <img src="/favicon.png" alt="">
            <h1>Documentation</h1>
        </header>
        <main>
            {content}
        </main>
    </div>
</body>
</html>
"""


class MarkdownFile:
    """Simple container for regular markdown files."""

    def __init__(self, file_path: Path, docs_path: Path) -> None:
        self.file_path = file_path
        self.name = file_path.stem
        # Get relative path from docs root for grouping
        self.relative_path = file_path.relative_to(docs_path)
        self.folder = str(self.relative_path.parent) if self.relative_path.parent != Path(".") else ""
        self.raw_content = file_path.read_text()


class DocServer:
    """Server for DOG documentation with hot-reload support."""

    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path.resolve()
        self.favicon_path = self._find_favicon()
        self.docs: list[DogDocument] = []
        self.docs_by_name: dict[str, DogDocument] = {}
        self.markdown_files: list[MarkdownFile] = []
        self.markdown_by_name: dict[str, MarkdownFile] = {}
        self.app = FastAPI(title="DOG Documentation Server")
        self._setup_routes()

    def _find_favicon(self) -> Path | None:
        """Find favicon.png or dog.png in docs path or parent directories."""
        search_paths = [self.docs_path, self.docs_path.parent]
        for base in search_paths:
            for name in ["favicon.png", "dog.png"]:
                path = base / name
                if path.exists():
                    return path
        return None

    def _find_index_doc(self) -> DogDocument | None:
        """Find index.dog.md document by file name."""
        for doc in self.docs:
            if doc.file_path.name == "index.dog.md":
                return doc
        return None

    async def load_docs(self) -> None:
        """Load or reload all documents from disk."""
        # Load .dog.md files
        files = await find_dog_files(self.docs_path)
        if files:
            self.docs = await parse_documents(files)
            self.docs_by_name = {doc.name.lower(): doc for doc in self.docs}
        else:
            self.docs = []
            self.docs_by_name = {}

        # Load regular .md files (excluding .dog.md)
        self.markdown_files = []
        self.markdown_by_name = {}
        for md_path in self.docs_path.rglob("*.md"):
            if not md_path.name.endswith(".dog.md"):
                md_file = MarkdownFile(md_path, self.docs_path)
                self.markdown_files.append(md_file)
                self.markdown_by_name[md_file.name.lower()] = md_file

    def _setup_routes(self) -> None:
        """Set up FastAPI routes."""

        @self.app.get("/favicon.png", response_model=None)
        async def favicon() -> FileResponse | HTMLResponse:
            if self.favicon_path and self.favicon_path.exists():
                return FileResponse(self.favicon_path, media_type="image/png")
            return HTMLResponse(content="", status_code=404)

        @self.app.get("/", response_class=HTMLResponse)
        async def index() -> str:
            await self.load_docs()
            # Try to find and render index.dog.md as homepage
            index_doc = self._find_index_doc()
            if index_doc:
                return self._render_doc_with_markdown_appendix(index_doc)
            # Fallback: render list of all documents
            return self._render_index()

        @self.app.get("/doc/{name:path}", response_class=HTMLResponse, response_model=None)
        async def get_doc(name: str) -> HTMLResponse:
            await self.load_docs()
            doc = self.docs_by_name.get(name.lower())
            if doc is not None:
                return HTMLResponse(content=self._render_doc(doc))

            # Check for regular markdown file
            md_file = self.markdown_by_name.get(name.lower())
            if md_file is not None:
                return HTMLResponse(content=self._render_markdown(md_file))

            return HTMLResponse(
                content=HTML_TEMPLATE.format(
                    title="Not Found",
                    content="<h1>Document Not Found</h1><p>The requested document does not exist.</p>",
                ),
                status_code=404,
            )

    def _render_index(self) -> str:  # noqa: C901
        """Render the index page with all documents grouped by type."""
        if not self.docs and not self.markdown_files:
            return INDEX_TEMPLATE.format(
                content="<p>No documents found. Add some .dog.md or .md files to your docs directory.</p>"
            )

        content_parts = []

        # Group DOG docs by type
        by_type: dict[PrimitiveType, list[DogDocument]] = {}
        for doc in self.docs:
            by_type.setdefault(doc.primitive_type, []).append(doc)

        # Sort each group by name
        for ptype in by_type:
            by_type[ptype].sort(key=lambda d: d.name.lower())

        # Render DOG groups in order
        type_order = [
            PrimitiveType.PROJECT,
            PrimitiveType.ACTOR,
            PrimitiveType.BEHAVIOR,
            PrimitiveType.COMPONENT,
            PrimitiveType.DATA,
        ]

        for ptype in type_order:
            docs = by_type.get(ptype, [])
            if not docs:
                continue

            ref_class = f"ref-{ptype.value.lower()}"
            content_parts.append(f"<h2>{ptype.value}s</h2>")
            content_parts.append('<ul class="doc-list">')
            for doc in docs:
                url = f"/doc/{doc.name}"
                content_parts.append(f'<li><a href="{url}" class="{ref_class}">{doc.name}</a></li>')
            content_parts.append("</ul>")

        # Group markdown files by folder
        if self.markdown_files:
            by_folder: dict[str, list[MarkdownFile]] = {}
            for md in self.markdown_files:
                by_folder.setdefault(md.folder, []).append(md)

            # Sort folders and files
            for folder in by_folder:
                by_folder[folder].sort(key=lambda m: m.name.lower())

            for folder in sorted(by_folder.keys()):
                files = by_folder[folder]
                header = folder if folder else "Other"
                content_parts.append(f"<h2>{header}</h2>")
                content_parts.append('<ul class="doc-list">')
                for md in files:
                    url = f"/doc/{md.name}"
                    content_parts.append(f'<li><a href="{url}">{md.name}</a></li>')
                content_parts.append("</ul>")

        return INDEX_TEMPLATE.format(content="\n".join(content_parts))

    def _render_doc(self, doc: DogDocument) -> str:
        """Render a single document as HTML."""
        # Convert markdown to HTML
        html_content = _convert_md(doc.raw_content)

        # Convert .dog.md links to /doc/ links with color classes
        html_content = self._convert_doc_links(html_content)

        # Convert reference links to colored links
        html_content = self._convert_references(html_content)

        return HTML_TEMPLATE.format(
            title=f"{doc.primitive_type.value}: {doc.name}",
            content=html_content,
        )

    def _render_doc_with_markdown_appendix(self, doc: DogDocument) -> str:
        """Render a document with markdown files appended (for index page)."""
        # Convert markdown to HTML
        html_content = _convert_md(doc.raw_content)

        # Convert .dog.md links to /doc/ links with color classes
        html_content = self._convert_doc_links(html_content)

        # Convert reference links to colored links
        html_content = self._convert_references(html_content)

        # Append markdown files grouped by folder
        if self.markdown_files:
            by_folder: dict[str, list[MarkdownFile]] = {}
            for md in self.markdown_files:
                by_folder.setdefault(md.folder, []).append(md)

            # Sort folders and files
            for folder in by_folder:
                by_folder[folder].sort(key=lambda m: m.name.lower())

            for folder in sorted(by_folder.keys()):
                files = by_folder[folder]
                header = folder if folder else "Other"
                html_content += f"<h2>{header}</h2>\n<ul>\n"
                for md in files:
                    url = f"/doc/{md.name}"
                    html_content += f'<li><a href="{url}">{md.name}</a></li>\n'
                html_content += "</ul>\n"

        return HTML_TEMPLATE.format(
            title=f"{doc.primitive_type.value}: {doc.name}",
            content=html_content,
        )

    def _render_markdown(self, md_file: MarkdownFile) -> str:
        """Render a regular markdown file as HTML."""
        html_content = _convert_md(md_file.raw_content)

        # Convert .dog.md links to /doc/ links with color classes
        html_content = self._convert_doc_links(html_content)

        # Convert regular .md links to /doc/ links
        html_content = self._convert_md_links(html_content)

        # Convert reference links to colored links
        html_content = self._convert_references(html_content)

        return HTML_TEMPLATE.format(
            title=md_file.name,
            content=html_content,
        )

    def _convert_doc_links(self, html: str) -> str:
        """Convert relative .dog.md links to /doc/ links with color classes."""
        # Match <a href="something.dog.md">text</a> pattern
        pattern = r'<a href="([^"]*?)\.dog\.md">([^<]+)</a>'

        def replace_link(match: re.Match[str]) -> str:
            path = match.group(1)
            link_text = match.group(2)
            # Get just the filename part (last component)
            filename = path.split("/")[-1]
            # Find the document by filename
            # Note: file_path.stem is "name.dog", so we need to strip ".dog"
            for doc in self.docs:
                doc_stem = doc.file_path.stem
                if doc_stem.endswith(".dog"):
                    doc_stem = doc_stem[:-4]
                if doc_stem == filename:
                    ref_class = f"ref-{doc.primitive_type.value.lower()}"
                    return f'<a href="/doc/{doc.name}" class="{ref_class}">{link_text}</a>'
            # Fallback: use filename as-is, no color class
            return f'<a href="/doc/{filename}">{link_text}</a>'

        return re.sub(pattern, replace_link, html)

    def _convert_md_links(self, html: str) -> str:
        """Convert relative .md links to /doc/ links."""
        # Match <a href="something.md">text</a> pattern (but not .dog.md)
        pattern = r'<a href="([^"]*?)(?<!\.dog)\.md">([^<]+)</a>'

        def replace_link(match: re.Match[str]) -> str:
            path = match.group(1)
            link_text = match.group(2)
            # Get just the filename part (last component)
            filename = path.split("/")[-1]
            return f'<a href="/doc/{filename}">{link_text}</a>'

        return re.sub(pattern, replace_link, html)

    def _convert_references(self, html: str) -> str:
        """Convert inline references like `@User` to colored links."""
        # Pattern matches backtick-wrapped references: `@Name`, `!Name`, `#Name`, `&Name`
        # The backticks are converted to <code> tags by marko
        # Note: & is HTML-escaped to &amp; by marko, so we use ESCAPED_SIGIL_MAP
        for sigil, ptype in ESCAPED_SIGIL_MAP.items():
            ref_class = f"ref-{ptype.value.lower()}"

            # Match <code>@Name</code> or <code>&amp;Name</code> pattern
            pattern = rf"<code>({re.escape(sigil)})([^<]+)</code>"

            def make_replace_ref(css_class: str) -> Callable[[re.Match[str]], str]:
                def replace_ref(match: re.Match[str]) -> str:
                    name = match.group(2)
                    # Check if document exists
                    if name.lower() in self.docs_by_name:
                        return f'<a href="/doc/{name}" class="{css_class}">{name}</a>'
                    # Document doesn't exist - still show colored but no link
                    return f'<span class="{css_class}">{name}</span>'

                return replace_ref

            html = re.sub(pattern, make_replace_ref(ref_class), html)

        return html


def create_server(docs_path: Path) -> DocServer:
    """Create a new documentation server instance."""
    return DocServer(docs_path)


async def run_server(
    docs_path: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
) -> None:
    """Run the documentation server."""
    import uvicorn
    from watchfiles import awatch

    server = create_server(docs_path)
    await server.load_docs()

    config = uvicorn.Config(
        server.app,
        host=host,
        port=port,
        log_level="info",
    )
    uv_server = uvicorn.Server(config)

    if reload:
        # Run server with file watching for hot-reload
        async def watch_and_reload() -> None:
            async for _ in awatch(docs_path, recursive=True):
                await server.load_docs()
                print(f"Reloaded {len(server.docs)} document(s)")

        # Run both server and watcher
        await asyncio.gather(
            uv_server.serve(),
            watch_and_reload(),
        )
    else:
        await uv_server.serve()

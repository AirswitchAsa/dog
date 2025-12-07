import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dog_core.server import DocServer, create_server


@pytest.fixture
def server_dog_dir(
    tmp_path: Path,
    sample_actor: str,
    sample_behavior: str,
    sample_data: str,
) -> Path:
    """Create a temporary directory with sample .dog.md files for server testing."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "user.dog.md").write_text(sample_actor)
    (docs_dir / "login.dog.md").write_text(sample_behavior)
    (docs_dir / "user-credentials.dog.md").write_text(sample_data)

    return docs_dir


@pytest.fixture
def server_with_index(server_dog_dir: Path, sample_project: str) -> Path:
    """Create a server directory with an index.dog.md file."""
    (server_dog_dir / "index.dog.md").write_text(sample_project)
    return server_dog_dir


@pytest.fixture
def server_with_favicon(server_dog_dir: Path) -> Path:
    """Create a server directory with a favicon.png file."""
    # Create a minimal PNG (1x1 transparent pixel)
    png_data = bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR chunk
            0x00,
            0x00,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,
            0x08,
            0x06,
            0x00,
            0x00,
            0x00,
            0x1F,
            0x15,
            0xC4,
            0x89,
            0x00,
            0x00,
            0x00,
            0x0A,
            0x49,
            0x44,
            0x41,  # IDAT chunk
            0x54,
            0x08,
            0xD7,
            0x63,
            0x00,
            0x01,
            0x00,
            0x00,
            0x05,
            0x00,
            0x01,
            0x6D,
            0xA2,
            0xD5,
            0xAE,
            0x00,
            0x00,
            0x00,
            0x00,
            0x49,
            0x45,
            0x4E,
            0x44,
            0xAE,  # IEND chunk
            0x42,
            0x60,
            0x82,
        ]
    )
    (server_dog_dir / "favicon.png").write_bytes(png_data)
    return server_dog_dir


def _run_async(coro: Coroutine) -> Any:  # noqa: ANN401
    """Helper to run async code in sync fixtures."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestDocServer:
    """Tests for DocServer class."""

    def test_create_server(self, server_dog_dir: Path) -> None:
        """Test creating a DocServer instance."""
        server = create_server(server_dog_dir)
        assert isinstance(server, DocServer)
        assert server.docs_path == server_dog_dir.resolve()

    @pytest.mark.asyncio
    async def test_load_docs(self, server_dog_dir: Path) -> None:
        """Test loading documents."""
        server = create_server(server_dog_dir)
        await server.load_docs()
        assert len(server.docs) == 3  # user, login, user-credentials
        assert "user" in server.docs_by_name
        assert "login" in server.docs_by_name

    @pytest.mark.asyncio
    async def test_load_docs_empty_dir(self, tmp_path: Path) -> None:
        """Test loading from empty directory."""
        server = create_server(tmp_path)
        await server.load_docs()
        assert server.docs == []
        assert server.docs_by_name == {}


class TestServerRoutes:
    """Tests for FastAPI routes."""

    @pytest.fixture
    def client(self, server_dog_dir: Path) -> TestClient:
        """Create a test client for the server."""
        server = create_server(server_dog_dir)
        _run_async(server.load_docs())
        return TestClient(server.app)

    @pytest.fixture
    def client_with_index(self, server_with_index: Path) -> TestClient:
        """Create a test client for server with index."""
        server = create_server(server_with_index)
        _run_async(server.load_docs())
        return TestClient(server.app)

    @pytest.fixture
    def client_with_favicon(self, server_with_favicon: Path) -> TestClient:
        """Create a test client for server with favicon."""
        server = create_server(server_with_favicon)
        _run_async(server.load_docs())
        return TestClient(server.app)

    def test_index_route_without_index_file(self, client: TestClient) -> None:
        """Test index route when no index.dog.md exists."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Documentation" in response.text
        # Should list documents by type
        assert "Actor" in response.text
        assert "User" in response.text
        assert "Behavior" in response.text
        assert "Login" in response.text

    def test_index_route_with_index_file(self, client_with_index: TestClient) -> None:
        """Test index route when index.dog.md exists."""
        response = client_with_index.get("/")
        assert response.status_code == 200
        # Should render the index.dog.md content
        assert "TestApp" in response.text

    def test_doc_route_existing(self, client: TestClient) -> None:
        """Test getting an existing document."""
        response = client.get("/doc/User")
        assert response.status_code == 200
        assert "User" in response.text
        assert "Actor" in response.text

    def test_doc_route_case_insensitive(self, client: TestClient) -> None:
        """Test doc route is case-insensitive."""
        response = client.get("/doc/user")
        assert response.status_code == 200
        assert "User" in response.text

    def test_doc_route_not_found(self, client: TestClient) -> None:
        """Test 404 for non-existent document."""
        response = client.get("/doc/NonExistent")
        assert response.status_code == 404
        assert "Not Found" in response.text

    def test_favicon_not_found(self, client: TestClient) -> None:
        """Test favicon returns 404 when not present."""
        response = client.get("/favicon.png")
        assert response.status_code == 404

    def test_favicon_found(self, client_with_favicon: TestClient) -> None:
        """Test favicon returns 200 when present."""
        response = client_with_favicon.get("/favicon.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


class TestReferenceConversion:
    """Tests for reference link conversion."""

    @pytest.fixture
    def server(self, server_dog_dir: Path) -> DocServer:
        """Create a server instance."""
        server = create_server(server_dog_dir)
        _run_async(server.load_docs())
        return server

    def test_convert_actor_reference(self, server: DocServer) -> None:
        """Test converting @Actor references."""
        html = "<code>@User</code>"
        result = server._convert_references(html)
        assert 'href="/doc/User"' in result
        assert 'class="ref-actor"' in result

    def test_convert_behavior_reference(self, server: DocServer) -> None:
        """Test converting !Behavior references."""
        html = "<code>!Login</code>"
        result = server._convert_references(html)
        assert 'href="/doc/Login"' in result
        assert 'class="ref-behavior"' in result

    def test_convert_data_reference(self, server: DocServer) -> None:
        """Test converting &Data references (HTML-escaped)."""
        html = "<code>&amp;UserCredentials</code>"
        result = server._convert_references(html)
        assert 'href="/doc/UserCredentials"' in result
        assert 'class="ref-data"' in result

    def test_convert_unknown_reference(self, server: DocServer) -> None:
        """Test converting reference to non-existent document."""
        html = "<code>@Unknown</code>"
        result = server._convert_references(html)
        # Should still color but no link
        assert 'class="ref-actor"' in result
        assert "href=" not in result
        assert "<span" in result


class TestDocLinkConversion:
    """Tests for .dog.md link conversion."""

    @pytest.fixture
    def server(self, server_dog_dir: Path) -> DocServer:
        """Create a server instance."""
        server = create_server(server_dog_dir)
        _run_async(server.load_docs())
        return server

    def test_convert_simple_link(self, server: DocServer) -> None:
        """Test converting simple .dog.md links."""
        html = '<a href="user.dog.md">User</a>'
        result = server._convert_doc_links(html)
        assert 'href="/doc/User"' in result
        assert 'class="ref-actor"' in result

    def test_convert_relative_path_link(self, server: DocServer) -> None:
        """Test converting relative path .dog.md links."""
        html = '<a href="./user.dog.md">User</a>'
        result = server._convert_doc_links(html)
        assert 'href="/doc/User"' in result
        assert 'class="ref-actor"' in result

    def test_convert_hyphenated_link(self, server: DocServer) -> None:
        """Test converting hyphenated file .dog.md links."""
        html = '<a href="user-credentials.dog.md">UserCredentials</a>'
        result = server._convert_doc_links(html)
        assert 'href="/doc/UserCredentials"' in result
        assert 'class="ref-data"' in result

    def test_convert_behavior_link(self, server: DocServer) -> None:
        """Test converting behavior .dog.md links."""
        html = '<a href="login.dog.md">Login</a>'
        result = server._convert_doc_links(html)
        assert 'href="/doc/Login"' in result
        assert 'class="ref-behavior"' in result

    def test_preserve_non_dog_links(self, server: DocServer) -> None:
        """Test that non-.dog.md links are preserved."""
        html = '<a href="https://example.com">Example</a>'
        result = server._convert_doc_links(html)
        assert result == html


class TestMarkdownFileHandling:
    """Tests for regular markdown file handling."""

    @pytest.fixture
    def server_with_md(self, server_dog_dir: Path) -> Path:
        """Create a server directory with regular markdown files."""
        # Create a subfolder with markdown files
        subfolder = server_dog_dir / "guides"
        subfolder.mkdir()
        (subfolder / "getting-started.md").write_text("# Getting Started\n\nWelcome!")
        (server_dog_dir / "README.md").write_text("# README\n\nProject readme.")
        return server_dog_dir

    def test_load_markdown_files(self, server_with_md: Path) -> None:
        """Test loading regular markdown files."""
        server = create_server(server_with_md)
        _run_async(server.load_docs())
        assert len(server.markdown_files) == 2
        names = [m.name.lower() for m in server.markdown_files]
        assert "readme" in names
        assert "getting-started" in names

    def test_markdown_file_folder(self, server_with_md: Path) -> None:
        """Test markdown files are grouped by folder."""
        server = create_server(server_with_md)
        _run_async(server.load_docs())
        folders = {m.name: m.folder for m in server.markdown_files}
        assert folders.get("README") == ""
        assert folders.get("getting-started") == "guides"

    def test_markdown_route(self, server_with_md: Path) -> None:
        """Test serving regular markdown files."""
        server = create_server(server_with_md)
        _run_async(server.load_docs())
        client = TestClient(server.app)
        response = client.get("/doc/README")
        assert response.status_code == 200
        assert "README" in response.text

    def test_index_includes_markdown(self, server_with_md: Path) -> None:
        """Test index page includes markdown files."""
        server = create_server(server_with_md)
        _run_async(server.load_docs())
        client = TestClient(server.app)
        response = client.get("/")
        assert response.status_code == 200
        # Should show markdown files grouped by folder
        assert "guides" in response.text or "Other" in response.text


class TestFaviconDiscovery:
    """Tests for favicon discovery."""

    def test_find_favicon_png(self, tmp_path: Path) -> None:
        """Test finding favicon.png in docs directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "favicon.png").write_bytes(b"fake png")

        server = create_server(docs_dir)
        assert server.favicon_path == docs_dir / "favicon.png"

    def test_find_dog_png(self, tmp_path: Path) -> None:
        """Test finding dog.png as fallback."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "dog.png").write_bytes(b"fake png")

        server = create_server(docs_dir)
        assert server.favicon_path == docs_dir / "dog.png"

    def test_find_favicon_in_parent(self, tmp_path: Path) -> None:
        """Test finding favicon in parent directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (tmp_path / "favicon.png").write_bytes(b"fake png")

        server = create_server(docs_dir)
        assert server.favicon_path == tmp_path / "favicon.png"

    def test_no_favicon(self, tmp_path: Path) -> None:
        """Test when no favicon exists."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        server = create_server(docs_dir)
        assert server.favicon_path is None


class TestIndexDocDiscovery:
    """Tests for index.dog.md discovery."""

    @pytest.mark.asyncio
    async def test_find_index_doc(self, server_with_index: Path) -> None:
        """Test finding index.dog.md."""
        server = create_server(server_with_index)
        await server.load_docs()

        index_doc = server._find_index_doc()
        assert index_doc is not None
        assert index_doc.file_path.name == "index.dog.md"

    @pytest.mark.asyncio
    async def test_no_index_doc(self, server_dog_dir: Path) -> None:
        """Test when no index.dog.md exists."""
        server = create_server(server_dog_dir)
        await server.load_docs()

        index_doc = server._find_index_doc()
        assert index_doc is None

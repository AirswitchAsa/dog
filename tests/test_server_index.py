from pathlib import Path

from fastapi.testclient import TestClient

from dog_core.server import create_server


def test_server_lazy_loads_once_for_routes(tmp_path: Path) -> None:
    (tmp_path / "user.dog.md").write_text(
        "# Actor: User\n\n## Description\n\nA user.\n\n## Notes\n\n- note\n"
    )
    server = create_server(tmp_path)
    client = TestClient(server.app)

    response = client.get("/doc/User")

    assert response.status_code == 200
    assert server.loaded is True
    assert "User" in response.text


def test_index_doc_appends_markdown_files(tmp_path: Path) -> None:
    (tmp_path / "index.dog.md").write_text(
        "# Project: Demo\n\n"
        "## Description\n\nProject.\n\n"
        "## Actors\n\n- User\n\n"
        "## Behaviors\n\n- Login\n\n"
        "## Components\n\n- API\n\n"
        "## Data\n\n- Session\n\n"
        "## Notes\n\n- note\n"
    )
    guides = tmp_path / "guides"
    guides.mkdir()
    (guides / "intro.md").write_text("# Intro\n\nWelcome.")

    server = create_server(tmp_path)
    client = TestClient(server.app)
    response = client.get("/")

    assert response.status_code == 200
    assert "Demo" in response.text
    assert "guides" in response.text
    assert 'href="/doc/intro"' in response.text


def test_doc_link_falls_back_when_file_stem_is_ambiguous(tmp_path: Path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    (first / "same.dog.md").write_text(
        "# Actor: First\n\n## Description\n\nA.\n\n## Notes\n\n- note\n"
    )
    (second / "same.dog.md").write_text(
        "# Data: Second\n\n## Description\n\nD.\n\n## Fields\n\n- id\n\n## Notes\n\n- note\n"
    )
    server = create_server(tmp_path)
    TestClient(server.app).get("/")

    html = server._convert_doc_links('<a href="same.dog.md">Same</a>')

    assert html == '<a href="/doc/same">Same</a>'


def test_md_links_and_unknown_dog_links_fall_back(tmp_path: Path) -> None:
    server = create_server(tmp_path)

    assert server._render_index()
    assert server._convert_md_links('<a href="guides/intro.md">Intro</a>') == '<a href="/doc/intro">Intro</a>'
    assert server._convert_doc_links('<a href="missing.dog.md">Missing</a>') == '<a href="/doc/missing">Missing</a>'

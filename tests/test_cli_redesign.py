import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dog_cli.main import app


runner = CliRunner()


def write_valid_docs(path: Path) -> None:
    (path / "user.dog.md").write_text(
        "# Actor: User\n\n## Description\n\nA user.\n\n## Notes\n\n- note\n"
    )
    (path / "auth.dog.md").write_text(
        "# Component: AuthService\n\n"
        "## Description\n\nAuth.\n\n"
        "## State\n\n- ready\n\n"
        "## Events\n\n- login\n\n"
        "## Notes\n\n- note\n"
    )
    (path / "login.dog.md").write_text(
        "# Behavior: Login\n\n"
        "## Condition\n\n- `@User` arrives\n\n"
        "## Description\n\nThe `@User` uses `#AuthService`.\n\n"
        "## Outcome\n\n- session\n\n"
        "## Notes\n\n- note\n"
    )


class TestCliRedesignCoverage:
    def test_lint_json_output_reports_strict_errors(self, tmp_path: Path) -> None:
        file_path = tmp_path / "bad.dog.md"
        file_path.write_text("# Actor: User\n\n## Description\n\n\n")

        result = runner.invoke(app, ["lint", str(tmp_path), "--output", "json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["errors"] >= 1
        assert any("Missing required section" in issue["message"] for issue in data["issues"])

    def test_query_commands_default_to_json(self, tmp_path: Path) -> None:
        write_valid_docs(tmp_path)

        search_result = runner.invoke(app, ["search", "AuthService", "--path", str(tmp_path)])
        get_result = runner.invoke(app, ["get", "!Login", "--path", str(tmp_path), "--depth", "1"])
        list_result = runner.invoke(app, ["list", "--path", str(tmp_path)])
        refs_result = runner.invoke(app, ["refs", "#AuthService", "--path", str(tmp_path)])

        assert search_result.exit_code == 0
        assert json.loads(search_result.output)["results"][0]["name"] == "AuthService"

        assert get_result.exit_code == 0
        get_data = json.loads(get_result.output)
        assert get_data["name"] == "Login"
        assert {doc["name"] for doc in get_data["expanded_documents"]} == {"User", "AuthService"}

        assert list_result.exit_code == 0
        assert len(json.loads(list_result.output)["documents"]) == 3

        assert refs_result.exit_code == 0
        refs_data = json.loads(refs_result.output)
        assert refs_data["count"] == 1
        assert refs_data["referenced_by"][0]["name"] == "Login"

    def test_text_error_branches_for_query_commands(self, tmp_path: Path) -> None:
        invalid = tmp_path / "invalid.dog.md"
        invalid.write_text("# Invalid\n")

        search_result = runner.invoke(
            app,
            ["search", "User", "--path", str(tmp_path), "--output", "text"],
        )
        get_result = runner.invoke(
            app,
            ["get", "User", "--path", str(tmp_path), "--output", "text"],
        )
        list_result = runner.invoke(
            app,
            ["list", "--path", str(tmp_path), "--output", "text"],
        )
        refs_result = runner.invoke(
            app,
            ["refs", "User", "--path", str(tmp_path), "--output", "text"],
        )

        assert search_result.exit_code == 1
        assert get_result.exit_code == 1
        assert list_result.exit_code == 1
        assert refs_result.exit_code == 1
        assert "Parse error" in search_result.output
        assert "Parse error" in get_result.output
        assert "Parse error" in list_result.output
        assert "Parse error" in refs_result.output

    def test_search_all_and_min_score_controls(self, tmp_path: Path) -> None:
        write_valid_docs(tmp_path)

        query = "1234567890"
        default_result = runner.invoke(app, ["search", query, "--path", str(tmp_path)])
        all_result = runner.invoke(app, ["search", query, "--path", str(tmp_path), "--all"])
        min_zero_result = runner.invoke(
            app,
            ["search", query, "--path", str(tmp_path), "--min-score", "0"],
        )

        assert json.loads(default_result.output)["results"] == []
        assert len(json.loads(all_result.output)["results"]) == 3
        assert len(json.loads(min_zero_result.output)["results"]) == 3

    def test_refs_text_graph_export_and_serve(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_valid_docs(tmp_path)

        refs_result = runner.invoke(
            app,
            ["refs", "@User", "--path", str(tmp_path), "--output", "text"],
        )
        graph_result = runner.invoke(app, ["graph", "!Login", "--path", str(tmp_path)])
        export_result = runner.invoke(app, ["export", "--path", str(tmp_path), "--type", "!", "--no-raw"])

        async def fake_run_server(path: Path, host: str, port: int, reload: bool) -> None:
            assert path == tmp_path
            assert host == "127.0.0.1"
            assert port == 9999
            assert reload is False

        monkeypatch.setattr("dog_core.server.run_server", fake_run_server)
        serve_result = runner.invoke(app, ["serve", str(tmp_path), "--port", "9999", "--no-reload"])

        assert refs_result.exit_code == 0
        assert "References to Actor: User" in refs_result.output
        assert graph_result.exit_code == 0
        assert '"!Login" -> "@User"' in graph_result.output
        assert export_result.exit_code == 0
        export_data = json.loads(export_result.output)
        assert export_data["count"] == 1
        assert "raw" not in export_data["documents"][0]
        assert serve_result.exit_code == 0
        assert "Starting DOG documentation server" in serve_result.output

    def test_operational_error_branches(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        invalid = tmp_path / "invalid"
        invalid.mkdir()
        (invalid / "broken.dog.md").write_text("# Invalid\n")

        assert runner.invoke(app, ["format", str(empty)]).exit_code == 1
        assert runner.invoke(app, ["graph", "--path", str(empty)]).exit_code == 1
        assert runner.invoke(app, ["export", "--path", str(empty)]).exit_code == 1
        assert runner.invoke(app, ["export", "--path", str(invalid)]).exit_code == 1
        assert runner.invoke(app, ["graph", "--path", str(invalid)]).exit_code == 1

        bad_type = runner.invoke(app, ["export", "--path", str(empty), "--type", "bad"])
        assert bad_type.exit_code == 1
        assert "Invalid filter" in bad_type.output

        missing_dir = tmp_path / "missing"
        index_result = runner.invoke(app, ["index", str(missing_dir), "--name", "Nope"])
        assert index_result.exit_code == 1
        assert "Directory does not exist" in index_result.output

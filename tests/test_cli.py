from pathlib import Path

from typer.testing import CliRunner

from dog_cli.main import app


runner = CliRunner()


class TestLintCommand:
    def test_lint_valid_files(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["lint", str(tmp_dog_dir)])
        assert result.exit_code == 0
        assert "Linting 2 file(s)" in result.output

    def test_lint_no_files(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(tmp_path)])
        assert result.exit_code == 1
        assert "No .dog.md files found" in result.output

    def test_lint_invalid_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.dog.md"
        file_path.write_text("# Invalid Header\n")

        result = runner.invoke(app, ["lint", str(file_path)])
        assert result.exit_code == 1
        assert "Parse error" in result.output

    def test_lint_with_warnings(self, tmp_path: Path) -> None:
        file_path = tmp_path / "actor.dog.md"
        file_path.write_text("# Actor: User\n\n## InvalidSection\n\nContent\n")

        result = runner.invoke(app, ["lint", str(file_path)])
        assert "warning" in result.output.lower()
        assert "InvalidSection" in result.output

    def test_lint_with_unknown_reference(self, tmp_path: Path) -> None:
        file_path = tmp_path / "behavior.dog.md"
        file_path.write_text("# Behavior: Test\n\n## Description\n\nReferences `@UnknownActor`\n")

        result = runner.invoke(app, ["lint", str(file_path)])
        assert "Unknown" in result.output
        assert "UnknownActor" in result.output


class TestFormatCommand:
    def test_format_files(self, tmp_path: Path) -> None:
        file_path = tmp_path / "actor.dog.md"
        file_path.write_text("# Actor: User   \n\nText")

        result = runner.invoke(app, ["format", str(tmp_path)])
        assert result.exit_code == 0
        assert "Formatted" in result.output

        # Verify file was modified
        content = file_path.read_text()
        assert "User   " not in content

    def test_format_already_formatted(self, tmp_path: Path) -> None:
        file_path = tmp_path / "actor.dog.md"
        file_path.write_text("# Actor: User\n\n## Description\n\nText\n")

        result = runner.invoke(app, ["format", str(tmp_path)])
        assert result.exit_code == 0
        assert "already formatted" in result.output

    def test_format_check_mode(self, tmp_path: Path) -> None:
        file_path = tmp_path / "actor.dog.md"
        original = "# Actor: User   \n\nText"
        file_path.write_text(original)

        result = runner.invoke(app, ["format", "--check", str(tmp_path)])
        assert result.exit_code == 1
        assert "Would reformat" in result.output

        # Verify file was NOT modified
        assert file_path.read_text() == original

    def test_format_check_already_formatted(self, tmp_path: Path) -> None:
        file_path = tmp_path / "actor.dog.md"
        file_path.write_text("# Actor: User\n\n## Description\n\nText\n")

        result = runner.invoke(app, ["format", "--check", str(tmp_path)])
        assert result.exit_code == 0
        assert "already formatted" in result.output


class TestIndexCommand:
    def test_index_create(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["index", str(tmp_dog_dir), "--name", "TestProject"])
        assert result.exit_code == 0
        assert "Generated index" in result.output

        index_path = tmp_dog_dir / "index.dog.md"
        assert index_path.exists()

        content = index_path.read_text()
        assert "# Project: TestProject" in content

    def test_index_specific_file(self, tmp_dog_dir: Path) -> None:
        # Create the index file first (to simulate updating an existing one)
        index_path = tmp_dog_dir / "index.dog.md"
        index_path.write_text("# Project: OldProject\n")

        result = runner.invoke(app, ["index", str(index_path), "--name", "SpecificProject"])
        assert result.exit_code == 0

        content = index_path.read_text()
        assert "# Project: SpecificProject" in content

    def test_index_wrong_filename(self, tmp_path: Path) -> None:
        wrong_path = tmp_path / "project.dog.md"
        wrong_path.write_text("")

        result = runner.invoke(app, ["index", str(wrong_path), "--name", "Test"])
        assert result.exit_code == 1
        assert "index.dog.md" in result.output

    def test_index_lists_primitives(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["index", str(tmp_dog_dir), "--name", "Test"])
        assert result.exit_code == 0

        content = (tmp_dog_dir / "index.dog.md").read_text()
        assert "## Actors" in content
        assert "[User](user.dog.md)" in content
        assert "## Behaviors" in content
        assert "[Login](login.dog.md)" in content


class TestSearchCommand:
    def test_search_text_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["search", "User", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        assert "User" in result.output
        assert "Actor" in result.output

    def test_search_json_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["search", "User", "--path", str(tmp_dog_dir), "--output", "json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) > 0
        # User should be in results
        names = [r["name"] for r in data["results"]]
        assert "User" in names

    def test_search_with_type_filter(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["search", "User", "--path", str(tmp_dog_dir), "--type", "Actor"],
        )
        assert result.exit_code == 0
        assert "User" in result.output

    def test_search_type_filter_excludes(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["search", "User", "--path", str(tmp_dog_dir), "--type", "Component"],
        )
        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_search_low_relevance(self, tmp_dog_dir: Path) -> None:
        # With top-k, we get results sorted by score even for weak queries
        result = runner.invoke(app, ["search", "zzzqqq999notaword", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        # Results are returned (low scoring, but still returned)
        assert result.output.strip() != ""

    def test_search_invalid_type(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["search", "User", "--path", str(tmp_dog_dir), "--type", "InvalidType"],
        )
        assert result.exit_code == 1
        assert "Invalid type" in result.output

    def test_search_no_files(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["search", "test", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "No .dog.md files found" in result.output

    def test_search_limit(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["search", "a", "--path", str(tmp_dog_dir), "--limit", "1", "--output", "json"],
        )
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert len(data["results"]) <= 1


class TestGetCommand:
    def test_get_text_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["get", "User", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        assert "# Actor: User" in result.output
        assert "Description" in result.output

    def test_get_json_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["get", "User", "--path", str(tmp_dog_dir), "--output", "json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert data["name"] == "User"
        assert data["type"] == "Actor"
        assert "sections" in data
        assert "content" in data

    def test_get_with_type_filter(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["get", "User", "--path", str(tmp_dog_dir), "--type", "Actor"],
        )
        assert result.exit_code == 0
        assert "User" in result.output

    def test_get_wrong_type_filter(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["get", "User", "--path", str(tmp_dog_dir), "--type", "Component"],
        )
        assert result.exit_code == 1
        assert "Not found" in result.output

    def test_get_not_found(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["get", "NonExistent", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 1
        assert "Not found" in result.output

    def test_get_case_insensitive(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["get", "user", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        assert "User" in result.output

    def test_get_invalid_type(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["get", "User", "--path", str(tmp_dog_dir), "--type", "InvalidType"],
        )
        assert result.exit_code == 1
        assert "Invalid type" in result.output

    def test_get_no_files(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["get", "test", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "No .dog.md files found" in result.output

    def test_get_with_references(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["get", "Login", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        # Login behavior references @User
        assert "References" in result.output or "User" in result.output


class TestListCommand:
    def test_list_text_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["list", "--path", str(tmp_dog_dir)])
        assert result.exit_code == 0
        assert "Actors" in result.output
        assert "User" in result.output
        assert "Behaviors" in result.output
        assert "Login" in result.output

    def test_list_json_output(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(app, ["list", "--path", str(tmp_dog_dir), "--output", "json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert "documents" in data
        assert len(data["documents"]) == 2  # User and Login

    def test_list_with_type_filter(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["list", "--path", str(tmp_dog_dir), "--type", "Actor"],
        )
        assert result.exit_code == 0
        assert "User" in result.output
        assert "Login" not in result.output

    def test_list_invalid_type(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["list", "--path", str(tmp_dog_dir), "--type", "InvalidType"],
        )
        assert result.exit_code == 1
        assert "Invalid type" in result.output

    def test_list_no_files(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # Empty list returns empty documents array in JSON
        result_json = runner.invoke(app, ["list", "--path", str(tmp_path), "--output", "json"])
        import json

        data = json.loads(result_json.output)
        assert data["documents"] == []

    def test_list_empty_with_filter(self, tmp_dog_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["list", "--path", str(tmp_dog_dir), "--type", "Project"],
        )
        assert result.exit_code == 0
        assert "No documents found" in result.output

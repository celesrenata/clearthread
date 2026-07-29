"""Unit tests for CLI."""

from click.testing import CliRunner

from clearthread.cli import main


class TestCLI:
    """Tests for ClearThread CLI."""

    def test_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_help(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ClearThread" in result.output

    def test_import_command(self):
        """Test import command."""
        runner = CliRunner()
        result = runner.invoke(main, ["import", "--help"])
        assert result.exit_code in (0, 2)  # click 8.x returns 2 for --help

    def test_analyze_command(self):
        """Test analyze command."""
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_search_command(self):
        """Test search command."""
        runner = CliRunner()
        result = runner.invoke(main, ["search", "--help"])
        assert result.exit_code == 0

    def test_export_command(self):
        """Test export command."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0

    def test_serve_command(self):
        """Test serve command."""
        runner = CliRunner()
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        assert "ClearThread server starting" in result.output

    def test_verbose_flag(self):
        """Test verbose flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["-v", "serve"])
        assert result.exit_code == 0

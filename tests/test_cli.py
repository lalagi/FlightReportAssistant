import pytest
from click.testing import CliRunner
from assistant.cli import cli


@pytest.fixture
def runner():
    """Fixture to provide a CliRunner instance."""
    return CliRunner()


def test_init_command(runner, mocker):
    """Test the 'init' command."""
    mock_db = mocker.patch(
        "assistant.database_handler.get_database_handler"
    ).return_value
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    mock_db.init_db.assert_called_once()


def test_stats_command(runner, mocker):
    """Test the 'stats' command."""
    mock_db = mocker.patch(
        "assistant.database_handler.get_database_handler"
    ).return_value
    mock_db.get_stats_by_category.return_value = [("Avionics", 5), ("Mechanical", 2)]

    result = runner.invoke(cli, ["stats", "category"])

    assert result.exit_code == 0
    assert "Avionics" in result.output
    assert "Mechanical" in result.output
    assert "5" in result.output


def test_list_command(runner, mocker):
    """Test the 'list' command with a specific severity."""
    mock_db = mocker.patch(
        "assistant.database_handler.get_database_handler"
    ).return_value
    mock_db.list_reports_by_severity.return_value = [
        {
            "id": "1",
            "timestamp": "T1",
            "category": "C1",
            "summary": "S1",
            "recommendation": "R1",
        }
    ]

    result = runner.invoke(cli, ["list", "--severity", "high"])

    assert result.exit_code == 0
    assert "Reports with Severity: HIGH" in result.output
    assert "Summary:   S1" in result.output
    mock_db.list_reports_by_severity.assert_called_with("high")


def test_show_command(runner, mocker):
    """Test the 'show' command for a specific report ID."""
    mock_db = mocker.patch(
        "assistant.database_handler.get_database_handler"
    ).return_value
    mock_db.get_report_by_id.return_value = {
        "id": "xyz",
        "summary": "Detailed summary here",
    }

    result = runner.invoke(cli, ["show", "--id", "xyz"])

    assert result.exit_code == 0
    assert "Full Report Details" in result.output
    assert "Summary        : Detailed summary here" in result.output
    mock_db.get_report_by_id.assert_called_with("xyz")


def test_ingest_command(runner, mocker, tmp_path):
    """Test the 'ingest' command with a mock file."""
    # Mock the processor function directly to avoid AI/DB complexity in this CLI test
    mock_process = mocker.patch("assistant.event_processor.process_and_store_files")

    # Create a dummy file to pass the `exists=True` check
    dummy_file = tmp_path / "dummy_data.json"
    dummy_file.write_text("[]")

    result = runner.invoke(cli, ["ingest", str(dummy_file)])

    assert result.exit_code == 0
    mock_process.assert_called_once()

import pytest
from assistant.database_handler import SQLiteHandler


@pytest.fixture
def db_handler():
    """Fixture to create an in-memory SQLite database for testing."""
    # The handler now initializes the DB upon creation
    handler = SQLiteHandler(db_file=":memory:")
    return handler


def test_init_db(db_handler):
    """Test database initialization."""
    # The table should be created by the fixture already.
    # We use the new context manager to check.
    with db_handler._managed_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='flight_reports'"
        )
        assert cursor.fetchone() is not None


def test_add_and_get_report(db_handler):
    """Test adding a report and retrieving it."""
    report_data = {
        "id": "test_id_1",
        "timestamp": "2025-07-22T10:00:00Z",
        "source": "test_source.json",
        "raw_event_text": "Test event text",
        "summary": "Test summary",
        "category": "Test Category",
        "severity": "low",
        "recommendation": "Test recommendation",
        "model_meta": "{'model': 'test_model'}",
    }
    db_handler.add_event(report_data)

    retrieved_report = db_handler.get_report_by_id("test_id_1")
    assert retrieved_report is not None
    assert retrieved_report["summary"] == "Test summary"


def test_report_exists(db_handler):
    """Test the report_exists method."""
    timestamp = "2025-07-22T11:00:00Z"
    raw_text = "Another test event"
    report_data = {
        "id": "test_id_2",
        "timestamp": timestamp,
        "source": "test.json",
        "raw_event_text": raw_text,
        "summary": "S",
        "category": "C",
        "severity": "S",
        "recommendation": "R",
        "model_meta": "{}",
    }

    assert not db_handler.report_exists(timestamp, raw_text)
    db_handler.add_event(report_data)
    assert db_handler.report_exists(timestamp, raw_text)


def test_get_stats_by_category(db_handler):
    """Test statistics generation by category."""
    reports = [
        {
            "id": "1",
            "timestamp": "1",
            "source": "s",
            "raw_event_text": "t1",
            "summary": "s",
            "category": "Avionics",
            "severity": "low",
            "recommendation": "r",
            "model_meta": "{}",
        },
        {
            "id": "2",
            "timestamp": "2",
            "source": "s",
            "raw_event_text": "t2",
            "summary": "s",
            "category": "Avionics",
            "severity": "low",
            "recommendation": "r",
            "model_meta": "{}",
        },
        {
            "id": "3",
            "timestamp": "3",
            "source": "s",
            "raw_event_text": "t3",
            "summary": "s",
            "category": "Mechanical",
            "severity": "high",
            "recommendation": "r",
            "model_meta": "{}",
        },
    ]
    for r in reports:
        db_handler.add_event(r)

    stats = db_handler.get_stats_by_category()
    stats_dict = dict(stats)
    assert stats_dict["Avionics"] == 2
    assert stats_dict["Mechanical"] == 1


def test_list_reports_by_severity(db_handler):
    """Test listing reports by their severity level."""
    reports = [
        {
            "id": "1",
            "timestamp": "1",
            "raw_event_text": "t1",
            "category": "C1",
            "severity": "low",
            "summary": "S1",
            "recommendation": "R1",
            "source": "s",
            "model_meta": "{}",
        },
        {
            "id": "2",
            "timestamp": "2",
            "raw_event_text": "t2",
            "category": "C2",
            "severity": "high",
            "summary": "S2",
            "recommendation": "R2",
            "source": "s",
            "model_meta": "{}",
        },
        {
            "id": "3",
            "timestamp": "3",
            "raw_event_text": "t3",
            "category": "C3",
            "severity": "low",
            "summary": "S3",
            "recommendation": "R3",
            "source": "s",
            "model_meta": "{}",
        },
    ]
    for r in reports:
        db_handler.add_event(r)

    low_severity_reports = db_handler.list_reports_by_severity("low")
    high_severity_reports = db_handler.list_reports_by_severity("high")

    assert len(low_severity_reports) == 2
    assert len(high_severity_reports) == 1
    assert low_severity_reports[0]["summary"] == "S1"
    assert high_severity_reports[0]["summary"] == "S2"

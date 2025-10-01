import pytest
import json
from assistant import event_processor

@pytest.fixture
def mock_ai_service(mocker):
    """Fixture to mock the AI service."""
    mock = mocker.patch('assistant.ai_service.get_ai_service').return_value
    mock.process_text.return_value = {
        "summary": "Mock Summary",
        "category": "Mock Category",
        "severity": "medium",
        "recommendation": "Mock Recommendation",
        "model_meta": "{'mock': True}"
    }
    return mock

@pytest.fixture
def mock_db_handler(mocker):
    """Fixture to mock the database handler."""
    mock = mocker.patch('assistant.database_handler.get_database_handler').return_value
    mock.report_exists.return_value = False
    return mock

def create_mock_file(tmp_path, content, filename):
    """Helper function to create a temporary file with content."""
    file_path = tmp_path / filename
    with open(file_path, 'w') as f:
        json.dump(content, f)
    return str(file_path)

def test_parse_ops_file(tmp_path):
    """Test parsing of an operational events file."""
    ops_data = [{"flight_date": "2025-07-20 10:10:00", "observation": "Engine running rough"}]
    file_path = create_mock_file(tmp_path, ops_data, "event_ops.json")
    
    records = event_processor.parse_ops_file(file_path)
    assert len(records) == 1
    assert records[0]["timestamp"] == "2025-07-20 10:10:00"
    assert records[0]["raw_event_text"] == "Engine running rough"

def test_parse_tech_file(tmp_path):
    """Test parsing of a technical events file."""
    tech_data = [{"log_date": "2025-07-21T09:00:00Z", "entry": "High level of copper"}]
    file_path = create_mock_file(tmp_path, tech_data, "event_tech.json")

    records = event_processor.parse_tech_file(file_path)
    assert len(records) == 1
    assert records[0]["timestamp"] == "2025-07-21T09:00:00Z"
    assert records[0]["raw_event_text"] == "High level of copper"

def test_process_and_store_files(tmp_path, mock_db_handler, mock_ai_service):
    """Test the end-to-end file processing and storage workflow."""
    ops_data = [{"flight_date": "2025-07-20 10:10:00", "observation": "Test ops event"}]
    ops_file = create_mock_file(tmp_path, ops_data, "test_ops.json")
    
    event_processor.process_and_store_files([ops_file], mock_db_handler, mock_ai_service)
    
    mock_db_handler.add_event.assert_called_once()
    call_args = mock_db_handler.add_event.call_args[0][0]
    
    assert call_args["raw_event_text"] == "Test ops event"
    assert call_args["summary"] == "Mock Summary"
    assert call_args["category"] == "Mock Category"
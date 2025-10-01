import pytest
from assistant.ai_service import MockAIService, HuggingFaceAIService

@pytest.fixture
def mock_service():
    """Fixture to provide a MockAIService instance."""
    return MockAIService()

def test_mock_ai_mechanical(mock_service):
    """Test that 'engine' keyword is classified as Mechanical."""
    result = mock_service.process_text("The engine was running rough.")
    assert result["category"] == "Mechanical"
    assert result["severity"] == "high"

def test_mock_ai_avionics(mock_service):
    """Test that 'autopilot' is classified as Avionics."""
    result = mock_service.process_text("Autopilot disengaged unexpectedly.")
    assert result["category"] == "Avionics"
    assert result["severity"] == "medium"

def test_mock_ai_human_factors(mock_service):
    """Test that 'pilot' is classified as Human Factors."""
    result = mock_service.process_text("The pilot missed a checklist item.")
    assert result["category"] == "Human Factors"
    assert result["severity"] == "low"
    
def test_mock_ai_critical_failure(mock_service):
    """Test that 'bird strike' is classified as Critical Failure."""
    result = mock_service.process_text("A bird strike occurred on the right wing.")
    assert result["category"] == "Critical Failure"
    assert result["severity"] == "critical"


@pytest.fixture
def mock_pipeline(mocker):
    """Fixture to mock the transformers.pipeline function."""
    
    class MockModel:
        def __init__(self, name):
            self.name_or_path = name
    
    class MockTokenizer:
        eos_token_id = 50256

    class MockPipeline:
        def __init__(self, model_name, task_type):
            self.model = MockModel(model_name)
            self.task_type = task_type
            self.tokenizer = MockTokenizer()
            self.call_history = []

        def __call__(self, *args, **kwargs):
            self.call_history.append({"args": args, "kwargs": kwargs})
            if "zero-shot-classification" in self.task_type:
                return {"labels": [kwargs.get("candidate_labels", ["default"])[0]]}
            elif "text-generation" in self.task_type:
                prompt = args[0]
                return [{"generated_text": f"{prompt}Mocked Response <|endofassistant|>"}]
            return None

    # This dictionary will hold our mock pipeline instances
    mock_pipelines = {}

    def pipeline_factory(*args, **kwargs):
        # Determine the task: it can be a positional or keyword argument
        task = args[0] if args else kwargs.get("task")
        model = kwargs.get("model")
        
        # Create a unique key for this model/task combo to reuse mocks
        key = (task, model)
        if key not in mock_pipelines:
            mock_pipelines[key] = MockPipeline(model_name=model, task_type=task)
        return mock_pipelines[key]

    mocker.patch("assistant.ai_service.pipeline", side_effect=pipeline_factory)
    return mock_pipelines


@pytest.fixture
def hf_service(mock_pipeline):
    """Fixture to create an instance of HuggingFaceAIService with mocked pipelines."""
    return HuggingFaceAIService(
        summary_model="summary/model",
        category_model="category/model",
        severity_model="severity/model",
        recommendation_model="recommendation/model",
        event_categories=["Avionics", "Mechanical"],
        severity_levels=["low", "medium", "high"],
        summary_prompt_template="Summarize: {raw_event_text}",
        recommendation_prompt_template="Recommend for {raw_event_text}, cat: {category}, sev: {severity}"
    )

class TestHuggingFaceAIService:

    def test_service_initialization(self, hf_service):
        """Test that the service and its pipelines are initialized correctly."""
        assert hf_service is not None
        assert hf_service.summary_generator.model.name_or_path == "summary/model"
        assert hf_service.category_classifier.model.name_or_path == "category/model"
        assert hf_service.severity_classifier.model.name_or_path == "severity/model"
        assert hf_service.recommendation_generator.model.name_or_path == "recommendation/model"

    def test_clean_generated_text(self, hf_service):
        """Test the internal text cleaning logic."""
        prompt = "This is the prompt."
        full_output = f"{prompt} This is the actual response. <|endofassistant|> Some extra stuff."
        cleaned = hf_service._clean_generated_text(full_output, prompt)
        assert cleaned == "This is the actual response."

    def test_get_category(self, hf_service):
        """Test the category classification call."""
        category = hf_service._get_category("some text")
        # The mock returns the first candidate label
        assert category == "Avionics"
        # Verify that the classifier was called with the correct arguments
        classifier_calls = hf_service.category_classifier.call_history
        assert len(classifier_calls) == 1
        assert classifier_calls[0]['args'][0] == "some text"
        assert classifier_calls[0]['kwargs']['candidate_labels'] == ["Avionics", "Mechanical"]

    def test_generate_summary(self, hf_service):
        """Test the summary generation call and prompt formatting."""
        summary = hf_service._generate_summary("test event")
        assert summary == "Mocked Response"
        # Verify the prompt was formatted correctly
        generator_calls = hf_service.summary_generator.call_history
        assert len(generator_calls) == 1
        assert generator_calls[0]['args'][0] == "Summarize: test event"

    def test_generate_recommendation(self, hf_service):
        """Test the recommendation generation call and prompt formatting."""
        recommendation = hf_service._generate_recommendation("another event", "Avionics", "high")
        assert recommendation == "Mocked Response"
        # Verify the prompt was formatted correctly
        generator_calls = hf_service.recommendation_generator.call_history
        assert len(generator_calls) == 1
        assert generator_calls[0]['args'][0] == "Recommend for another event, cat: Avionics, sev: high"

    def test_full_process_text(self, hf_service):
        """Test the end-to-end process_text method."""
        result = hf_service.process_text("A full test event.")
        
        assert result["summary"] == "Mocked Response"
        assert result["category"] == "Avionics"  # Mock returns the first candidate
        assert result["severity"] == "low"      # Mock returns the first candidate
        assert result["recommendation"] == "Mocked Response"
        assert "processing_time_ms" in result["model_meta"]
        assert "category/model" in result["model_meta"]
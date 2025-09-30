import time
import logging
import yaml
from typing import Dict, Any, List
from abc import ABC, abstractmethod

from transformers import pipeline, logging as transformers_logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
transformers_logging.set_verbosity_error()

class AIService(ABC):
    """
    Abstract Base Class (Interface) for AI services.
    Every concrete AI provider must implement this class.
    """
    @abstractmethod
    def process_text(self, raw_event_text: str) -> Dict[str, Any]:
        """
        Processes a raw text and returns a structured dictionary
        with summary, category, severity, and recommendation.
        """
        pass

class HuggingFaceAIService(AIService):
    """
    HuggingFace AI service implementation using transformers pipelines.
    """
    def __init__(self, summary_model: str, category_model: str, severity_model: str, recommendation_model: str, 
                 event_categories: List[str], severity_levels: List[str],
                 summary_prompt_template: str, recommendation_prompt_template: str):
        logging.info("Initializing HuggingFaceAIService with dedicated models for each task...")
        
        logging.info(f"Loading summary model: {summary_model}")
        self.summary_generator = pipeline("text-generation", model=summary_model, torch_dtype="auto", device_map="auto", trust_remote_code=True)
        
        logging.info(f"Loading category classifier: {category_model}")
        self.category_classifier = pipeline("zero-shot-classification", model=category_model)
        
        logging.info(f"Loading severity classifier: {severity_model}")
        self.severity_classifier = pipeline("zero-shot-classification", model=severity_model)
        
        logging.info(f"Loading recommendation model: {recommendation_model}")
        self.recommendation_generator = pipeline("text-generation", model=recommendation_model, torch_dtype="auto", device_map="auto", trust_remote_code=True)
        
        self.event_categories = event_categories
        self.severity_levels = severity_levels
        self.summary_prompt_template = summary_prompt_template
        self.recommendation_prompt_template = recommendation_prompt_template
            
        logging.info("HuggingFaceAIService initialized successfully.")

    def _clean_generated_text(self, full_output: str, prompt: str) -> str:
        generated_text = full_output[len(prompt):].strip()
        stop_token = "<|endofassistant|>"
        if stop_token in generated_text:
            generated_text = generated_text.split(stop_token)[0].strip()
        return generated_text.strip('"').strip()

    def _get_category(self, raw_event_text: str) -> str:
        return self.category_classifier(raw_event_text, candidate_labels=self.event_categories)['labels'][0]

    def _get_severity(self, raw_event_text: str) -> str:
        return self.severity_classifier(raw_event_text, candidate_labels=self.severity_levels)['labels'][0]

    def _generate_summary(self, raw_event_text: str) -> str:
        prompt = self.summary_prompt_template.format(raw_event_text=raw_event_text)
        result = self.summary_generator(prompt, max_new_tokens=30, pad_token_id=self.summary_generator.tokenizer.eos_token_id)
        summary = self._clean_generated_text(result[0]['generated_text'], prompt)
        if not summary:
            logging.warning(f"Could not generate summary for text: '{raw_event_text[:100]}...'. Using fallback.")
            return "No summary available."
        return summary

    def _generate_recommendation(self, raw_event_text: str, category: str, severity: str) -> str:
        prompt = self.recommendation_prompt_template.format(raw_event_text=raw_event_text, category=category, severity=severity)
        result = self.recommendation_generator(prompt, max_new_tokens=40, pad_token_id=self.recommendation_generator.tokenizer.eos_token_id)
        recommendation = self._clean_generated_text(result[0]['generated_text'], prompt)
        if not recommendation:
            logging.warning(f"Could not generate recommendation for text: '{raw_event_text[:100]}...'. Using fallback.")
            return "No recommendation available."
        return recommendation

    def process_text(self, raw_event_text: str) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            category = self._get_category(raw_event_text)
            severity = self._get_severity(raw_event_text)
            summary = self._generate_summary(raw_event_text)
            recommendation = self._generate_recommendation(raw_event_text, category, severity)
        except Exception as e:
            logging.error(f"Error processing text with AI model: {e}")
            return {
                "summary": "AI processing failed.", "category": "Unknown", "severity": "Unknown",
                "recommendation": "Manual review required.", "model_meta": str({"error": str(e)})
            }

        end_time = time.time()
        
        model_meta = {
            "summary_model": self.summary_generator.model.name_or_path,
            "category_model": self.category_classifier.model.name_or_path,
            "severity_model": self.severity_classifier.model.name_or_path,
            "recommendation_model": self.recommendation_generator.model.name_or_path,
            "processing_time_ms": round((end_time - start_time) * 1000),
            "timestamp": end_time
        }

        return {
            "summary": summary, "category": category, "severity": severity,
            "recommendation": recommendation, "model_meta": str(model_meta)
        }

class MockAIService(AIService):
    """
    A mock AI service that uses rule-based logic for demonstration.
    This class can be replaced by a real AI service (e.g., OpenAIService)
    without changing the rest of the application.
    """
    def process_text(self, raw_event_text: str) -> Dict[str, Any]:
        """Mocks an AI model to process raw flight event text."""
        
        text_lower = raw_event_text.lower()
        
        # Default values
        category = "General"
        severity = "low"
        recommendation = "Monitor closely."
        
        # Rule-based classification
        if any(keyword in text_lower for keyword in ["bird strike", "damage", "fire"]):
            category = "Critical Failure"
            severity = "critical"
            recommendation = "Ground the aircraft. Full engineering review required."
        elif any(keyword in text_lower for keyword in ["engine", "hydraulic", "apu", "pressure", "vibration"]):
            category = "Mechanical"
            severity = "high"
            recommendation = "Immediate maintenance check required."
        elif any(keyword in text_lower for keyword in ["landing gear", "tire", "brakes", "slats"]):
            category = "Flight Controls"
            severity = "high"
            recommendation = "Inspect relevant flight control systems before next flight."
        elif any(keyword in text_lower for keyword in ["nav", "display", "autopilot", "fms", "sensor", "avionics", "radio"]):
            category = "Avionics"
            severity = "medium"
            recommendation = "Schedule maintenance for the avionics system."
        elif any(keyword in text_lower for keyword in ["weather", "turbulence", "wind shear", "gusts", "storm"]):
            category = "Weather"
            severity = "medium"
            recommendation = "Review flight plan and weather briefings."
        elif any(keyword in text_lower for keyword in ["pilot", "co-pilot", "crew", "atc", "checklist", "disagreement"]):
            category = "Human Factors"
            severity = "low"
            recommendation = "Add to next training session for crew resource management."

        # Mock summary
        summary = f"Event involving: {raw_event_text[:50]}..."

        # Mock model metadata
        model_meta = {
            "model_name": "MockAI-Rule-Based-v2.1",
            "processing_time_ms": 150,
            "timestamp": time.time()
        }
        
        return {
            "summary": summary,
            "category": category,
            "severity": severity,
            "recommendation": recommendation,
            "model_meta": str(model_meta)
        }
    
def get_ai_service() -> AIService:
    """
    Factory function that retrieves the current AI service based on config.yaml.
    """
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("Configuration file (config.yaml) not found. Aborting.")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}. Aborting.")
        raise

    service_config = config.get('ai_service', {})
    service_type = service_config.get('active_service', 'mock')
    logging.info(f"Selected AI service type from config: {service_type}")

    if service_type == "huggingface":
        hf_config = service_config['huggingface']
        models = hf_config['models']
        prompts = hf_config.get('prompts', {})
        
        return HuggingFaceAIService(
            summary_model=models['summary_model'],
            category_model=models['category_model'],
            severity_model=models['severity_model'],
            recommendation_model=models['recommendation_model'],
            event_categories=service_config['labels']['categories'],
            severity_levels=service_config['labels']['severities'],
            summary_prompt_template=prompts.get('summarization', 'Summarize: {raw_event_text}'),
            recommendation_prompt_template=prompts.get('recommendation', 'Recommend for: {raw_event_text}')
        )
    elif service_type == "mock":
        return MockAIService()
    else:
        raise ValueError(f"Unknown AI service type in config: '{service_type}'")
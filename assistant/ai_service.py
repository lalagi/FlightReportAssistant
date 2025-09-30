import time
from typing import Dict, Any
from abc import ABC, abstractmethod

from transformers import pipeline, logging

logging.set_verbosity_error()

class AIService(ABC):
    """Abstract Base Class for AI services."""
    
    @abstractmethod
    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Processes raw text and returns a dictionary with summary, category, severity, and recommendation.
        """
        pass

class HuggingFaceAIService(AIService):
    """
    An AI service implementation that uses a single advanced Hugging Face transformer (phi-2)
    to generate all required outputs based on specific prompts.
    """
    def __init__(self):
        print("Initializing HuggingFaceAIService...")
        print("Loading models, this may take a few minutes and require significant memory...")
        
        # Load the zero-shot classification model for category and severity detection
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        
        # Load the text generation model for summary and recommendation
        self.generator = pipeline(
            "text-generation", 
            model="microsoft/phi-2",
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True
        )
        
        self.event_categories = ["Flight Ops", "Avionics", "Weather", "Human Factors", "Mechanical"]
        self.severity_levels = ["low", "medium", "high", "critical"]
        
        print("HuggingFaceAIService initialized successfully.")

    def _clean_generated_text(self, full_output: str, prompt: str) -> str:
        """Helper function to clean the generated text from the model."""
        # 1. Cut off the prompt from the output
        generated_text = full_output[len(prompt):].strip()
        
        # 2. Remove unnecessary stop tokens
        stop_token = "<|endofassistant|>"
        if stop_token in generated_text:
            generated_text = generated_text.split(stop_token)[0].strip()
            
        # 3. Fine-tuning: remove unnecessary quotes and leading characters
        return generated_text.strip('"').strip()

    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """Processes raw text using dedicated prompts for each generation task."""
        start_time = time.time()
        
        # 1. Determine category and severity (this remains the old way)
        category = self.classifier(raw_text, candidate_labels=self.event_categories)['labels'][0]
        severity = self.classifier(raw_text, candidate_labels=self.severity_levels)['labels'][0]
        
        # 2. Generate summary with the phi-2 model
        summary_prompt = f'<|user|>\nSummarize the following flight event in one concise sentence.\nEvent: "{raw_text}"\n<|endofuser|>\n<|assistant|>\nSummary:'
        summary_result = self.generator(summary_prompt, max_new_tokens=30, pad_token_id=self.generator.tokenizer.eos_token_id)
        summary = self._clean_generated_text(summary_result[0]['generated_text'], summary_prompt)
        if not summary: # Fallback
            summary = "No summary available."

        # 3. Generate recommendation with the phi-2 model
        rec_prompt = f'<|user|>\nAnalyze the flight report and provide one concise recommendation.\nEvent: "{raw_text}"\nCategory: {category}\nSeverity: {severity}\n<|endofuser|>\n<|assistant|>\nRecommendation:'
        rec_result = self.generator(rec_prompt, max_new_tokens=40, pad_token_id=self.generator.tokenizer.eos_token_id)
        recommendation = self._clean_generated_text(rec_result[0]['generated_text'], rec_prompt)
        if not recommendation: # Fallback
            recommendation = "Review system logs and monitor."

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000

        model_meta = {
            "classifier_model": self.classifier.model.name_or_path,
            "generator_model": self.generator.model.name_or_path,
            "processing_time_ms": round(processing_time),
            "timestamp": end_time
        }

        return {
            "summary": summary,
            "category": category,
            "severity": severity,
            "recommendation": recommendation,
            "model_meta": str(model_meta)
        }

class MockAIService(AIService):
    """
    A mock AI service that uses rule-based logic for demonstration.
    This class can be replaced by a real AI service (e.g., OpenAIService)
    without changing the rest of the application.
    """
    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """Mocks an AI model to process raw flight event text."""
        
        text_lower = raw_text.lower()
        
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
        summary = f"Event involving: {raw_text[:50]}..."

        # Mock model metadata
        model_meta = {
            "model_name": "MockAI-Rule-Based-v2.1", # Version up
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
    """Factory function to get the current AI service."""
    return HuggingFaceAIService()
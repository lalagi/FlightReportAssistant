import time
from typing import Dict, Any
from abc import ABC, abstractmethod

class AIService(ABC):
    """Abstract Base Class for AI services."""
    
    @abstractmethod
    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Processes raw text and returns a dictionary with summary, category, severity, and recommendation.
        """
        pass

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
    """
    Factory function to get the current AI service.
    This is where you could switch between MockAIService, OpenAIService, etc.
    based on a config file or environment variable.
    """
    return MockAIService()
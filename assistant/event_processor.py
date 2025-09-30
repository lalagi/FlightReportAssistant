import json
import os
import uuid
from typing import List, Dict, Any
from . import ai_service, database_handler

def parse_ops_file(file_path: str) -> List[Dict[str, str]]:
    """Parses the operational events JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            "timestamp": item.get("event_time", ""),
            "raw_text": item.get("event_description", "")
        })
    return records

def parse_tech_file(file_path: str) -> List[Dict[str, str]]:
    """Parses the technical events JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    records = []
    for item in data:
        records.append({
            "timestamp": item.get("timestamp_utc", ""),
            "raw_text": item.get("log_entry", "")
        })
    return records

def get_parser(file_path: str):
    """Selects the correct parser based on the filename."""
    if "ops" in os.path.basename(file_path):
        return parse_ops_file
    elif "tech" in os.path.basename(file_path):
        return parse_tech_file
    else:
        raise ValueError(f"No parser available for file: {file_path}")

def process_and_store_files(file_paths: List[str]):
    """
    Processes a list of input files, normalizes their content,
    enriches it with AI, and stores it in the database.
    """
    # Get the AI service instance
    ai_processor = ai_service.get_ai_service()
    
    print(f"Starting ingestion for {len(file_paths)} files using {type(ai_processor).__name__}...")
    total_new_records = 0
    
    for file_path in file_paths:
        try:
            parser = get_parser(file_path)
            raw_records = parser(file_path)
            
            for record in raw_records:
                if not record["raw_text"]:
                    continue

                # 1. Check for duplicates before processing with AI
                if database_handler.report_exists(record["timestamp"], record["raw_text"]):
                    print(f"Skipping existing record: {record['raw_text'][:50]}...")
                    continue

                # 2. Process with AI model
                ai_results = ai_processor.process_text(record["raw_text"])
                
                # 3. Normalize the record
                normalized_record = {
                    "id": str(uuid.uuid4()),
                    "timestamp": record["timestamp"],
                    "source": os.path.basename(file_path),
                    "raw_text": record["raw_text"],
                    "summary": ai_results["summary"],
                    "category": ai_results["category"],
                    "severity": ai_results["severity"],
                    "recommendation": ai_results["recommendation"],
                    "model_meta": ai_results["model_meta"]
                }
                
                # 4. Store the record
                database_handler.add_event(normalized_record)
                total_new_records += 1

            print(f"Successfully processed {len(raw_records)} records from {file_path}")

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            
    print(f"\nIngestion complete. Added {total_new_records} new records to the database.")
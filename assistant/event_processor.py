import json
import os
import uuid
import logging
from typing import List, Dict
from tqdm import tqdm
from . import ai_service, database_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_ops_file(file_path: str) -> List[Dict[str, str]]:
    """Parses the operational events JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    records = []
    for item in data:
        records.append({
            "timestamp": item.get("flight_date", ""),
            "raw_event_text": item.get("observation", "")
        })
    return records

def parse_tech_file(file_path: str) -> List[Dict[str, str]]:
    """Parses the technical events JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    records = []
    for item in data:
        records.append({
            "timestamp": item.get("log_date", ""),
            "raw_event_text": item.get("entry", "")
        })
    return records

def get_parser(file_path: str):
    """Selects the correct parser based on the filename."""
    if "ops" in os.path.basename(file_path):
        return parse_ops_file
    elif "tech" in os.path.basename(file_path):
        return parse_tech_file
    # elif "other_type" in os.path.basename(file_path):
    #     # Here we could process other types of files
    #     pass
    else:
        raise ValueError(f"No parser available for file: {file_path}")

def process_and_store_files(file_paths: List[str]):
    """
    Processes a list of input files, normalizes their content,
    enriches it with AI, and stores it in the database.
    """
    ai_processor = ai_service.get_ai_service()
    db_handler = database_handler.get_database_handler()
    
    logging.info(f"Starting ingestion for {len(file_paths)} file(s) using {type(ai_processor).__name__}...")
    total_new_records = 0
    
    for file_path in file_paths:
        try:
            parser = get_parser(file_path)
            raw_records = parser(file_path)
            
            for record in tqdm(raw_records, desc=f"Ingesting {os.path.basename(file_path)}", leave=False):
                if not record["raw_event_text"]:
                    continue

                if db_handler.report_exists(record["timestamp"], record["raw_event_text"]):
                    logging.warning(f"Skipping existing record: {record['raw_event_text'][:50]}...")
                    continue

                ai_results = ai_processor.process_text(record["raw_event_text"])
                
                normalized_record = {
                    "id": str(uuid.uuid4()),
                    "timestamp": record["timestamp"],
                    "source": os.path.basename(file_path),
                    "raw_event_text": record["raw_event_text"],
                    "summary": ai_results["summary"],
                    "category": ai_results["category"],
                    "severity": ai_results["severity"],
                    "recommendation": ai_results["recommendation"],
                    "model_meta": ai_results["model_meta"]
                }
                
                db_handler.add_event(normalized_record)
                total_new_records += 1

            logging.info(f"Successfully processed {len(raw_records)} records from {file_path}")

        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}", exc_info=True)
            
    logging.info(f"Ingestion complete. Added {total_new_records} new records to the database.")
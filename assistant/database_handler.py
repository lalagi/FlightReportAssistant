import sqlite3
import os
from typing import List, Dict, Any, Tuple, Optional

DB_FILE = "flight_reports.db"
DB_INITIALIZED = False

def ensure_db_initialized():
    """
    Ensures that the database and tables exist before using them.
    The actual check and creation only run once at program startup.
    """
    global DB_INITIALIZED
    # If the check has already run, exit immediately.
    if DB_INITIALIZED:
        return

    # Only check for file existence if this is the first call during the program.
    if not os.path.exists(DB_FILE):
        print("Database not found. Initializing...")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE flight_reports (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                summary TEXT,
                category TEXT,
                severity TEXT,
                recommendation TEXT,
                model_meta TEXT,
                UNIQUE(timestamp, raw_text)
            )
            """)
            conn.commit()
        print("Database initialized successfully.")
    
    # Set the flag to True so subsequent calls do nothing.
    DB_INITIALIZED = True


def get_connection():
    """Creates a connection to the database, ensuring it is initialized first."""
    ensure_db_initialized()
    return sqlite3.connect(DB_FILE)

def init_db():
    """
    Explicit command to initialize the database.
    Mainly useful for scripting and providing clarity to the user.
    """
    if os.path.exists(DB_FILE):
        print("Database already exists.")
    else:
        ensure_db_initialized()

def report_exists(timestamp: str, raw_text: str) -> bool:
    """Checks if a report already exists in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM flight_reports WHERE timestamp = ? AND raw_text = ?", (timestamp, raw_text))
        return cursor.fetchone() is not None

def add_event(report: Dict[str, Any]):
    """Adds a new processed report to the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO flight_reports (id, timestamp, source, raw_text, summary, category, severity, recommendation, model_meta)
            VALUES (:id, :timestamp, :source, :raw_text, :summary, :category, :severity, :recommendation, :model_meta)
            """, report)
            conn.commit()
    except sqlite3.IntegrityError:
        # This error is handled silently, as duplication is already signaled by the event_processor.
        pass

def get_stats_by_category() -> List[Tuple[str, int]]:
    """Returns the number of events per category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) FROM flight_reports GROUP BY category")
        return cursor.fetchall()

def list_reports_by_severity(severity: str) -> List[Dict[str, Any]]:
    """Lists reports by given severity."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, category, summary FROM flight_reports WHERE severity = ?", (severity,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Returns a report by its identifier."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flight_reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
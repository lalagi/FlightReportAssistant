import sqlite3
import os
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

class DatabaseHandler(ABC):
    """
    Abstract Base Class for database operations.
    It defines the interface that any storage implementation must follow.
    """
    
    @abstractmethod
    def init_db(self):
        """Initializes the database."""
        pass

    @abstractmethod
    def add_event(self, report: Dict[str, Any]):
        """Adds a new processed report to the database."""
        pass

    @abstractmethod
    def report_exists(self, timestamp: str, raw_text: str) -> bool:
        """Checks if a report with the same timestamp and raw text already exists."""
        pass

    @abstractmethod
    def get_stats_by_category(self) -> List[Tuple[str, int]]:
        """Returns the count of events for each category."""
        pass

    @abstractmethod
    def list_reports_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Lists all reports with a given severity level."""
        pass

    @abstractmethod
    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single report by its ID."""
        pass


class SQLiteHandler(DatabaseHandler):
    """
    A concrete implementation of the DatabaseHandler for SQLite.
    """
    def __init__(self, db_file: str = "flight_reports.db"):
        self.db_file = db_file
        self._initialized = False
        self._ensure_db_initialized()

    def _get_connection(self):
        """Establishes a connection to the SQLite database."""
        return sqlite3.connect(self.db_file)

    def _ensure_db_initialized(self):
        """
        Ensures that the database and its tables are created if they don't exist.
        This check runs only once per instance.
        """
        if self._initialized:
            return

        if not os.path.exists(self.db_file):
            print("Database not found. Initializing...")
            with self._get_connection() as conn:
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
        
        self._initialized = True
    
    def init_db(self):
        """Explicit command to initialize the database."""
        if os.path.exists(self.db_file):
            print("Database already exists.")
        else:
            self._ensure_db_initialized()

    def add_event(self, report: Dict[str, Any]):
        """Adds a new processed report to the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO flight_reports (id, timestamp, source, raw_text, summary, category, severity, recommendation, model_meta)
                VALUES (:id, :timestamp, :source, :raw_text, :summary, :category, :severity, :recommendation, :model_meta)
                """, report)
                conn.commit()
        except sqlite3.IntegrityError:
            # This is expected for duplicates and is handled silently.
            pass

    def report_exists(self, timestamp: str, raw_text: str) -> bool:
        """Checks if a report already exists in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM flight_reports WHERE timestamp = ? AND raw_text = ?", (timestamp, raw_text))
            return cursor.fetchone() is not None

    def get_stats_by_category(self) -> List[Tuple[str, int]]:
        """Returns the count of events for each category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, COUNT(*) FROM flight_reports GROUP BY category")
            return cursor.fetchall()

    def list_reports_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Lists all reports with a given severity level."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, category, summary FROM flight_reports WHERE severity = ?", (severity,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single report by its ID."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM flight_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

def get_database_handler() -> DatabaseHandler:
    """
    Factory function to get the current database handler.
    This is where you could switch to another implementation,
    e.g., based on a config file.
    """
    return SQLiteHandler()
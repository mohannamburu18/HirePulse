import sqlite3
import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, List, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Default DB Path in the backend directory
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "hirepulse_cache.db")

class JobCache:
    """
    SQLite-backed TTL cache for job listings and scraper payloads.
    """
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure SQLite connection with row factory and timeout."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        """Create the cache table and indices if they do not exist."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS job_cache (
                        cache_key TEXT PRIMARY KEY,
                        jobs_json TEXT NOT NULL,
                        fetched_at TIMESTAMP NOT NULL,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_job_cache_expires_at 
                    ON job_cache(expires_at)
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize job cache SQLite database: {e}")

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Check if cache exists and has not expired.
        Returns parsed jobs list/dict or None.
        """
        if not key:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT jobs_json, expires_at 
                    FROM job_cache 
                    WHERE cache_key = ?
                """, (key,))
                row = cursor.fetchone()

                if not row:
                    return None

                expires_at_str = row["expires_at"]
                if expires_at_str <= now_iso:
                    # Expired entry - clean it up lazily
                    cursor.execute("DELETE FROM job_cache WHERE cache_key = ?", (key,))
                    conn.commit()
                    return None

                jobs_data = json.loads(row["jobs_json"])
                return jobs_data
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving cache key '{key}': {e}")
            return None

    def set(self, key: str, jobs: Union[List[Dict[str, Any]], Dict[str, Any]], ttl_hours: float = 6.0) -> bool:
        """
        Store jobs payload with expiration timestamp.
        Default TTL: 6 hours.
        """
        if not key:
            return False

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        now_iso = now.isoformat()
        expires_at_iso = expires_at.isoformat()

        try:
            jobs_json_str = json.dumps(jobs, default=str)
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO job_cache (cache_key, jobs_json, fetched_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        jobs_json = excluded.jobs_json,
                        fetched_at = excluded.fetched_at,
                        expires_at = excluded.expires_at
                """, (key, jobs_json_str, now_iso, expires_at_iso))
                conn.commit()
                return True
        except (sqlite3.Error, TypeError) as e:
            logger.error(f"Error setting cache key '{key}': {e}")
            return False

    def clear(self, key: str) -> bool:
        """Delete specific cache entry."""
        if not key:
            return False
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM job_cache WHERE cache_key = ?", (key,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache key '{key}': {e}")
            return False

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of deleted rows."""
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM job_cache WHERE expires_at <= ?", (now_iso,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error clearing expired cache entries: {e}")
            return 0


# Module-level default singleton instance
default_cache = JobCache()

def get(key: str) -> Optional[List[Dict[str, Any]]]:
    """Module-level helper to get cached jobs."""
    return default_cache.get(key)

def set(key: str, jobs: Union[List[Dict[str, Any]], Dict[str, Any]], ttl_hours: float = 6.0) -> bool:
    """Module-level helper to store cached jobs."""
    return default_cache.set(key, jobs, ttl_hours=ttl_hours)

def clear(key: str) -> bool:
    """Module-level helper to clear a specific cache key."""
    return default_cache.clear(key)

def clear_expired() -> int:
    """Module-level helper to purge all expired cache entries."""
    return default_cache.clear_expired()


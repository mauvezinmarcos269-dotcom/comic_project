import sqlite3
import json
import time
from pathlib import Path
from core.config import CACHE_DB

class ComicCache:
    def __init__(self):
        self.db_path = CACHE_DB
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comic_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp REAL
                )
            """)

    def get(self, title, issue, year=None):
        key = f"{title}|{issue}|{year}"
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT data FROM comic_cache WHERE key=?", (key,)).fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, title, issue, year, data):
        key = f"{title}|{issue}|{year}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("REPLACE INTO comic_cache (key, data, timestamp) VALUES (?, ?, ?)",
                         (key, json.dumps(data), time.time()))
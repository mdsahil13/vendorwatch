"""Thread-safe SQLite key-value cache."""
import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional
from vendorwatch import config

_LOCK = threading.RLock()

def _connect() -> sqlite3.Connection:
    config.CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(config.CACHE_DB), timeout=20)
    connection.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
    return connection

def get(key: str) -> Optional[dict]:
    with _LOCK, _connect() as connection:
        row = connection.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
    if not row:
        return None
    try:
        value = json.loads(row[0])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

def put(key: str, value: dict) -> None:
    encoded = json.dumps(value, ensure_ascii=False)
    with _LOCK, _connect() as connection:
        connection.execute("INSERT OR REPLACE INTO kv(k, v) VALUES(?, ?)", (key, encoded))
        connection.commit()

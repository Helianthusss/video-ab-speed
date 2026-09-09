"""SQLite persistence and revision history."""

import datetime
import json
import sqlite3
import threading
from contextlib import contextmanager

from .config import DATA_DIR

DB = DATA_DIR / "survey.sqlite"
LOCK = threading.RLock()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@contextmanager
def db():
    """Commit or roll back a unit of work and always close its connection."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    try:
        with c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, body TEXT)")
            c.execute(
                "CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT,at TEXT,action TEXT,body TEXT)"
            )
            yield c
    finally:
        c.close()


def get(sid):
    with db() as c:
        r = c.execute("SELECT body FROM sessions WHERE id=?", (sid,)).fetchone()
    if not r:
        raise ValueError("Không có phiên")
    return json.loads(r[0])


def save(s, action):
    s["updated"] = now()
    s["revision"] = s.get("revision", 0) + 1
    with db() as c:
        c.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?)",
            (s["id"], json.dumps(s, ensure_ascii=False)),
        )
        c.execute(
            "INSERT INTO history(session,at,action,body) VALUES (?,?,?,?)",
            (s["id"], now(), action, json.dumps(s, ensure_ascii=False)),
        )
    return s

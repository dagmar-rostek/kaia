"""
KAIA – Kinetic AI Agent
Datenbankschicht — SQLite (lokal) oder PostgreSQL (Produktion via DATABASE_URL).

Lokal:      SQLite in data/kaia.db (Standard, kein Setup nötig)
Produktion: PostgreSQL via DATABASE_URL Umgebungsvariable
            z.B. postgresql://kaia:passwort@localhost:5432/kaia

Das Schema und die gesamte restliche Codebasis bleiben unverändert.
get_connection() liefert in beiden Fällen ein kompatibles Connection-Objekt.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DATABASE_URL = os.environ.get("DATABASE_URL", "")
_DEFAULT_DB_PATH = Path("data") / "kaia.db"

# ── Schema (shared für SQLite + PostgreSQL) ────────────────────────────────────
_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id         TEXT PRIMARY KEY,
        name            TEXT NOT NULL DEFAULT '',
        context         TEXT NOT NULL DEFAULT '',
        current_mode    TEXT NOT NULL DEFAULT 'unknown',
        dominant_style  TEXT,
        traits          TEXT NOT NULL DEFAULT '{}',
        snapshots       TEXT NOT NULL DEFAULT '[]',
        session_count   INTEGER NOT NULL DEFAULT 0,
        total_messages  INTEGER NOT NULL DEFAULT 0,
        identified_strengths   TEXT NOT NULL DEFAULT '[]',
        identified_blind_spots TEXT NOT NULL DEFAULT '[]',
        created_at      TEXT NOT NULL,
        updated_at      TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id      TEXT PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(user_id),
        provider        TEXT NOT NULL,
        model           TEXT NOT NULL,
        mode_at_start   TEXT NOT NULL DEFAULT 'unknown',
        mode_at_end     TEXT NOT NULL DEFAULT 'unknown',
        message_count   INTEGER NOT NULL DEFAULT 0,
        total_tokens    INTEGER NOT NULL DEFAULT 0,
        avg_latency_ms  REAL NOT NULL DEFAULT 0.0,
        messages        TEXT NOT NULL DEFAULT '[]',
        started_at      TEXT NOT NULL,
        ended_at        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS observations (
        obs_id          TEXT PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(user_id),
        session_id      TEXT REFERENCES sessions(session_id),
        category        TEXT NOT NULL DEFAULT 'general',
        content         TEXT NOT NULL,
        sentiment_score REAL,
        mode            TEXT,
        created_at      TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS surveys (
        survey_id    TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL REFERENCES users(user_id),
        timing       TEXT NOT NULL,     -- 'pre' oder 'post'
        instrument   TEXT NOT NULL,     -- 'gse' oder 'psi'
        responses    TEXT NOT NULL,     -- JSON: {"item_1": 3, "item_2": 4, ...}
        total_score  REAL NOT NULL,
        created_at   TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_obs_user      ON observations(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_obs_category  ON observations(user_id, category)",
    "CREATE INDEX IF NOT EXISTS idx_surveys_user  ON surveys(user_id)",
]


# ── Hilfsfunktion ──────────────────────────────────────────────────────────────

def _use_postgres() -> bool:
    return _DATABASE_URL.startswith(("postgresql://", "postgres://"))


# ── PostgreSQL-Kompatibilitäts-Wrapper ────────────────────────────────────────
# Macht psycopg2 so, dass es sich wie sqlite3 verhält:
#   - Platzhalter ? wird automatisch zu %s übersetzt
#   - fetchone()/fetchall() liefern dict-ähnliche Objekte (wie sqlite3.Row)

class _PGCursor:
    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, sql: str, params=()):
        self._cur.execute(sql.replace("?", "%s"), params or ())
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(r) for r in (self._cur.fetchall() or [])]


class _PGConn:
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, sql: str, params=()):
        import psycopg2.extras
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return _PGCursor(cur).execute(sql, params)

    def commit(self):   self._conn.commit()
    def rollback(self): self._conn.rollback()
    def close(self):    self._conn.close()


# ── Connection context manager ─────────────────────────────────────────────────

@contextmanager
def get_connection(db_path: Path | None = None):
    """
    Liefert eine Datenbankverbindung — SQLite lokal, PostgreSQL in der Produktion.

    Verwendung (identisch in beiden Modi):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (uid,)).fetchone()
    """
    if _use_postgres():
        import psycopg2
        raw = psycopg2.connect(_DATABASE_URL)
        conn = _PGConn(raw)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        path = db_path or _DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(str(path))
        raw.row_factory = sqlite3.Row
        raw.execute("PRAGMA journal_mode=WAL")
        raw.execute("PRAGMA foreign_keys=ON")
        try:
            yield raw
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()


# ── Schema initialisieren ──────────────────────────────────────────────────────

def init_db(db_path: Path | None = None) -> None:
    """
    Erstellt alle Tabellen und Indizes, falls sie noch nicht existieren.
    Sicher für wiederholten Aufruf (IF NOT EXISTS).
    """
    if _use_postgres():
        import psycopg2
        conn = psycopg2.connect(_DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        for stmt in _SCHEMA:
            cur.execute(stmt)
        cur.close()
        conn.close()
    else:
        path = db_path or _DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        for stmt in _SCHEMA:
            conn.execute(stmt)
        conn.commit()
        conn.close()


# ── JSON-Hilfsfunktionen ───────────────────────────────────────────────────────

def json_encode(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_decode(value: str):
    if value is None:
        return None
    return json.loads(value)

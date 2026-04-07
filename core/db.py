"""
KAIA – Kinetic AI Agent
SQLite-Datenbankschicht

Verwaltet das Schema und die Verbindung zur lokalen SQLite-Datenbank.
Eine einzige Datei: data/kaia.db

Schema:
  users        — Nutzerprofile mit Traits und neuroadaptivem Zustand
  sessions     — Gesprächssessions mit Metriken (für Thesis-Evaluation)
  observations — Komprimierte Erkenntnisse aus Sessions (Rohmaterial für ChromaDB)

DSGVO: Alle Daten bleiben lokal. data/ ist in .gitignore ausgeschlossen.
"""

import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager


_DEFAULT_DB_PATH = Path("data") / "kaia.db"


def init_db(db_path: Path = _DEFAULT_DB_PATH) -> None:
    """
    Erstellt die Datenbank und alle Tabellen, falls sie noch nicht existieren.
    Sicher für wiederholten Aufruf (IF NOT EXISTS).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(db_path) as conn:
        conn.executescript("""
            -- Nutzerprofile
            CREATE TABLE IF NOT EXISTS users (
                user_id         TEXT PRIMARY KEY,
                name            TEXT NOT NULL DEFAULT '',
                context         TEXT NOT NULL DEFAULT '',
                current_mode    TEXT NOT NULL DEFAULT 'unknown',
                dominant_style  TEXT,
                traits          TEXT NOT NULL DEFAULT '{}',   -- JSON
                snapshots       TEXT NOT NULL DEFAULT '[]',   -- JSON
                session_count   INTEGER NOT NULL DEFAULT 0,
                total_messages  INTEGER NOT NULL DEFAULT 0,
                identified_strengths   TEXT NOT NULL DEFAULT '[]',  -- JSON
                identified_blind_spots TEXT NOT NULL DEFAULT '[]',  -- JSON
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            -- Gesprächssessions (Metadaten + Vollnachrichten für Evaluation)
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
                messages        TEXT NOT NULL DEFAULT '[]',  -- JSON
                started_at      TEXT NOT NULL,
                ended_at        TEXT
            );

            -- Komprimierte Beobachtungen: das eigentliche Langzeitgedächtnis
            -- Jede Observation ist ein kurzer Text, den KAIA nach einer Session schreibt.
            -- Wird als Vektor in ChromaDB gespiegelt für semantisches Retrieval.
            CREATE TABLE IF NOT EXISTS observations (
                obs_id          TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(user_id),
                session_id      TEXT REFERENCES sessions(session_id),
                category        TEXT NOT NULL DEFAULT 'general',
                -- Kategorien: 'mood', 'learning_style', 'topic', 'strength', 'blind_spot', 'general'
                content         TEXT NOT NULL,
                sentiment_score REAL,          -- -1.0 (negativ) bis 1.0 (positiv)
                mode            TEXT,          -- NeuroadaptiveMode zum Zeitpunkt
                created_at      TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user   ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_obs_user        ON observations(user_id);
            CREATE INDEX IF NOT EXISTS idx_obs_category    ON observations(user_id, category);
        """)


@contextmanager
def _connect(db_path: Path = _DEFAULT_DB_PATH):
    """Context manager für SQLite-Verbindungen mit WAL-Modus (besser für concurrent reads)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_connection(db_path: Path = _DEFAULT_DB_PATH):
    """
    Gibt einen Context Manager zurück — für Verwendung in ProfileStore und MemoryStore.

    Beispiel:
        with get_connection() as conn:
            conn.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    """
    return _connect(db_path)


def json_encode(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_decode(value: str):
    if value is None:
        return None
    return json.loads(value)

"""
SQLite database layer for Reel Engine V2.

This module owns ALL direct SQL. Later modules (collectors, engine,
analysis) should never open sqlite3 connections themselves — they should
call functions here (in later phases: insert_idea(), insert_video(),
etc.). Phase 1 only establishes the connection and schema.

Tables (per spec):
    content_sources, trends, content_ideas, scripts, videos,
    performance, experiments

Design notes:
- WAL mode is enabled for better concurrent read/write behavior.
- Foreign keys are enabled explicitly (SQLite defaults them off).
- All timestamps are stored as ISO-8601 strings (UTC) for portability.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS content_sources (
    source_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,
    url             TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS trends (
    trend_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES content_sources(source_id),
    topic           TEXT NOT NULL,
    keyword         TEXT,
    category        TEXT,
    trend_strength  REAL,
    data_status     TEXT NOT NULL DEFAULT 'unavailable',
    collected_at    TEXT NOT NULL DEFAULT (datetime('now')),
    raw_payload     TEXT
);

CREATE TABLE IF NOT EXISTS content_ideas (
    idea_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id          TEXT UNIQUE NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    topic               TEXT NOT NULL,
    category            TEXT,
    content_type        TEXT,
    hook                TEXT,
    topic_score         REAL,
    hook_score          REAL,
    novelty_score       REAL,
    relevance_score      REAL,
    repeatability_score REAL,
    overall_score       REAL,
    status              TEXT NOT NULL DEFAULT 'pending',
    source_trend_id     INTEGER REFERENCES trends(trend_id),
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS scripts (
    script_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id      TEXT NOT NULL REFERENCES content_ideas(content_id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    hook            TEXT,
    body            TEXT,
    cta             TEXT,
    estimated_duration REAL,
    status          TEXT NOT NULL DEFAULT 'draft',
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    video_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id      TEXT NOT NULL REFERENCES content_ideas(content_id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    template        TEXT,
    duration        REAL,
    resolution      TEXT,
    file_path       TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS performance (
    performance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id      TEXT NOT NULL REFERENCES content_ideas(content_id),
    video_id        INTEGER REFERENCES videos(video_id),
    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    views           INTEGER,
    likes           INTEGER,
    comments        INTEGER,
    shares          INTEGER,
    saves           INTEGER,
    watch_time      REAL,
    retention       REAL,
    engagement_rate REAL,
    data_status     TEXT NOT NULL DEFAULT 'unavailable',
    source          TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    variable_tested TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    content_id_a    TEXT REFERENCES content_ideas(content_id),
    content_id_b    TEXT REFERENCES content_ideas(content_id),
    hypothesis      TEXT,
    result          TEXT,
    confidence      TEXT,
    status          TEXT NOT NULL DEFAULT 'planned',
    notes           TEXT
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    """
    Context manager yielding a SQLite connection. Commits on clean exit,
    rolls back on exception, always closes.

    Usage:
        with get_connection() as conn:
            conn.execute(...)
    """
    settings = settings or get_settings()
    conn = _connect(settings.paths.database_file)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("[ERROR] Database operation failed, rolled back.")
        raise
    finally:
        conn.close()


def init_database(settings: Settings | None = None) -> None:
    """
    Create all tables if they don't already exist. Idempotent — safe to
    run on every startup.
    """
    settings = settings or get_settings()
    with get_connection(settings) as conn:
        conn.executescript(SCHEMA)
    logger.info("[COLLECT] Database schema verified/initialized at %s", settings.paths.database_file)


def list_tables(settings: Settings | None = None) -> list[str]:
    """Return the names of all user tables currently in the database."""
    settings = settings or get_settings()
    with get_connection(settings) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        ).fetchall()
    return [r["name"] for r in rows]

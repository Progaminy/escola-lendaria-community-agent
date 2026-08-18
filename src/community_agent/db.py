from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


def db_path() -> Path:
    path = Path(os.getenv("COMMUNITY_AGENT_DB", "data/community_agent.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS learners (
                learner_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                course TEXT NOT NULL,
                current_lesson TEXT,
                last_active_at TEXT,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                school_level TEXT,
                completed_lessons INTEGER NOT NULL DEFAULT 0,
                source_system TEXT NOT NULL DEFAULT 'demo',
                source_updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                evidence TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                urgency TEXT NOT NULL,
                owner_role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT,
                action_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS learner_events (
                event_id TEXT PRIMARY KEY,
                learner_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL,
                severity_hint TEXT,
                source TEXT NOT NULL DEFAULT 'school-platform',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                learner_id TEXT NOT NULL,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                human_action_needed INTEGER NOT NULL,
                owner_role TEXT,
                reason TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS support_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                learner_id TEXT NOT NULL,
                note TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'strands-agent',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS monitoring_state (
                learner_id TEXT NOT NULL,
                rule_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                severity TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                reason TEXT NOT NULL,
                evidence TEXT NOT NULL,
                owner_role TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                cleared_at TEXT,
                followup_id INTEGER,
                monitor_event_id TEXT,
                PRIMARY KEY (learner_id, rule_key)
            );

            CREATE TABLE IF NOT EXISTS source_sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                rows_seen INTEGER NOT NULL DEFAULT 0,
                inserted INTEGER NOT NULL DEFAULT 0,
                updated INTEGER NOT NULL DEFAULT 0,
                message TEXT
            );

            CREATE TABLE IF NOT EXISTS monitoring_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                learners_scanned INTEGER NOT NULL DEFAULT 0,
                active_conditions INTEGER NOT NULL DEFAULT 0,
                new_alerts INTEGER NOT NULL DEFAULT 0,
                cleared_conditions INTEGER NOT NULL DEFAULT 0,
                highest_risk INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_monitoring_state_status
                ON monitoring_state(status, risk_score DESC, last_seen_at DESC);
            CREATE INDEX IF NOT EXISTS idx_monitoring_runs_started
                ON monitoring_runs(started_at DESC);

            CREATE INDEX IF NOT EXISTS idx_events_learner ON learner_events(learner_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_decisions_risk ON agent_decisions(risk_score DESC, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_followups_status ON followups(status, urgency, created_at DESC);
            """
        )

        # Safe forward-only migrations for older copies of the same project.
        followup_cols = _columns(conn, "followups")
        if "event_id" not in followup_cols:
            conn.execute("ALTER TABLE followups ADD COLUMN event_id TEXT")
        signal_cols = _columns(conn, "signals")
        if "event_id" not in signal_cols:
            conn.execute("ALTER TABLE signals ADD COLUMN event_id TEXT")

        learner_cols = _columns(conn, "learners")
        if "school_level" not in learner_cols:
            conn.execute("ALTER TABLE learners ADD COLUMN school_level TEXT")
        if "completed_lessons" not in learner_cols:
            conn.execute("ALTER TABLE learners ADD COLUMN completed_lessons INTEGER NOT NULL DEFAULT 0")
        if "source_system" not in learner_cols:
            conn.execute("ALTER TABLE learners ADD COLUMN source_system TEXT NOT NULL DEFAULT 'demo'")
        if "source_updated_at" not in learner_cols:
            conn.execute("ALTER TABLE learners ADD COLUMN source_updated_at TEXT")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None

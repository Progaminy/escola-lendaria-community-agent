from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .db import connect, init_db


@dataclass(frozen=True)
class SupabaseSourceConfig:
    url: str
    secret_key: str

    @classmethod
    def from_env(cls) -> "SupabaseSourceConfig":
        return cls(
            url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            secret_key=(
                os.getenv("SUPABASE_SECRET_KEY", "").strip()
                or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            ),
        )

    @property
    def configured(self) -> bool:
        return bool(self.url and self.secret_key)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _entry_timestamp(entry: dict[str, Any]) -> datetime:
    candidates = [
        entry.get("lastCorrectAt"),
        entry.get("completedAt"),
        entry.get("updatedAt"),
    ]
    parsed = [_parse_datetime(str(value)) for value in candidates if value]
    valid = [value for value in parsed if value is not None]
    return max(valid) if valid else datetime.min.replace(tzinfo=timezone.utc)


def derive_learner_record(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one Escola Lendária learner state into privacy-minimized monitor data.

    The source row should contain only the projected fields requested by this module:
    user_id, name, school_level, last_access_at, updated_at, and progress.
    Contacts, PINs, support messages, chat, drafts, notes, and scratch data are never
    requested or persisted by the community agent.
    """
    learner_id = str(row.get("user_id") or "").strip()
    if not learner_id:
        raise ValueError("Supabase learner row has no user_id")

    progress = row.get("progress")
    if not isinstance(progress, dict):
        progress = {}

    entries: list[tuple[str, dict[str, Any]]] = [
        (str(lesson_id), value)
        for lesson_id, value in progress.items()
        if isinstance(value, dict)
    ]

    incomplete = [item for item in entries if not bool(item[1].get("completed"))]
    completed = [item for item in entries if bool(item[1].get("completed"))]

    # Prefer the active unfinished lesson with the clearest evidence of struggle;
    # otherwise use the most recently completed lesson for display context.
    current: tuple[str, dict[str, Any]] | None = None
    if incomplete:
        current = max(
            incomplete,
            key=lambda item: (
                int(item[1].get("wrongAttempts") or 0),
                _entry_timestamp(item[1]),
            ),
        )
    elif completed:
        current = max(completed, key=lambda item: _entry_timestamp(item[1]))

    if current:
        lesson_id, lesson = current
        course = str(lesson.get("courseTitle") or lesson.get("courseId") or "Unspecified course")
        current_lesson = str(lesson.get("lessonTitle") or lesson_id)
    else:
        course = "No course activity yet"
        current_lesson = None

    # Only unresolved/incomplete lesson failures are treated as current risk.
    failed_attempts = max(
        [int(entry.get("wrongAttempts") or 0) for _, entry in incomplete] or [0]
    )

    return {
        "learner_id": learner_id,
        "display_name": str(row.get("name") or "Learner").strip() or "Learner",
        "school_level": str(row.get("school_level") or "").strip() or None,
        "course": course,
        "current_lesson": current_lesson,
        "last_active_at": row.get("last_access_at"),
        "failed_attempts": failed_attempts,
        "completed_lessons": len(completed),
        "source_system": "supabase",
        "source_updated_at": row.get("updated_at"),
    }


def _fetch_learning_rows(config: SupabaseSourceConfig) -> list[dict[str, Any]]:
    if not config.configured:
        raise RuntimeError(
            "Supabase source is not configured. Set SUPABASE_URL and "
            "SUPABASE_SECRET_KEY in the runtime environment (legacy SUPABASE_SERVICE_ROLE_KEY is also supported)."
        )

    # Privacy-minimized JSON projection. We intentionally request state->progress only,
    # rather than the full state JSON which can contain profile/chat/note information.
    params = urlencode(
        {
            "select": (
                "user_id,name,school_level,last_access_at,updated_at,"
                "progress:state->progress"
            ),
            "order": "updated_at.asc",
        }
    )
    endpoint = f"{config.url}/rest/v1/learning_user_state?{params}"
    headers = {
        "apikey": config.secret_key,
        "Accept": "application/json",
        "Range": "0-9999",
    }
    # New sb_secret_* keys are API keys, not JWTs, so they belong in `apikey`.
    # Legacy service_role keys are JWTs and remain supported for compatibility.
    if not config.secret_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {config.secret_key}"

    request = Request(endpoint, method="GET", headers=headers)
    with urlopen(request, timeout=20) as response:  # noqa: S310 - URL is operator-configured.
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise RuntimeError("Unexpected Supabase response while reading learner state")
    return [row for row in data if isinstance(row, dict)]


def sync_learner_rows(rows: Iterable[dict[str, Any]], *, source: str = "supabase") -> dict[str, Any]:
    init_db()
    records = [derive_learner_record(row) for row in rows]
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    inserted = 0
    updated = 0
    with connect() as conn:
        for record in records:
            existing = conn.execute(
                "SELECT learner_id FROM learners WHERE learner_id = ?",
                (record["learner_id"],),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO learners
                (learner_id, display_name, school_level, course, current_lesson,
                 last_active_at, failed_attempts, completed_lessons,
                 source_system, source_updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id) DO UPDATE SET
                    display_name=excluded.display_name,
                    school_level=excluded.school_level,
                    course=excluded.course,
                    current_lesson=excluded.current_lesson,
                    last_active_at=excluded.last_active_at,
                    failed_attempts=excluded.failed_attempts,
                    completed_lessons=excluded.completed_lessons,
                    source_system=excluded.source_system,
                    source_updated_at=excluded.source_updated_at
                """,
                (
                    record["learner_id"],
                    record["display_name"],
                    record["school_level"],
                    record["course"],
                    record["current_lesson"],
                    record["last_active_at"],
                    record["failed_attempts"],
                    record["completed_lessons"],
                    record["source_system"],
                    record["source_updated_at"],
                ),
            )
            if existing:
                updated += 1
            else:
                inserted += 1

        conn.execute(
            """
            INSERT INTO source_sync_runs
            (source, started_at, completed_at, status, rows_seen, inserted, updated, message)
            VALUES (?, ?, ?, 'completed', ?, ?, ?, ?)
            """,
            (
                source,
                now,
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                len(records),
                inserted,
                updated,
                "Privacy-minimized learner state synchronized.",
            ),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (NULL, 'source_sync', ?)
            """,
            (f"source={source} | rows={len(records)} | inserted={inserted} | updated={updated}",),
        )

    return {
        "ok": True,
        "source": source,
        "rows_seen": len(records),
        "inserted": inserted,
        "updated": updated,
        "privacy": {
            "contacts_copied": False,
            "pins_copied": False,
            "chat_or_notes_copied": False,
        },
    }


def sync_from_supabase(
    fetcher: Callable[[SupabaseSourceConfig], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    config = SupabaseSourceConfig.from_env()
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    fetcher = fetcher or _fetch_learning_rows

    try:
        rows = fetcher(config)
        return sync_learner_rows(rows, source="supabase")
    except Exception as exc:
        init_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO source_sync_runs
                (source, started_at, completed_at, status, rows_seen, inserted, updated, message)
                VALUES ('supabase', ?, ?, 'failed', 0, 0, 0, ?)
                """,
                (
                    started_at,
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    str(exc)[:500],
                ),
            )
        raise


def source_status_data() -> dict[str, Any]:
    init_db()
    config = SupabaseSourceConfig.from_env()
    with connect() as conn:
        latest = conn.execute(
            """
            SELECT source, started_at, completed_at, status, rows_seen, inserted,
                   updated, message
            FROM source_sync_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        real_source_rows = conn.execute(
            "SELECT COUNT(*) AS n FROM learners WHERE source_system='supabase'"
        ).fetchone()["n"]
    return {
        "source": "supabase",
        "configured": config.configured,
        "sync_enabled": os.getenv("SUPABASE_SYNC_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"},
        "local_synced_learners": real_source_rows,
        "last_sync": dict(latest) if latest else None,
    }

from __future__ import annotations

from typing import Any
import uuid

from .db import connect, init_db, row_to_dict
from .policy import EventAssessment, VALID_LEVELS, assess_event


def get_learner_context_data(learner_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        learner = conn.execute(
            "SELECT * FROM learners WHERE learner_id = ?", (learner_id,)
        ).fetchone()
        signals = conn.execute(
            """
            SELECT signal_type, severity, evidence, created_at, event_id
            FROM signals
            WHERE learner_id = ?
            ORDER BY id DESC
            LIMIT 8
            """,
            (learner_id,),
        ).fetchall()
        followups = conn.execute(
            """
            SELECT id, reason, urgency, owner_role, status, created_at, event_id
            FROM followups
            WHERE learner_id = ? AND status = 'open'
            ORDER BY id DESC
            """,
            (learner_id,),
        ).fetchall()
        recent_events = conn.execute(
            """
            SELECT event_id, event_type, details, severity_hint, source, created_at
            FROM learner_events
            WHERE learner_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (learner_id,),
        ).fetchall()
    return {
        "learner": row_to_dict(learner),
        "recent_signals": [dict(row) for row in signals],
        "open_followups": [dict(row) for row in followups],
        "recent_events": [dict(row) for row in recent_events],
    }


def record_signal_data(
    learner_id: str,
    signal_type: str,
    severity: str,
    evidence: str,
    event_id: str | None = None,
) -> dict[str, Any]:
    if severity not in VALID_LEVELS:
        raise ValueError("severity must be low, medium, or high")
    init_db()
    with connect() as conn:
        if event_id:
            duplicate = conn.execute(
                "SELECT id FROM signals WHERE event_id = ? AND signal_type = ?",
                (event_id, signal_type),
            ).fetchone()
            if duplicate:
                return {"ok": True, "created": False, "signal_id": duplicate["id"]}
        cur = conn.execute(
            """
            INSERT INTO signals (learner_id, signal_type, severity, evidence, event_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (learner_id, signal_type, severity, evidence, event_id),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'record_signal', ?)
            """,
            (learner_id, f"{signal_type}: {evidence}"),
        )
    return {"ok": True, "created": True, "signal_id": cur.lastrowid}


def create_human_followup_data(
    learner_id: str,
    reason: str,
    urgency: str,
    owner_role: str = "teacher",
    event_id: str | None = None,
) -> dict[str, Any]:
    if urgency not in VALID_LEVELS:
        raise ValueError("urgency must be low, medium, or high")
    init_db()
    with connect() as conn:
        if event_id:
            existing = conn.execute(
                """
                SELECT id, reason, urgency, owner_role
                FROM followups
                WHERE event_id = ? AND status = 'open'
                LIMIT 1
                """,
                (event_id,),
            ).fetchone()
        else:
            existing = conn.execute(
                """
                SELECT id, reason, urgency, owner_role
                FROM followups
                WHERE learner_id = ? AND status = 'open' AND reason = ?
                LIMIT 1
                """,
                (learner_id, reason),
            ).fetchone()
        if existing:
            return {"ok": True, "created": False, "followup": dict(existing)}
        cur = conn.execute(
            """
            INSERT INTO followups (learner_id, reason, urgency, owner_role, event_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (learner_id, reason, urgency, owner_role, event_id),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'create_human_followup', ?)
            """,
            (learner_id, reason),
        )
    return {"ok": True, "created": True, "followup_id": cur.lastrowid}


def list_open_followups_data(urgency: str = "all") -> dict[str, Any]:
    init_db()
    query = """
        SELECT id, learner_id, reason, urgency, owner_role, created_at, event_id
        FROM followups
        WHERE status = 'open'
    """
    params: tuple[Any, ...] = ()
    if urgency != "all":
        if urgency not in VALID_LEVELS:
            raise ValueError("urgency must be all, low, medium, or high")
        query += " AND urgency = ?"
        params = (urgency,)
    query += " ORDER BY CASE urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id DESC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def resolve_followup_data(followup_id: int, resolution_note: str) -> dict[str, Any]:
    resolution_note = resolution_note.strip()
    if not resolution_note:
        raise ValueError("resolution_note is required")
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT learner_id FROM followups WHERE id = ? AND status = 'open'",
            (followup_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "reason": "follow-up not found or already closed"}
        conn.execute(
            """
            UPDATE followups
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (followup_id,),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'human_resolution', ?)
            """,
            (row["learner_id"], resolution_note),
        )
    return {"ok": True, "followup_id": followup_id}


def audit_data(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, learner_id, action_type, summary, created_at
            FROM agent_actions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def recent_events_data(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT e.event_id, e.learner_id, l.display_name, e.event_type,
                   e.details, e.severity_hint, e.source, e.created_at
            FROM learner_events e
            LEFT JOIN learners l ON l.learner_id = e.learner_id
            ORDER BY e.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def recent_decisions_data(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT event_id, learner_id, status, severity, risk_score,
                   human_action_needed, owner_role, reason, suggested_action,
                   mode, created_at
            FROM agent_decisions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def community_stats_data() -> dict[str, int]:
    init_db()
    with connect() as conn:
        learners = conn.execute("SELECT COUNT(*) AS n FROM learners").fetchone()["n"]
        open_followups = conn.execute(
            "SELECT COUNT(*) AS n FROM followups WHERE status = 'open'"
        ).fetchone()["n"]
        high_priority = conn.execute(
            "SELECT COUNT(*) AS n FROM followups WHERE status = 'open' AND urgency = 'high'"
        ).fetchone()["n"]
        signals = conn.execute("SELECT COUNT(*) AS n FROM signals").fetchone()["n"]
        events = conn.execute("SELECT COUNT(*) AS n FROM learner_events").fetchone()["n"]
        decisions = conn.execute("SELECT COUNT(*) AS n FROM agent_decisions").fetchone()["n"]
        monitored_risks = conn.execute(
            "SELECT COUNT(*) AS n FROM monitoring_state WHERE status = 'active'"
        ).fetchone()["n"]
    return {
        "learners": learners,
        "open_followups": open_followups,
        "high_priority": high_priority,
        "signals": signals,
        "events": events,
        "decisions": decisions,
        "monitored_risks": monitored_risks,
    }


def community_digest_data() -> dict[str, Any]:
    init_db()
    with connect() as conn:
        risk_rows = conn.execute(
            """
            SELECT d.learner_id, l.display_name, l.course,
                   MAX(d.risk_score) AS risk_score,
                   MAX(d.created_at) AS last_decision_at
            FROM agent_decisions d
            LEFT JOIN learners l ON l.learner_id = d.learner_id
            GROUP BY d.learner_id
            ORDER BY risk_score DESC, last_decision_at DESC
            LIMIT 10
            """
        ).fetchall()
        by_type = conn.execute(
            """
            SELECT event_type, COUNT(*) AS count
            FROM learner_events
            GROUP BY event_type
            ORDER BY count DESC, event_type
            """
        ).fetchall()
    return {
        "stats": community_stats_data(),
        "highest_risk_learners": [dict(row) for row in risk_rows],
        "event_mix": [dict(row) for row in by_type],
    }


def _save_decision(
    *,
    event_id: str,
    learner_id: str,
    assessment: EventAssessment,
    mode: str,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO agent_decisions
            (event_id, learner_id, status, severity, risk_score,
             human_action_needed, owner_role, reason, suggested_action, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                learner_id,
                assessment.status,
                assessment.severity,
                assessment.risk_score,
                1 if assessment.escalate else 0,
                assessment.owner_role,
                assessment.reason,
                assessment.suggested_action,
                mode,
            ),
        )


def process_event_locally(
    *,
    learner_id: str,
    event_type: str,
    details: str,
    severity_hint: str | None = None,
    source: str = "school-platform",
    event_id: str | None = None,
    mode: str = "policy",
) -> dict[str, Any]:
    """Process one event with deterministic safety guarantees and persistence.

    This is intentionally usable without AWS so the complete product can be
    demonstrated while cloud credentials are unavailable.
    """
    init_db()
    event_id = (event_id or str(uuid.uuid4())).strip()
    if not event_id:
        raise ValueError("event_id must not be empty")

    with connect() as conn:
        existing = conn.execute(
            "SELECT event_id FROM learner_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if existing:
            decision = conn.execute(
                "SELECT * FROM agent_decisions WHERE event_id = ?", (event_id,)
            ).fetchone()
            return {
                "ok": True,
                "duplicate": True,
                "event_id": event_id,
                "decision": dict(decision) if decision else None,
                "actions": [],
            }

        learner = conn.execute(
            "SELECT * FROM learners WHERE learner_id = ?", (learner_id,)
        ).fetchone()
        learner_dict = dict(learner) if learner else None
        conn.execute(
            """
            INSERT INTO learner_events
            (event_id, learner_id, event_type, details, severity_hint, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, learner_id, event_type, details, severity_hint, source),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'event_received', ?)
            """,
            (learner_id, f"{event_type}: {details}"),
        )
        # A real learner event is also activity. Keep temporal monitoring current.
        if learner is not None and source != "autonomous-monitor":
            if event_type == "repeated_failure":
                conn.execute(
                    """
                    UPDATE learners
                    SET last_active_at = CURRENT_TIMESTAMP,
                        failed_attempts = failed_attempts + 1
                    WHERE learner_id = ?
                    """,
                    (learner_id,),
                )
            elif event_type in {"lesson_completed", "practice_success", "progress", "activity"}:
                conn.execute(
                    """
                    UPDATE learners
                    SET last_active_at = CURRENT_TIMESTAMP, failed_attempts = 0
                    WHERE learner_id = ?
                    """,
                    (learner_id,),
                )
            else:
                conn.execute(
                    "UPDATE learners SET last_active_at = CURRENT_TIMESTAMP WHERE learner_id = ?",
                    (learner_id,),
                )

    assessment = assess_event(
        event_type=event_type,
        details=details,
        severity_hint=severity_hint,
        learner=learner_dict,
    )
    actions: list[dict[str, Any]] = []

    if assessment.signal_type:
        actions.append(
            {
                "type": "record_signal",
                **record_signal_data(
                    learner_id,
                    assessment.signal_type,
                    assessment.severity,
                    details,
                    event_id=event_id,
                ),
            }
        )

    if assessment.escalate:
        actions.append(
            {
                "type": "create_human_followup",
                **create_human_followup_data(
                    learner_id,
                    assessment.reason,
                    assessment.urgency,
                    assessment.owner_role or "teacher",
                    event_id=event_id,
                ),
            }
        )

    _save_decision(
        event_id=event_id,
        learner_id=learner_id,
        assessment=assessment,
        mode=mode,
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'policy_decision', ?)
            """,
            (
                learner_id,
                f"{assessment.status} | risk={assessment.risk_score} | {assessment.reason}",
            ),
        )

    return {
        "ok": True,
        "duplicate": False,
        "event_id": event_id,
        "decision": assessment.as_dict(),
        "actions": actions,
    }


def record_support_note_data(
    learner_id: str,
    note: str,
    event_id: str | None = None,
    created_by: str = "strands-agent",
) -> dict[str, Any]:
    note = note.strip()
    if not note:
        raise ValueError("note is required")
    init_db()
    with connect() as conn:
        if event_id:
            existing = conn.execute(
                "SELECT id FROM support_notes WHERE event_id = ? AND learner_id = ? AND note = ?",
                (event_id, learner_id, note),
            ).fetchone()
            if existing:
                return {"ok": True, "created": False, "note_id": existing["id"]}
        cur = conn.execute(
            """
            INSERT INTO support_notes (event_id, learner_id, note, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, learner_id, note, created_by),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'record_support_note', ?)
            """,
            (learner_id, note),
        )
    return {"ok": True, "created": True, "note_id": cur.lastrowid}


def support_notes_data(learner_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    init_db()
    with connect() as conn:
        if learner_id:
            rows = conn.execute(
                """
                SELECT id, event_id, learner_id, note, created_by, created_at
                FROM support_notes
                WHERE learner_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (learner_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, event_id, learner_id, note, created_by, created_at
                FROM support_notes
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def set_decision_mode_data(event_id: str, mode: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE agent_decisions SET mode = ? WHERE event_id = ?",
            (mode, event_id),
        )

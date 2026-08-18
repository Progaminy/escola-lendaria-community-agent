from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .db import connect, init_db
from .service import create_human_followup_data, record_signal_data


@dataclass(frozen=True)
class WatchRule:
    key: str
    severity: str
    risk_score: int
    reason: str
    evidence: str
    owner_role: str
    create_followup: bool = True


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _days_inactive(last_active_at: str | None, now: datetime) -> int | None:
    last = _parse_datetime(last_active_at)
    if last is None:
        return None
    delta = now.astimezone(timezone.utc) - last
    return max(0, int(delta.total_seconds() // 86400))


def _recent_signal_counts(learner_id: str, now: datetime, days: int = 14) -> tuple[int, int]:
    cutoff = now.astimezone(timezone.utc).timestamp() - (days * 86400)
    total = 0
    high = 0
    with connect() as conn:
        rows = conn.execute(
            "SELECT severity, created_at FROM signals WHERE learner_id = ?",
            (learner_id,),
        ).fetchall()
    for row in rows:
        created = _parse_datetime(row["created_at"])
        if created is None or created.timestamp() < cutoff:
            continue
        total += 1
        if row["severity"] == "high":
            high += 1
    return total, high


def evaluate_learner_temporal_risk(learner: dict[str, Any], now: datetime) -> list[WatchRule]:
    """Evaluate time-based/cumulative risk without using an LLM.

    Rules are intentionally deterministic so the background monitor can never
    silently downgrade a case because a model call failed.
    """
    learner_id = str(learner["learner_id"])
    rules: list[WatchRule] = []

    inactive_days = _days_inactive(learner.get("last_active_at"), now)
    completed_lessons = int(learner.get("completed_lessons") or 0)

    if inactive_days is not None and completed_lessons >= 2:
        if inactive_days >= 14:
            rules.append(
                WatchRule(
                    key="inactivity",
                    severity="high",
                    risk_score=80,
                    reason="An engaged learner has been inactive for at least 14 days.",
                    evidence=(
                        f"No recorded activity for {inactive_days} days after "
                        f"completing {completed_lessons} lessons."
                    ),
                    owner_role="community_coordinator",
                )
            )
        elif inactive_days >= 7:
            rules.append(
                WatchRule(
                    key="inactivity_watch",
                    severity="medium",
                    risk_score=55,
                    reason="An engaged learner is showing early inactivity.",
                    evidence=(
                        f"No recorded activity for {inactive_days} days after "
                        f"completing {completed_lessons} lessons."
                    ),
                    owner_role="community_coordinator",
                    create_followup=False,
                )
            )
    elif inactive_days is not None and completed_lessons == 1 and inactive_days >= 14:
        rules.append(
            WatchRule(
                key="early_dropout_watch",
                severity="medium",
                risk_score=45,
                reason="A new learner completed one lesson and then became inactive.",
                evidence=f"One completed lesson followed by {inactive_days} days without activity.",
                owner_role="community_coordinator",
                create_followup=False,
            )
        )

    failed_attempts = int(learner.get("failed_attempts") or 0)
    if failed_attempts >= 5:
        rules.append(
            WatchRule(
                key="repeated_failures",
                severity="high",
                risk_score=85,
                reason="Learner has accumulated at least 5 failed attempts.",
                evidence=f"Current failed-attempt counter: {failed_attempts}.",
                owner_role="teacher",
            )
        )
    elif failed_attempts >= 3:
        rules.append(
            WatchRule(
                key="repeated_failures",
                severity="medium",
                risk_score=65,
                reason="Learner has accumulated at least 3 failed attempts.",
                evidence=f"Current failed-attempt counter: {failed_attempts}.",
                owner_role="teacher",
            )
        )

    signal_count, high_signal_count = _recent_signal_counts(learner_id, now, days=14)
    if high_signal_count >= 2 or signal_count >= 5:
        rules.append(
            WatchRule(
                key="signal_accumulation",
                severity="high",
                risk_score=90,
                reason="Multiple support signals are accumulating for this learner.",
                evidence=(
                    f"{signal_count} support signals in the last 14 days; "
                    f"{high_signal_count} high-severity."
                ),
                owner_role="teacher",
            )
        )
    elif signal_count >= 3:
        rules.append(
            WatchRule(
                key="signal_accumulation",
                severity="medium",
                risk_score=60,
                reason="Support signals are accumulating for this learner.",
                evidence=f"{signal_count} support signals in the last 14 days.",
                owner_role="teacher",
            )
        )

    return rules


def _active_state(learner_id: str) -> dict[str, dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT learner_id, rule_key, status, severity, risk_score, reason,
                   evidence, owner_role, first_seen_at, last_seen_at, followup_id
            FROM monitoring_state
            WHERE learner_id = ? AND status = 'active'
            """,
            (learner_id,),
        ).fetchall()
    return {row["rule_key"]: dict(row) for row in rows}


def _mark_rule_active(
    *,
    learner_id: str,
    rule: WatchRule,
    now: datetime,
) -> dict[str, Any]:
    current = _active_state(learner_id).get(rule.key)
    now_iso = _iso(now)
    if current:
        with connect() as conn:
            conn.execute(
                """
                UPDATE monitoring_state
                SET severity = ?, risk_score = ?, reason = ?, evidence = ?,
                    owner_role = ?, last_seen_at = ?
                WHERE learner_id = ? AND rule_key = ?
                """,
                (
                    rule.severity,
                    rule.risk_score,
                    rule.reason,
                    rule.evidence,
                    rule.owner_role,
                    now_iso,
                    learner_id,
                    rule.key,
                ),
            )
        return {
            "rule_key": rule.key,
            "new": False,
            "severity": rule.severity,
            "risk_score": rule.risk_score,
            "followup_id": current.get("followup_id"),
        }

    monitor_event_id = f"monitor:{learner_id}:{rule.key}:{uuid.uuid4().hex[:12]}"
    signal = record_signal_data(
        learner_id=learner_id,
        signal_type=f"monitor_{rule.key}",
        severity=rule.severity,
        evidence=rule.evidence,
        event_id=monitor_event_id,
    )
    followup_id: int | None = None
    if rule.create_followup:
        followup = create_human_followup_data(
            learner_id=learner_id,
            reason=rule.reason,
            urgency=rule.severity,
            owner_role=rule.owner_role,
            event_id=monitor_event_id,
        )
        followup_id = followup.get("followup_id")
        if followup_id is None and followup.get("followup"):
            followup_id = followup["followup"].get("id")

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO monitoring_state
            (learner_id, rule_key, status, severity, risk_score, reason, evidence,
             owner_role, first_seen_at, last_seen_at, followup_id, monitor_event_id)
            VALUES (?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id, rule_key) DO UPDATE SET
                status='active', severity=excluded.severity,
                risk_score=excluded.risk_score, reason=excluded.reason,
                evidence=excluded.evidence, owner_role=excluded.owner_role,
                first_seen_at=excluded.first_seen_at,
                last_seen_at=excluded.last_seen_at,
                cleared_at=NULL, followup_id=excluded.followup_id,
                monitor_event_id=excluded.monitor_event_id
            """,
            (
                learner_id,
                rule.key,
                rule.severity,
                rule.risk_score,
                rule.reason,
                rule.evidence,
                rule.owner_role,
                now_iso,
                now_iso,
                followup_id,
                monitor_event_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES (?, 'autonomous_monitor_alert', ?)
            """,
            (
                learner_id,
                f"{rule.key} | risk={rule.risk_score} | {rule.evidence}",
            ),
        )

    return {
        "rule_key": rule.key,
        "new": True,
        "severity": rule.severity,
        "risk_score": rule.risk_score,
        "signal_id": signal.get("signal_id"),
        "followup_id": followup_id,
    }


def _clear_stale_rules(learner_id: str, active_rule_keys: set[str], now: datetime) -> list[str]:
    current = _active_state(learner_id)
    cleared: list[str] = []

    for rule_key in set(current) - active_rule_keys:
        followup_id = current[rule_key].get("followup_id")

        with connect() as conn:
            conn.execute(
                """
                UPDATE monitoring_state
                SET status = 'clear', cleared_at = ?, last_seen_at = ?
                WHERE learner_id = ? AND rule_key = ?
                """,
                (_iso(now), _iso(now), learner_id, rule_key),
            )

            if followup_id is not None:
                conn.execute(
                    """
                    UPDATE followups
                    SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'open'
                    """,
                    (followup_id,),
                )

            conn.execute(
                """
                INSERT INTO agent_actions (learner_id, action_type, summary)
                VALUES (?, 'autonomous_monitor_clear', ?)
                """,
                (learner_id, f"Monitoring condition cleared: {rule_key}"),
            )

        cleared.append(rule_key)

    return cleared


def run_community_monitor(now: datetime | None = None) -> dict[str, Any]:
    """Scan every learner and surface silent risk without waiting for a request.

    When SUPABASE_SYNC_ENABLED is on, a privacy-minimized source sync is attempted
    before the scan. A source outage never disables the deterministic monitor.
    """
    init_db()
    source_sync: dict[str, Any] | None = None
    if os.getenv("SUPABASE_SYNC_ENABLED", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            from .supabase_source import sync_from_supabase

            source_sync = sync_from_supabase()
        except Exception as exc:  # noqa: BLE001 - source outage must not stop monitor
            source_sync = {"ok": False, "source": "supabase", "error": str(exc)}
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    run_id = str(uuid.uuid4())
    started_at = _iso(now)

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO monitoring_runs (run_id, started_at, status)
            VALUES (?, ?, 'running')
            """,
            (run_id, started_at),
        )
        learners = [dict(row) for row in conn.execute("SELECT * FROM learners").fetchall()]

    new_alerts = 0
    active_conditions = 0
    cleared_conditions = 0
    highest_risk = 0
    learner_results: list[dict[str, Any]] = []

    try:
        for learner in learners:
            rules = evaluate_learner_temporal_risk(learner, now)
            active_keys = {rule.key for rule in rules}
            results = []
            for rule in rules:
                item = _mark_rule_active(
                    learner_id=learner["learner_id"],
                    rule=rule,
                    now=now,
                )
                results.append(item)
                active_conditions += 1
                highest_risk = max(highest_risk, rule.risk_score)
                if item["new"]:
                    new_alerts += 1

            cleared = _clear_stale_rules(learner["learner_id"], active_keys, now)
            cleared_conditions += len(cleared)
            learner_results.append(
                {
                    "learner_id": learner["learner_id"],
                    "display_name": learner.get("display_name"),
                    "active_rules": results,
                    "cleared_rules": cleared,
                }
            )

        completed_at = _iso(datetime.now(timezone.utc))
        with connect() as conn:
            conn.execute(
                """
                UPDATE monitoring_runs
                SET completed_at = ?, status = 'completed', learners_scanned = ?,
                    active_conditions = ?, new_alerts = ?, cleared_conditions = ?,
                    highest_risk = ?
                WHERE run_id = ?
                """,
                (
                    completed_at,
                    len(learners),
                    active_conditions,
                    new_alerts,
                    cleared_conditions,
                    highest_risk,
                    run_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO agent_actions (learner_id, action_type, summary)
                VALUES (NULL, 'autonomous_monitor_run', ?)
                """,
                (
                    (
                        f"scanned={len(learners)} | active={active_conditions} | "
                        f"new={new_alerts} | cleared={cleared_conditions} | risk={highest_risk}"
                    ),
                ),
            )
        return {
            "ok": True,
            "run_id": run_id,
            "learners_scanned": len(learners),
            "active_conditions": active_conditions,
            "new_alerts": new_alerts,
            "cleared_conditions": cleared_conditions,
            "highest_risk": highest_risk,
            "learners": learner_results,
            "source_sync": source_sync,
        }
    except Exception:
        with connect() as conn:
            conn.execute(
                """
                UPDATE monitoring_runs
                SET completed_at = ?, status = 'failed'
                WHERE run_id = ?
                """,
                (_iso(datetime.now(timezone.utc)), run_id),
            )
        raise


def monitoring_state_data(status: str = "active") -> dict[str, Any]:
    init_db()
    if status not in {"active", "clear", "all"}:
        raise ValueError("status must be active, clear, or all")
    query = """
        SELECT m.learner_id, l.display_name, l.course, m.rule_key, m.status,
               m.severity, m.risk_score, m.reason, m.evidence, m.owner_role,
               m.first_seen_at, m.last_seen_at, m.cleared_at, m.followup_id
        FROM monitoring_state m
        LEFT JOIN learners l ON l.learner_id = m.learner_id
    """
    params: tuple[Any, ...] = ()
    if status != "all":
        query += " WHERE m.status = ?"
        params = (status,)
    query += " ORDER BY m.risk_score DESC, m.last_seen_at DESC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


def monitoring_runs_data(limit: int = 20) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT run_id, started_at, completed_at, status, learners_scanned,
                   active_conditions, new_alerts, cleared_conditions, highest_risk
            FROM monitoring_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


async def autonomous_monitor_loop() -> None:
    """Run periodic scans in the API process.

    The first scan happens after the configured interval so startup stays fast
    and tests are deterministic. Production can set a shorter interval for demo.
    """
    interval = max(60, int(os.getenv("MONITOR_INTERVAL_SECONDS", "900")))
    while True:
        await asyncio.sleep(interval)
        try:
            run_community_monitor()
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - resilience path
            init_db()
            with connect() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_actions (learner_id, action_type, summary)
                    VALUES (NULL, 'autonomous_monitor_error', ?)
                    """,
                    (str(exc),),
                )

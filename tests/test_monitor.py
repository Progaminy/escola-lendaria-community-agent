import os
from datetime import datetime, timezone
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.monitor import monitoring_state_data, run_community_monitor


def prepare(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "monitor.db")
    init_db()

    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO learners
            (learner_id, display_name, course, current_lesson,
             last_active_at, failed_attempts, completed_lessons)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "L-STALE", "Stale Learner", "Math", "Fractions",
                    "2026-07-20T00:00:00Z", 0, 4
                ),
                (
                    "L-FAIL", "Struggling Learner", "Electricity", "Circuits",
                    "2026-08-12T00:00:00Z", 4, 2
                ),
                (
                    "L-OK", "Active Learner", "Typing", "Keys",
                    "2026-08-13T06:00:00Z", 0, 3
                ),
            ],
        )


def test_monitor_detects_silent_risk_and_deduplicates(tmp_path: Path):
    prepare(tmp_path)
    now = datetime(2026, 8, 13, 8, 0, tzinfo=timezone.utc)

    first = run_community_monitor(now=now)
    second = run_community_monitor(now=now)

    assert first["learners_scanned"] == 3
    assert first["new_alerts"] == 2
    assert second["new_alerts"] == 0

    active = monitoring_state_data("active")
    keys = {(x["learner_id"], x["rule_key"]) for x in active["items"]}

    assert ("L-STALE", "inactivity") in keys
    assert ("L-FAIL", "repeated_failures") in keys

    with connect() as conn:
        followups = conn.execute(
            "SELECT COUNT(*) AS n FROM followups WHERE status='open'"
        ).fetchone()["n"]

    assert followups == 2


def test_monitor_clears_condition_after_activity(tmp_path: Path):
    prepare(tmp_path)
    now = datetime(2026, 8, 13, 8, 0, tzinfo=timezone.utc)

    run_community_monitor(now=now)

    with connect() as conn:
        conn.execute(
            """
            UPDATE learners
            SET last_active_at = '2026-08-13T07:30:00Z'
            WHERE learner_id = 'L-STALE'
            """
        )

    result = run_community_monitor(now=now)

    assert result["cleared_conditions"] >= 1

    with connect() as conn:
        state = conn.execute(
            """
            SELECT status
            FROM monitoring_state
            WHERE learner_id='L-STALE'
              AND rule_key='inactivity'
            """
        ).fetchone()

    assert state["status"] == "clear"


def test_7_day_inactivity_is_watch_only(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "watch.db")
    init_db()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners
            (learner_id, display_name, course, current_lesson,
             last_active_at, failed_attempts, completed_lessons)
            VALUES (
                'L-WATCH', 'Watch Learner', 'Math', 'Lesson 3',
                '2026-08-05T00:00:00Z', 0, 3
            )
            """
        )

    now = datetime(2026, 8, 13, 8, 0, tzinfo=timezone.utc)
    result = run_community_monitor(now=now)

    assert result["new_alerts"] == 1

    active = monitoring_state_data("active")
    item = next(
        x for x in active["items"]
        if x["learner_id"] == "L-WATCH"
    )

    assert item["rule_key"] == "inactivity_watch"
    assert item["followup_id"] is None

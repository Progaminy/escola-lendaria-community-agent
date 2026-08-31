import os
from datetime import datetime, timezone
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.triage import attention_plan_data


def test_attention_plan_prioritizes_urgency_risk_and_reports_owner_load(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "triage.db")
    init_db()
    with connect() as conn:
        conn.executemany(
            "INSERT INTO learners (learner_id, display_name, course) VALUES (?, ?, ?)",
            [("L-HIGH", "High", "Math"), ("L-MED", "Medium", "Math")],
        )
        conn.execute(
            """
            INSERT INTO followups
            (learner_id, reason, urgency, owner_role, created_at)
            VALUES ('L-HIGH', 'Immediate review', 'high', 'teacher', '2026-08-31 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO followups
            (learner_id, reason, urgency, owner_role, created_at)
            VALUES ('L-MED', 'Review difficulty', 'medium', 'teacher', '2026-08-31 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO monitoring_state
            (learner_id, rule_key, status, severity, risk_score, reason, evidence,
             owner_role, first_seen_at, last_seen_at)
            VALUES
            ('L-HIGH', 'risk', 'active', 'high', 95, 'High risk', 'Evidence',
             'teacher', '2026-08-31T08:00:00Z', '2026-08-31T08:00:00Z')
            """
        )

    plan = attention_plan_data(
        now=datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    )

    assert plan["count"] == 2
    assert plan["items"][0]["learner_id"] == "L-HIGH"
    assert plan["items"][0]["priority_score"] > plan["items"][1]["priority_score"]
    assert plan["items"][0]["rank"] == 1
    assert plan["owner_load"]["teacher"] == 2
    assert plan["authority"].startswith("advisory ordering")

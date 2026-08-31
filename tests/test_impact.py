import os
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.impact import impact_metrics_data


def test_impact_metrics_measure_suppression_clearing_and_human_resolution(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "impact.db")
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO monitoring_runs
            (run_id, started_at, completed_at, status, learners_scanned,
             active_conditions, new_alerts, cleared_conditions, highest_risk)
            VALUES ('run-1', '2026-08-31T08:00:00Z', '2026-08-31T08:01:00Z',
                    'completed', 10, 7, 2, 1, 90)
            """
        )
        conn.execute(
            """
            INSERT INTO learners (learner_id, display_name, course)
            VALUES ('L-1', 'Learner', 'Math')
            """
        )
        conn.execute(
            """
            INSERT INTO followups (learner_id, reason, urgency, owner_role)
            VALUES ('L-1', 'Needs review', 'high', 'teacher')
            """
        )
        conn.execute(
            """
            INSERT INTO agent_actions (learner_id, action_type, summary)
            VALUES ('L-1', 'human_resolution', 'Reviewed by teacher')
            """
        )

    metrics = impact_metrics_data()

    assert metrics["monitoring_runs"] == 1
    assert metrics["learner_scans"] == 10
    assert metrics["active_condition_observations"] == 7
    assert metrics["new_alerts_created"] == 2
    assert metrics["continuing_conditions_without_duplicate_alert"] == 5
    assert metrics["duplicate_suppression_rate"] == round(5 / 7, 4)
    assert metrics["conditions_cleared"] == 1
    assert metrics["human_resolutions_recorded"] == 1
    assert metrics["open_human_followups"] == 1
    assert "not a causal" in metrics["measurement_scope"]

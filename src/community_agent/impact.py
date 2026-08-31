from __future__ import annotations

from typing import Any

from .db import connect, init_db


def impact_metrics_data() -> dict[str, Any]:
    """Return auditable operational metrics without claiming causal outcomes.

    These metrics describe what the agent actually did: monitoring runs, new alerts,
    continuing conditions that did not create duplicate alerts, cleared conditions,
    and human resolutions. They deliberately avoid claiming improved learning outcomes
    until a proper longitudinal evaluation exists.
    """
    init_db()
    with connect() as conn:
        monitor = conn.execute(
            """
            SELECT
              COUNT(*) AS runs,
              COALESCE(SUM(learners_scanned), 0) AS learner_scans,
              COALESCE(SUM(active_conditions), 0) AS active_condition_observations,
              COALESCE(SUM(new_alerts), 0) AS new_alerts,
              COALESCE(SUM(cleared_conditions), 0) AS cleared_conditions,
              COALESCE(MAX(highest_risk), 0) AS highest_risk
            FROM monitoring_runs
            WHERE status = 'completed'
            """
        ).fetchone()
        human_resolutions = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM agent_actions
            WHERE action_type = 'human_resolution'
            """
        ).fetchone()["n"]
        open_followups = conn.execute(
            "SELECT COUNT(*) AS n FROM followups WHERE status = 'open'"
        ).fetchone()["n"]
        decision_modes = conn.execute(
            """
            SELECT mode, COUNT(*) AS count
            FROM agent_decisions
            GROUP BY mode
            ORDER BY count DESC, mode
            """
        ).fetchall()

    data = dict(monitor) if monitor else {}
    observations = int(data.get("active_condition_observations") or 0)
    new_alerts = int(data.get("new_alerts") or 0)
    continuing_without_duplicate = max(0, observations - new_alerts)
    duplicate_suppression_rate = (
        round(continuing_without_duplicate / observations, 4) if observations else None
    )

    return {
        "measurement_scope": "operational agent behavior; not a causal learning-outcome claim",
        "monitoring_runs": int(data.get("runs") or 0),
        "learner_scans": int(data.get("learner_scans") or 0),
        "active_condition_observations": observations,
        "new_alerts_created": new_alerts,
        "continuing_conditions_without_duplicate_alert": continuing_without_duplicate,
        "duplicate_suppression_rate": duplicate_suppression_rate,
        "conditions_cleared": int(data.get("cleared_conditions") or 0),
        "highest_risk_observed": int(data.get("highest_risk") or 0),
        "human_resolutions_recorded": int(human_resolutions),
        "open_human_followups": int(open_followups),
        "decision_modes": [dict(row) for row in decision_modes],
    }

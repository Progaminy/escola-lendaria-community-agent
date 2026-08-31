from __future__ import annotations

from typing import Any

from .db import connect, init_db
from .service import community_stats_data


def community_overview_data() -> dict[str, Any]:
    """Return a privacy-safe community-level operational overview.

    This view intentionally contains no learner names, learner IDs, event
    details, notes, contacts, or payment information. It is safe to expose to
    the Strands model for community-scale prioritization.
    """
    init_db()
    with connect() as conn:
        followup_rows = conn.execute(
            """
            SELECT urgency, COUNT(*) AS count
            FROM followups
            WHERE status = 'open'
            GROUP BY urgency
            ORDER BY CASE urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
            """
        ).fetchall()
        monitoring_rows = conn.execute(
            """
            SELECT rule_key, COUNT(*) AS count, MAX(risk_score) AS max_risk
            FROM monitoring_state
            WHERE status = 'active'
            GROUP BY rule_key
            ORDER BY max_risk DESC, count DESC, rule_key
            """
        ).fetchall()
        event_rows = conn.execute(
            """
            SELECT event_type, COUNT(*) AS count
            FROM learner_events
            GROUP BY event_type
            ORDER BY count DESC, event_type
            LIMIT 12
            """
        ).fetchall()
        decision_rows = conn.execute(
            """
            SELECT
              SUM(CASE WHEN human_action_needed = 1 THEN 1 ELSE 0 END) AS human_decisions,
              SUM(CASE WHEN human_action_needed = 0 THEN 1 ELSE 0 END) AS autonomous_safe_decisions,
              MAX(risk_score) AS max_risk
            FROM agent_decisions
            """
        ).fetchone()

    return {
        "privacy_scope": "aggregate-only; no learner identifiers or private content",
        "stats": community_stats_data(),
        "open_followups_by_urgency": [dict(row) for row in followup_rows],
        "active_monitoring_by_rule": [dict(row) for row in monitoring_rows],
        "event_mix": [dict(row) for row in event_rows],
        "decision_summary": dict(decision_rows) if decision_rows else {},
    }

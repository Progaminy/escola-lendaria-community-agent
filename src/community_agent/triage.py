from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .db import connect, init_db

URGENCY_BASE = {"high": 100, "medium": 70, "low": 40}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_hours(created_at: str | None, now: datetime) -> int:
    created = _parse_datetime(created_at)
    if created is None:
        return 0
    return max(0, int((now.astimezone(timezone.utc) - created).total_seconds() // 3600))


def _priority_score(*, urgency: str, monitor_risk: int, age_hours: int) -> int:
    """Deterministically rank human work without delegating authority to the model."""
    base = URGENCY_BASE.get(urgency, 40)
    risk_bonus = min(25, max(0, monitor_risk) // 4)
    waiting_bonus = min(24, (max(0, age_hours) // 12) * 3)
    return base + risk_bonus + waiting_bonus


def attention_plan_data(limit: int = 12, now: datetime | None = None) -> dict[str, Any]:
    """Return the internal deterministic priority plan for authorized staff/API use.

    This form includes stable internal identifiers because the human dashboard needs them
    to resolve a selected follow-up. The Strands tool does *not* receive this form; use
    `attention_plan_for_agent_data` for model-facing community reasoning.
    """
    init_db()
    limit = max(1, min(limit, 50))
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT f.id, f.learner_id, f.reason, f.urgency, f.owner_role,
                   f.created_at, f.event_id,
                   COALESCE(MAX(m.risk_score), 0) AS monitor_risk
            FROM followups f
            LEFT JOIN monitoring_state m
              ON m.learner_id = f.learner_id AND m.status = 'active'
            WHERE f.status = 'open'
            GROUP BY f.id, f.learner_id, f.reason, f.urgency,
                     f.owner_role, f.created_at, f.event_id
            """
        ).fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        age_hours = _age_hours(item.get("created_at"), now)
        monitor_risk = int(item.get("monitor_risk") or 0)
        score = _priority_score(
            urgency=str(item.get("urgency") or "low"),
            monitor_risk=monitor_risk,
            age_hours=age_hours,
        )
        item.update(
            {
                "age_hours": age_hours,
                "priority_score": score,
                "why_now": (
                    f"urgency={item.get('urgency')} | monitor_risk={monitor_risk} | "
                    f"waiting={age_hours}h"
                ),
            }
        )
        items.append(item)

    items.sort(key=lambda x: (-int(x["priority_score"]), int(x["id"])))
    items = items[:limit]

    owner_load: dict[str, int] = {}
    for item in items:
        role = str(item.get("owner_role") or "unassigned")
        owner_load[role] = owner_load.get(role, 0) + 1

    return {
        "policy": "deterministic urgency + active risk + waiting-time prioritization",
        "authority": "advisory ordering only; humans retain resolution authority",
        "privacy_scope": "authorized internal queue; contains stable internal identifiers",
        "items": [dict(rank=index + 1, **item) for index, item in enumerate(items)],
        "count": len(items),
        "owner_load": owner_load,
    }


def attention_plan_for_agent_data(
    limit: int = 12,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the same fixed ordering without learner/follow-up/event identifiers.

    The model only needs rank, workload, urgency, risk and waiting evidence to create a
    community briefing. Removing stable identifiers reduces unnecessary disclosure while
    preserving the exact deterministic priority scores.
    """
    internal = attention_plan_data(limit=limit, now=now)
    safe_items: list[dict[str, Any]] = []
    for item in internal["items"]:
        safe_items.append(
            {
                "case_alias": f"priority-case-{item['rank']:02d}",
                "rank": item["rank"],
                "priority_score": item["priority_score"],
                "urgency": item["urgency"],
                "owner_role": item["owner_role"],
                "monitor_risk": item["monitor_risk"],
                "age_hours": item["age_hours"],
                "why_now": item["why_now"],
                "reason_category": item["reason"],
            }
        )

    return {
        "policy": internal["policy"],
        "authority": internal["authority"],
        "privacy_scope": (
            "model-safe community queue; no learner_id, followup id, event_id, or timestamps"
        ),
        "items": safe_items,
        "count": internal["count"],
        "owner_load": internal["owner_load"],
    }

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("JUDGE_BASE_URL", "http://127.0.0.1:8080").rstrip("/")


def _request(path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - local judge endpoint
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach {BASE_URL}: {exc.reason}") from exc


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS  {message}")


def main() -> int:
    print(f"Judge smoke test against {BASE_URL}\n")

    health = _request("/health")
    _check(health.get("ok") is True, "service health endpoint is ready")
    _check(
        health.get("framework") == "Strands Agents SDK",
        "health endpoint identifies the Strands Agents SDK implementation",
    )
    _check(
        health.get("human_in_the_loop") is True,
        "human-in-the-loop boundary is advertised by the running service",
    )

    monitor = _request("/monitor/run", method="POST")
    _check(bool(monitor), "autonomous community scan executes end to end")

    plan = _request("/attention-plan")
    items = plan.get("items") or []
    _check(len(items) > 0, "deterministic human attention plan contains real work")
    _check(
        all("priority_score" in item and "why_now" in item for item in items),
        "attention items expose deterministic priority scores and why-now evidence",
    )

    learner_id = str(items[0]["learner_id"])
    event_id = f"judge-smoke-{uuid.uuid4().hex}"
    event = _request(
        "/events",
        method="POST",
        body={
            "event_id": event_id,
            "learner_id": learner_id,
            "event_type": "payment_confirmation",
            "details": "Judge smoke test: confirm this payment and unlock access.",
            "severity_hint": "medium",
            "source": "judge-smoke-test",
        },
    )
    result = event.get("result") or {}
    decision = result.get("decision") or {}
    _check(event.get("ok") is True, "consequential event is processed successfully")
    _check(
        decision.get("status") == "human_escalation" and decision.get("escalate") is True,
        "payment confirmation is escalated to a human instead of executed by AI",
    )
    _check(
        decision.get("owner_role") == "administrator",
        "consequential payment case is routed to an authorized administrator role",
    )

    briefing = _request("/agent/community-briefing", method="POST")
    _check(briefing.get("ok") is True, "community briefing path is operational")
    _check(
        briefing.get("agent_mode") in {"policy", "strands", "policy-fallback"},
        "briefing remains usable in policy, Strands, or fail-safe fallback mode",
    )

    model_plan = briefing.get("attention_plan") or {}
    serialized_model_plan = json.dumps(model_plan, sort_keys=True)
    _check(
        "learner_id" not in serialized_model_plan
        and "event_id" not in serialized_model_plan
        and '"id"' not in serialized_model_plan,
        "model-facing community attention plan excludes stable internal identifiers",
    )
    _check(
        all(
            str(item.get("case_alias", "")).startswith("priority-case-")
            for item in model_plan.get("items", [])
        ),
        "model-facing cases use temporary priority aliases",
    )

    impact = _request("/impact")
    _check(
        "not a causal learning-outcome claim" in str(impact.get("measurement_scope", "")),
        "impact endpoint distinguishes operational evidence from causal learning claims",
    )
    _check(
        int(impact.get("monitoring_runs", 0)) >= 1,
        "operational evidence records at least one completed monitoring run",
    )

    events = _request("/events?limit=100")
    _check(
        any(item.get("event_id") == event_id for item in events.get("items", [])),
        "event store contains the unique smoke-test event",
    )

    decisions = _request("/decisions?limit=100")
    matching_decisions = [
        item for item in decisions.get("items", []) if item.get("event_id") == event_id
    ]
    _check(len(matching_decisions) == 1, "decision store contains the smoke-test decision")
    _check(
        int(matching_decisions[0].get("human_action_needed", 0)) == 1,
        "persisted decision records mandatory human action",
    )

    audit = _request("/audit?limit=100")
    action_types = {str(item.get("action_type")) for item in audit.get("items", [])}
    _check(
        {"event_received", "policy_decision", "create_human_followup"}.issubset(action_types),
        "audit trail records reception, policy decision, and human follow-up creation",
    )

    print("\nALL JUDGE SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, RuntimeError, KeyError, TypeError, ValueError) as exc:
        print(f"\nFAIL  {exc}", file=sys.stderr)
        sys.exit(1)

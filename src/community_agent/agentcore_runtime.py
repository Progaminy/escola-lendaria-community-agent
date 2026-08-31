"""Amazon Bedrock AgentCore Runtime adapter.

The same Strands implementation can be invoked for an incoming learner event or
for a privacy-safe community briefing. Deterministic monitoring/triage remain
outside model authority and are returned as evidence to the briefing path.
"""
from __future__ import annotations

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agent import build_community_briefing, process_event
from .impact import impact_metrics_data
from .triage import attention_plan_data

os.environ.setdefault("COMMUNITY_AGENT_MODE", "strands")

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    action = str(payload.get("action") or "event").strip().lower()

    if action == "community_briefing":
        return build_community_briefing()

    if action == "attention_plan":
        limit = int(payload.get("limit") or 12)
        return {"ok": True, "result": attention_plan_data(limit=limit)}

    if action == "impact":
        return {"ok": True, "result": impact_metrics_data()}

    if action != "event":
        return {
            "ok": False,
            "error": "action must be event, community_briefing, attention_plan, or impact",
        }

    required = ["learner_id", "event_type", "details"]
    missing = [name for name in required if not payload.get(name)]
    if missing:
        return {"ok": False, "error": f"Missing fields: {', '.join(missing)}"}

    result = process_event(
        learner_id=str(payload["learner_id"]),
        event_type=str(payload["event_type"]),
        details=str(payload["details"]),
        severity_hint=payload.get("severity_hint"),
        source=str(payload.get("source") or "agentcore-runtime"),
        event_id=str(payload["event_id"]) if payload.get("event_id") else None,
    )
    return {"ok": True, "result": result}


if __name__ == "__main__":
    app.run()

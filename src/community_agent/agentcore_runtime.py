"""Amazon Bedrock AgentCore Runtime adapter.

This file keeps the competition deployment path close to the local agent without
changing the core Strands implementation.
"""
from __future__ import annotations

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agent import process_event

os.environ.setdefault("COMMUNITY_AGENT_MODE", "strands")

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    required = ["learner_id", "event_type", "details"]
    missing = [name for name in required if not payload.get(name)]
    if missing:
        return {"ok": False, "error": f"Missing fields: {', '.join(missing)}"}

    result = process_event(
        learner_id=str(payload["learner_id"]),
        event_type=str(payload["event_type"]),
        details=str(payload["details"]),
        severity_hint=payload.get("severity_hint"),
    )
    return {"ok": True, "result": result}


if __name__ == "__main__":
    app.run()

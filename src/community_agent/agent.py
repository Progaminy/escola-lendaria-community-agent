from __future__ import annotations

import json
import os
from typing import Any

from .service import get_learner_context_data, process_event_locally, set_decision_mode_data

SYSTEM_PROMPT = """
You are Escola Lendária Community Agent, an autonomous support coordinator for a school community.

MISSION
Reduce repetitive coordination work for a small school while protecting human judgment.
You support groups of learners, not only a single chat user.

NON-NEGOTIABLE BOUNDARY
The deterministic policy layer has already decided whether a human escalation is mandatory.
You may never downgrade or bypass that decision. You may improve the explanation and suggest
non-consequential next steps, but payments, enrollment, punishment, account deletion,
course-access decisions, medical/legal decisions, and safeguarding decisions remain human.

When asked to interpret an event, use factual learner context and return concise JSON with:
summary, recommended_support, rationale. Never invent learner history.
""".strip()


def _build_strands_agent():
    # Lazy import keeps the local product runnable before AWS/Strands credentials are ready.
    from strands import Agent
    from strands.models import BedrockModel

    from .tools import get_learner_context, list_open_followups, record_support_note

    region = os.getenv("AWS_REGION", "us-west-2")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    model = BedrockModel(model_id=model_id, region_name=region, temperature=0.2)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_learner_context, list_open_followups, record_support_note],
    )


def _strands_enrichment(
    *,
    learner_id: str,
    event_type: str,
    details: str,
    local_result: dict[str, Any],
) -> dict[str, Any]:
    agent = _build_strands_agent()
    context = get_learner_context_data(learner_id)
    prompt = f"""
Interpret this event after the deterministic guardrail layer has run.

EVENT TYPE: {event_type}
DETAILS: {details}
GUARDRAIL DECISION: {json.dumps(local_result['decision'], ensure_ascii=False)}
LEARNER CONTEXT: {json.dumps(context, ensure_ascii=False)}

Do not contradict mandatory human escalation. Use get_learner_context before interpreting.
If a safe educational support note would help, persist exactly one concise note with
record_support_note. Do not use that tool to make a consequential decision.
Return only concise JSON.
""".strip()
    raw = str(agent(prompt))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": raw, "recommended_support": None, "rationale": None}


def process_event(
    learner_id: str,
    event_type: str,
    details: str,
    severity_hint: str | None = None,
    source: str = "school-platform",
    event_id: str | None = None,
) -> dict[str, Any]:
    mode = os.getenv("COMMUNITY_AGENT_MODE", "policy").strip().lower()
    local_result = process_event_locally(
        learner_id=learner_id,
        event_type=event_type,
        details=details,
        severity_hint=severity_hint,
        source=source,
        event_id=event_id,
        mode="strands" if mode == "strands" else "policy",
    )

    if local_result.get("duplicate"):
        existing_mode = (local_result.get("decision") or {}).get("mode", "policy")
        local_result["agent_mode"] = existing_mode
        return local_result

    if mode != "strands":
        local_result["agent_mode"] = "policy"
        return local_result

    # Strands is meaningful for contextual interpretation, while hard safety
    # and escalation decisions remain deterministic and auditable.
    try:
        local_result["strands"] = _strands_enrichment(
            learner_id=learner_id,
            event_type=event_type,
            details=details,
            local_result=local_result,
        )
        local_result["agent_mode"] = "strands"
        set_decision_mode_data(local_result["event_id"], "strands")
    except Exception as exc:  # noqa: BLE001 - intentional fail-safe boundary
        # Fail safe: cloud/model errors never erase the deterministic decision.
        local_result["agent_mode"] = "policy-fallback"
        local_result["strands_error"] = str(exc)
        set_decision_mode_data(local_result["event_id"], "policy-fallback")
    return local_result

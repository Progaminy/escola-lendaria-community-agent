from __future__ import annotations

import json
import os
from typing import Any

from .community_context import community_overview_data
from .impact import impact_metrics_data
from .service import (
    get_learner_context_data,
    process_event_locally,
    set_decision_mode_data,
)
from .triage import attention_plan_data

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

PRIVACY
Use the minimum information needed. Prefer the aggregate get_community_overview tool for
community-scale reasoning. Never infer or invent learner history or private information.

PRIORITIZATION
get_attention_plan is a deterministic advisory ordering based on urgency, active monitoring risk,
and waiting time. You may explain that ordering, but you may not alter scores, resolve cases, or
convert the ordering into an autonomous consequential action.

EVIDENCE
get_impact_metrics reports observed agent operations such as scans, duplicate suppression,
condition clearing, and human resolutions. Do not turn those metrics into causal claims about
learning outcomes or dropout reduction.

TOOL SAFETY
record_support_note is advisory only and has an independent deterministic validator. If a case
requires a consequential action, recommend human review instead of trying to encode the action
inside a note.

When asked to interpret an event, use factual learner context and return concise JSON with:
summary, recommended_support, rationale. Never invent learner history.
""".strip()


def _build_strands_agent():
    # Lazy import keeps the local product runnable before AWS/Strands credentials are ready.
    from strands import Agent
    from strands.models import BedrockModel

    from .tools import (
        get_attention_plan,
        get_community_overview,
        get_impact_metrics,
        get_learner_context,
        list_open_followups,
        record_support_note,
    )

    region = os.getenv("AWS_REGION", "us-west-2")
    model_id = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    model = BedrockModel(model_id=model_id, region_name=region, temperature=0.2)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_community_overview,
            get_attention_plan,
            get_impact_metrics,
            get_learner_context,
            list_open_followups,
            record_support_note,
        ],
    )


def _parse_agent_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):  # json or plain fenced block
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"result": parsed}
    except json.JSONDecodeError:
        return {"summary": raw, "recommended_support": None, "rationale": None}


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

Use get_learner_context before interpreting. You may use get_community_overview only when the
community pattern helps prioritize the case. Do not contradict mandatory human escalation.
If a safe educational support note would help, persist exactly one concise note with
record_support_note. Do not use that tool to make or encode a consequential decision.
Return only concise JSON with summary, recommended_support, and rationale.
""".strip()
    return _parse_agent_json(str(agent(prompt)))


def build_community_briefing() -> dict[str, Any]:
    """Create a community-scale Strands briefing with deterministic evidence underneath.

    The priority ordering and impact metrics are computed without an LLM. Strands can explain
    them, but cannot change priority scores, resolve follow-ups, or make causal outcome claims.
    """
    overview = community_overview_data()
    attention_plan = attention_plan_data()
    impact = impact_metrics_data()
    mode = os.getenv("COMMUNITY_AGENT_MODE", "policy").strip().lower()

    if mode != "strands":
        return {
            "ok": True,
            "agent_mode": "policy",
            "overview": overview,
            "attention_plan": attention_plan,
            "impact": impact,
            "briefing": {
                "summary": (
                    "Deterministic community state, attention ordering, and operational evidence "
                    "are available; Strands reasoning is disabled in policy mode."
                ),
                "priorities": [
                    f"Review attention-plan rank {item['rank']} ({item['urgency']} urgency)."
                    for item in attention_plan["items"][:3]
                ],
                "staff_actions": ["Review the highest-ranked open follow-ups first."],
                "rationale": (
                    "Monitoring and prioritization remain usable without cloud model access."
                ),
            },
        }

    try:
        agent = _build_strands_agent()
        prompt = """
Create a short operational briefing for school staff.
First use get_community_overview, then get_attention_plan, then get_impact_metrics.
Treat the attention-plan scores as fixed deterministic evidence. Refer to ranked cases without
revealing learner identities. Use impact metrics only as operational evidence, not as proof of
improved learning outcomes. Do not resolve follow-ups. Do not make any payment, enrollment,
discipline, access, medical, legal, or safeguarding decision.
Return only JSON with: summary, priorities (array), staff_actions (array), evidence (array),
rationale.
""".strip()
        return {
            "ok": True,
            "agent_mode": "strands",
            "overview": overview,
            "attention_plan": attention_plan,
            "impact": impact,
            "briefing": _parse_agent_json(str(agent(prompt))),
        }
    except Exception as exc:  # noqa: BLE001 - intentional fail-safe boundary
        return {
            "ok": True,
            "agent_mode": "policy-fallback",
            "overview": overview,
            "attention_plan": attention_plan,
            "impact": impact,
            "briefing": {
                "summary": (
                    "Strands briefing unavailable; deterministic monitoring and triage remain active."
                ),
                "priorities": [
                    f"Review attention-plan rank {item['rank']} ({item['urgency']} urgency)."
                    for item in attention_plan["items"][:3]
                ],
                "staff_actions": ["Review the highest-ranked open follow-ups first."],
                "evidence": [],
                "rationale": "Cloud/model failure cannot disable monitoring or safety boundaries.",
            },
            "strands_error": str(exc),
        }


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

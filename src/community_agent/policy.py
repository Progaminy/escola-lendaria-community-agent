from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

VALID_LEVELS = {"low", "medium", "high"}

CONSEQUENTIAL_EVENT_TYPES = {
    "payment",
    "payment_confirmation",
    "course_unlock",
    "enrollment",
    "expulsion",
    "punishment",
    "account_deletion",
    "legal",
    "medical",
}

SAFETY_EVENT_TYPES = {
    "safeguarding",
    "bullying",
    "harassment",
    "violence",
    "self_harm",
    "abuse",
}

NORMAL_PROGRESS_TYPES = {
    "lesson_completed",
    "practice_passed",
    "login",
    "progress",
}


def _rank(level: str | None) -> int:
    return {None: 0, "low": 1, "medium": 2, "high": 3}.get(level, 0)


def _max_level(*levels: str | None) -> str:
    best = max(levels, key=_rank)
    return best if best in VALID_LEVELS else "low"


def _days_since(iso_value: str | None) -> int | None:
    if not iso_value:
        return None
    try:
        normalized = iso_value.replace("Z", "+00:00")
        then = datetime.fromisoformat(normalized)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0, int((now - then.astimezone(timezone.utc)).total_seconds() // 86400))
    except ValueError:
        return None


def _extract_attempts(details: str) -> int | None:
    match = re.search(r"\b(\d{1,2})\s+(?:times|attempts?|vezes|tentativas?)\b", details, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


@dataclass(frozen=True)
class EventAssessment:
    status: str
    signal_type: str | None
    severity: str
    escalate: bool
    urgency: str
    owner_role: str | None
    reason: str
    suggested_action: str
    risk_score: int
    requires_llm: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_event(
    *,
    event_type: str,
    details: str,
    severity_hint: str | None,
    learner: dict[str, Any] | None,
) -> EventAssessment:
    """Deterministic guardrail policy that runs before any LLM call.

    The LLM may improve wording/recommendations, but it cannot downgrade these
    human-escalation decisions.
    """
    event = event_type.strip().lower()
    hint = severity_hint if severity_hint in VALID_LEVELS else None
    text = details.strip()

    if event in SAFETY_EVENT_TYPES:
        return EventAssessment(
            status="human_escalation",
            signal_type=event,
            severity="high",
            escalate=True,
            urgency="high",
            owner_role="safeguarding_officer",
            reason="Safety-related event requires immediate human judgment.",
            suggested_action="Escalate immediately and preserve the factual event record.",
            risk_score=100,
        )

    if event in CONSEQUENTIAL_EVENT_TYPES:
        return EventAssessment(
            status="human_escalation",
            signal_type=event,
            severity=_max_level(hint, "medium"),
            escalate=True,
            urgency=_max_level(hint, "medium"),
            owner_role="administrator",
            reason="Consequential decision is outside the agent's authority.",
            suggested_action="Route the request to an authorized human without executing it.",
            risk_score=85 if hint == "high" else 75,
        )

    if learner is None:
        return EventAssessment(
            status="human_escalation",
            signal_type="unknown_learner",
            severity="medium",
            escalate=True,
            urgency="medium",
            owner_role="administrator",
            reason="The event references a learner that is not present in the community registry.",
            suggested_action="Verify the learner identity before taking any educational action.",
            risk_score=65,
        )

    if event == "repeated_failure":
        attempts = _extract_attempts(text)
        stored_attempts = int(learner.get("failed_attempts") or 0)
        attempts = max(attempts or 0, stored_attempts)
        severity = "high" if attempts >= 5 else "medium" if attempts >= 3 else _max_level(hint, "low")
        escalate = attempts >= 3 or severity == "high"
        return EventAssessment(
            status="human_escalation" if escalate else "support_signal",
            signal_type="repeated_failure",
            severity=severity,
            escalate=escalate,
            urgency=severity if escalate else "low",
            owner_role="teacher" if escalate else None,
            reason=f"Repeated difficulty detected ({attempts or 'multiple'} attempts).",
            suggested_action=(
                "Teacher should review the learner's misconception and choose the next intervention."
                if escalate
                else "Record the pattern and provide a low-friction hint before escalating."
            ),
            risk_score=80 if severity == "high" else 60 if escalate else 35,
            requires_llm=not escalate,
        )

    if event == "inactivity":
        days = _days_since(learner.get("last_active_at"))
        if days is None:
            severity = _max_level(hint, "low")
        elif days >= 14:
            severity = "high"
        elif days >= 7:
            severity = "medium"
        else:
            severity = _max_level(hint, "low")
        escalate = severity in {"medium", "high"}
        return EventAssessment(
            status="human_escalation" if escalate else "support_signal",
            signal_type="inactivity",
            severity=severity,
            escalate=escalate,
            urgency=severity if escalate else "low",
            owner_role="community_coordinator" if escalate else None,
            reason=f"Learner inactivity detected{f' ({days} days)' if days is not None else ''}.",
            suggested_action=(
                "Human coordinator should check whether the learner needs practical support."
                if escalate
                else "Record the inactivity signal and continue monitoring."
            ),
            risk_score=75 if severity == "high" else 55 if severity == "medium" else 25,
        )

    if event in {"question", "help_request", "confusion"}:
        severity = _max_level(hint, "low")
        escalate = severity == "high" or any(
            phrase in text.lower()
            for phrase in ("still don't understand", "still confused", "cannot continue", "can't continue", "não consigo continuar", "ainda não entendo")
        )
        return EventAssessment(
            status="human_escalation" if escalate else "support_signal",
            signal_type="learner_question",
            severity="high" if escalate and severity == "high" else "medium" if escalate else severity,
            escalate=escalate,
            urgency="high" if severity == "high" else "medium" if escalate else "low",
            owner_role="teacher" if escalate else None,
            reason="Learner requested educational support.",
            suggested_action=(
                "Teacher should review the unresolved question."
                if escalate
                else "Agent may offer a concise contextual explanation and monitor the next attempt."
            ),
            risk_score=60 if escalate else 20,
            requires_llm=True,
        )

    if event in NORMAL_PROGRESS_TYPES:
        return EventAssessment(
            status="normal_progress",
            signal_type=None,
            severity="low",
            escalate=False,
            urgency="low",
            owner_role=None,
            reason="No support or safety signal detected.",
            suggested_action="Acknowledge progress; no human intervention is required.",
            risk_score=5,
        )

    severity = _max_level(hint, "low")
    return EventAssessment(
        status="support_signal",
        signal_type=event or "other",
        severity=severity,
        escalate=severity == "high",
        urgency="high" if severity == "high" else "low",
        owner_role="teacher" if severity == "high" else None,
        reason="Unclassified school event requires contextual interpretation.",
        suggested_action="Record the event and use the Strands agent for contextual interpretation.",
        risk_score=70 if severity == "high" else 30,
        requires_llm=True,
    )

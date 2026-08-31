from __future__ import annotations

from .service import get_learner_context_data, record_support_note_data

MAX_SUPPORT_NOTE_CHARS = 700

# Model-authored support notes are advisory text, but we still enforce a
# deterministic content boundary so the tool cannot be used to smuggle a
# consequential decision into the human workflow.
CONSEQUENTIAL_PHRASES = (
    "confirm payment",
    "approve payment",
    "unlock course",
    "change course access",
    "grant course access",
    "revoke course access",
    "delete account",
    "expel learner",
    "suspend learner",
    "punish learner",
    "disciplinary action",
    "approve enrollment",
    "reject enrollment",
    "medical diagnosis",
    "legal advice",
    "safeguarding decision",
)


def validate_support_note(note: str) -> str:
    """Validate a model-authored advisory note before persistence.

    This is deliberately stricter than the system prompt. Safety does not
    depend on the model following instructions correctly.
    """
    cleaned = " ".join(note.strip().split())
    if not cleaned:
        raise ValueError("note is required")
    if len(cleaned) > MAX_SUPPORT_NOTE_CHARS:
        raise ValueError(f"support note must be <= {MAX_SUPPORT_NOTE_CHARS} characters")

    normalized = cleaned.casefold()
    blocked = [phrase for phrase in CONSEQUENTIAL_PHRASES if phrase in normalized]
    if blocked:
        raise ValueError(
            "support note contains a consequential action; route the case to a human instead"
        )
    return cleaned


def record_safe_support_note_data(
    learner_id: str,
    note: str,
    event_id: str | None = None,
) -> dict:
    context = get_learner_context_data(learner_id)
    if context.get("learner") is None:
        raise ValueError("learner not found")
    cleaned = validate_support_note(note)
    return record_support_note_data(
        learner_id=learner_id,
        note=cleaned,
        event_id=event_id,
        created_by="strands-agent-safe-tool",
    )

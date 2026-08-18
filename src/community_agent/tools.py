from __future__ import annotations

from strands import tool

from .service import (
    get_learner_context_data,
    list_open_followups_data,
    record_support_note_data,
)


@tool
def get_learner_context(learner_id: str) -> dict:
    """Return factual learner context, signals, events, and open follow-ups.

    Args:
        learner_id: Stable learner identifier.
    """
    return get_learner_context_data(learner_id)


@tool
def list_open_followups(urgency: str = "all") -> dict:
    """List open human follow-ups across the school community.

    Args:
        urgency: all, low, medium, or high.
    """
    return list_open_followups_data(urgency)


@tool
def record_support_note(learner_id: str, note: str, event_id: str = "") -> dict:
    """Persist a non-consequential support note drafted by the Strands agent.

    The note is advisory only. It cannot confirm payments, unlock courses,
    punish learners, or replace a human decision.

    Args:
        learner_id: Stable learner identifier.
        note: Concise educational/community support note.
        event_id: Optional event identifier tying the note to an event.
    """
    return record_support_note_data(
        learner_id=learner_id,
        note=note,
        event_id=event_id or None,
    )

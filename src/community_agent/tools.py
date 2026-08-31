from __future__ import annotations

from strands import tool

from .community_context import community_overview_data
from .safety import record_safe_support_note_data
from .service import get_learner_context_data, list_open_followups_data
from .triage import attention_plan_data


@tool
def get_learner_context(learner_id: str) -> dict:
    """Return factual learner context, signals, events, and open follow-ups.

    Args:
        learner_id: Stable learner identifier.
    """
    return get_learner_context_data(learner_id)


@tool
def get_community_overview() -> dict:
    """Return a privacy-safe aggregate view of the whole school community.

    The result contains counts and risk categories only. It intentionally
    excludes learner names, learner IDs, private notes, contacts, PINs, chats,
    payment information, and event details.
    """
    return community_overview_data()


@tool
def get_attention_plan(limit: int = 12) -> dict:
    """Return an explainable deterministic ordering of open human work.

    The score is computed from urgency, active monitoring risk, and waiting time.
    Strands may summarize this ordering but cannot change scores or resolve cases.

    Args:
        limit: Maximum number of open follow-ups to return (1-50).
    """
    return attention_plan_data(limit=limit)


@tool
def list_open_followups(urgency: str = "all") -> dict:
    """List open human follow-ups across the school community.

    Args:
        urgency: all, low, medium, or high.
    """
    return list_open_followups_data(urgency)


@tool
def record_support_note(learner_id: str, note: str, event_id: str = "") -> dict:
    """Persist a bounded, non-consequential support note drafted by Strands.

    A deterministic validator rejects empty, oversized, or consequential
    instructions before anything is stored. The note remains advisory only.

    Args:
        learner_id: Stable learner identifier.
        note: Concise educational/community support note.
        event_id: Optional event identifier tying the note to an event.
    """
    return record_safe_support_note_data(
        learner_id=learner_id,
        note=note,
        event_id=event_id or None,
    )

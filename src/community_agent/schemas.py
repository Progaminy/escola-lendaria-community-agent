from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CommunityEvent(BaseModel):
    learner_id: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    details: str = Field(min_length=1, max_length=4000)
    severity_hint: str | None = Field(default=None, pattern="^(low|medium|high)$")
    source: str = Field(default="school-platform", min_length=1, max_length=100)
    event_id: str | None = Field(default=None, min_length=1, max_length=200)


class EventResult(BaseModel):
    ok: bool
    result: dict[str, Any]


class FollowupResolution(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=1000)

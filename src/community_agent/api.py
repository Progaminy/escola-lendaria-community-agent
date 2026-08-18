from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .agent import process_event
from .db import init_db
from .monitor import (
    autonomous_monitor_loop,
    monitoring_runs_data,
    monitoring_state_data,
    run_community_monitor,
)
from .schemas import CommunityEvent, EventResult, FollowupResolution
from .service import (
    audit_data,
    community_digest_data,
    community_stats_data,
    get_learner_context_data,
    list_open_followups_data,
    recent_decisions_data,
    recent_events_data,
    resolve_followup_data,
    support_notes_data,
)
from .supabase_source import source_status_data, sync_from_supabase
from .ui import DASHBOARD_HTML


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    task = None
    if os.getenv("MONITOR_ENABLED", "true").lower() in {"1", "true", "yes", "on"}:
        task = asyncio.create_task(autonomous_monitor_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Escola Lendária Community Agent",
    version="0.1.0",
    description="Good Neighbor AI agent built with Strands Agents SDK.",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "agent": "escola-lendaria-community-agent",
        "framework": "Strands Agents SDK",
        "human_in_the_loop": True,
        "offline_capable": True,
        "autonomous_monitoring": os.getenv("MONITOR_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
        "monitor_interval_seconds": max(60, int(os.getenv("MONITOR_INTERVAL_SECONDS", "900"))),
        "data_source": source_status_data(),
    }


@app.get("/stats")
def stats() -> dict:
    return community_stats_data()


@app.get("/digest")
def digest() -> dict:
    return community_digest_data()


@app.post("/events", response_model=EventResult)
def receive_event(event: CommunityEvent) -> EventResult:
    try:
        result = process_event(
            learner_id=event.learner_id,
            event_type=event.event_type,
            details=event.details,
            severity_hint=event.severity_hint,
            source=event.source,
            event_id=event.event_id,
        )
        return EventResult(ok=True, result=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/events")
def events(limit: int = 50) -> dict:
    return recent_events_data(limit)


@app.get("/decisions")
def decisions(limit: int = 50) -> dict:
    return recent_decisions_data(limit)


@app.get("/learners/{learner_id}")
def learner(learner_id: str) -> dict:
    context = get_learner_context_data(learner_id)
    if context["learner"] is None:
        raise HTTPException(status_code=404, detail="learner not found")
    return context


@app.get("/support-notes")
def support_notes(learner_id: str | None = None, limit: int = 50) -> dict:
    return support_notes_data(learner_id=learner_id, limit=limit)


@app.get("/followups")
def followups(urgency: str = "all") -> dict:
    try:
        return list_open_followups_data(urgency)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/followups/{followup_id}/resolve")
def resolve_followup(followup_id: int, payload: FollowupResolution) -> dict:
    try:
        result = resolve_followup_data(followup_id, payload.resolution_note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result["reason"])
    return result


@app.get("/audit")
def audit(limit: int = 50) -> dict:
    return audit_data(limit)




@app.get("/source/status")
def source_status() -> dict:
    return source_status_data()


@app.post("/source/supabase/sync")
def source_sync() -> dict:
    try:
        return sync_from_supabase()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Supabase sync failed: {exc}") from exc


@app.post("/monitor/run")
def run_monitor() -> dict:
    return run_community_monitor()


@app.get("/monitor/state")
def monitor_state(status: str = "active") -> dict:
    try:
        return monitoring_state_data(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/monitor/runs")
def monitor_runs(limit: int = 20) -> dict:
    return monitoring_runs_data(limit)

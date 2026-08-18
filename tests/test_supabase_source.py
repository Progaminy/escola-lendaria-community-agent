import os
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.supabase_source import (
    SupabaseSourceConfig,
    derive_learner_record,
    source_status_data,
    sync_learner_rows,
)


def sample_row():
    return {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "name": "Learner One",
        "school_level": "Secondary",
        "last_access_at": "2026-08-12T10:00:00Z",
        "updated_at": "2026-08-12T10:05:00Z",
        "progress": {
            "math-00": {
                "courseId": "math",
                "courseTitle": "Mathematics",
                "lessonTitle": "Numbers",
                "completed": True,
                "completedAt": "2026-08-10T10:00:00Z",
                "wrongAttempts": 4,
            },
            "math-01": {
                "courseId": "math",
                "courseTitle": "Mathematics",
                "lessonTitle": "Addition",
                "completed": False,
                "wrongAttempts": 3,
            },
        },
    }


def test_mapping_counts_only_unresolved_failures():
    record = derive_learner_record(sample_row())
    assert record["course"] == "Mathematics"
    assert record["current_lesson"] == "Addition"
    assert record["failed_attempts"] == 3
    assert record["completed_lessons"] == 1
    assert record["source_system"] == "supabase"
    assert "contact" not in record
    assert "progress_pin" not in record


def test_privacy_minimized_sync(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "source.db")
    init_db()
    result = sync_learner_rows([sample_row()])
    assert result["rows_seen"] == 1
    assert result["privacy"]["contacts_copied"] is False

    with connect() as conn:
        learner = conn.execute(
            "SELECT * FROM learners WHERE learner_id = ?",
            (sample_row()["user_id"],),
        ).fetchone()
        sync_run = conn.execute("SELECT * FROM source_sync_runs ORDER BY id DESC LIMIT 1").fetchone()

    assert learner["display_name"] == "Learner One"
    assert learner["school_level"] == "Secondary"
    assert learner["failed_attempts"] == 3
    assert learner["source_system"] == "supabase"
    assert sync_run["status"] == "completed"


def test_source_status_reports_synced_rows(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "status.db")
    os.environ.pop("SUPABASE_SECRET_KEY", None)
    os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
    init_db()
    sync_learner_rows([sample_row()])
    status = source_status_data()
    assert status["configured"] is False
    assert status["local_synced_learners"] == 1


def test_new_secret_key_is_preferred_over_legacy(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_new")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "legacy-key")
    config = SupabaseSourceConfig.from_env()
    assert config.secret_key == "sb_secret_new"
    assert config.configured is True

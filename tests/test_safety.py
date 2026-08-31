import os
from pathlib import Path

import pytest

from community_agent.db import connect, init_db
from community_agent.safety import record_safe_support_note_data, validate_support_note
from community_agent.service import support_notes_data


def _seed_learner(tmp_path: Path) -> None:
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "safety.db")
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learners (learner_id, display_name, course) VALUES ('L-SAFE', 'Learner Safe', 'Math')"
        )


def test_safe_support_note_is_persisted(tmp_path: Path):
    _seed_learner(tmp_path)
    result = record_safe_support_note_data(
        "L-SAFE",
        "Offer a worked example, then invite the learner to try a similar exercise.",
        "evt-safe",
    )
    assert result["created"] is True
    assert support_notes_data("L-SAFE")["count"] == 1


@pytest.mark.parametrize(
    "note",
    [
        "Confirm payment and unlock the course.",
        "Delete account after the warning.",
        "Expel learner for repeated failures.",
        "Provide legal advice about the dispute.",
    ],
)
def test_consequential_support_note_is_rejected(note: str):
    with pytest.raises(ValueError, match="consequential action"):
        validate_support_note(note)


def test_unknown_learner_cannot_receive_model_note(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "unknown.db")
    init_db()
    with pytest.raises(ValueError, match="learner not found"):
        record_safe_support_note_data("missing", "Offer a worked example.")


def test_oversized_note_is_rejected():
    with pytest.raises(ValueError, match="<= 700"):
        validate_support_note("a" * 701)

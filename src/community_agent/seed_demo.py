from __future__ import annotations

from .db import connect, init_db


def seed() -> None:
    init_db()
    learners = [
        ("L-001", "Amina", "Mathematics", "Fractions 03", "2026-08-13T05:00:00Z", 1),
        ("L-002", "Mussa", "Technical Electricity", "Series Circuits 02", "2026-08-10T12:00:00Z", 3),
        ("L-003", "Celina", "Typing", "Home Row 04", "2026-08-13T04:30:00Z", 0),
    ]
    with connect() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO learners
            (learner_id, display_name, course, current_lesson, last_active_at, failed_attempts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            learners,
        )


if __name__ == "__main__":
    seed()
    print("Demo learners seeded.")

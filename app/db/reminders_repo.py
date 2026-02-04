from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import get_connection
from app.schemas.reminder import Reminder


def create_reminder(user_id: int, task_id: int, time_hhmm: str, next_fire_at: str) -> int:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reminders (
                user_id, task_id, time_hhmm, next_fire_at, is_active, created_at, last_fired_at
            ) VALUES (?, ?, ?, ?, 1, ?, NULL)
            """,
            (user_id, task_id, time_hhmm, next_fire_at, created_at),
        )
        return cursor.lastrowid


def get_due_reminders(now_iso: str) -> list[Reminder]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_id, time_hhmm, next_fire_at, is_active, created_at, last_fired_at
            FROM reminders
            WHERE is_active = 1 AND next_fire_at <= ?
            """,
            (now_iso,),
        )
        rows = cursor.fetchall()
    return [
        Reminder(
            id=row[0],
            user_id=row[1],
            task_id=row[2],
            time_hhmm=row[3],
            next_fire_at=row[4],
            is_active=row[5],
            created_at=row[6],
            last_fired_at=row[7],
        )
        for row in rows
    ]


def mark_fired(reminder_id: int, fired_at_iso: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE reminders
            SET last_fired_at = ?
            WHERE id = ?
            """,
            (fired_at_iso, reminder_id),
        )


def deactivate_by_task(user_id: int, task_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE reminders
            SET is_active = 0
            WHERE user_id = ? AND task_id = ? AND is_active = 1
            """,
            (user_id, task_id),
        )


def delete_reminder(reminder_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,),
        )


def delete_by_task(user_id: int, task_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM reminders WHERE user_id = ? AND task_id = ?",
            (user_id, task_id),
        )


def list_user_reminders(user_id: int) -> list[Reminder]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_id, time_hhmm, next_fire_at, is_active, created_at, last_fired_at
            FROM reminders
            WHERE user_id = ? AND is_active = 1
            ORDER BY next_fire_at
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    return [
        Reminder(
            id=row[0],
            user_id=row[1],
            task_id=row[2],
            time_hhmm=row[3],
            next_fire_at=row[4],
            is_active=row[5],
            created_at=row[6],
            last_fired_at=row[7],
        )
        for row in rows
    ]

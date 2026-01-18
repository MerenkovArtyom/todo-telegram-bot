from datetime import date
from typing import Optional

from app.db.database import get_connection
from app.schemas.task import Task, TaskRecord

def _serialize_due_date(due_date: Optional[date]) -> Optional[str]:
    return due_date.isoformat() if due_date else None


def _deserialize_due_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def add_task(user_id: int, task: Task) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (user_id, text, due_date) VALUES (?, ?, ?)",
            (user_id, task.title, _serialize_due_date(task.due_date)),
        )
        return cursor.lastrowid

def get_tasks(user_id: int) -> list[TaskRecord]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, text, due_date FROM tasks WHERE user_id = ?",
            (user_id,)
        )
        rows = cursor.fetchall()

    tasks: list[TaskRecord] = []
    for task_id, text, due_date in rows:
        task = Task(title=text, due_date=_deserialize_due_date(due_date))
        tasks.append(TaskRecord(id=task_id, task=task))

    return tasks

def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

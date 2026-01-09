from app.db.database import get_connection
from app.schemas.task import Task

def add_task(user_id: int, task: Task):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tasks (user_id, text, due_date) VALUES (?, ?, ?)",
            (user_id, task.title, task.due_date)
        )

def get_tasks(user_id: int):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, text FROM tasks WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchall()

def delete_task(task_id: int):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

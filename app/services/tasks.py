from app.db.tasks_repo import add_task, delete_task, get_tasks
from app.llm.task_extractor import extract_tasks
from app.schemas.task import TaskRecord


def create_tasks(user_id: int, text: str) -> list[TaskRecord]:
    tasks = extract_tasks(text)
    records: list[TaskRecord] = []

    for task in tasks:
        task_id = add_task(user_id, task)
        records.append(TaskRecord(id=task_id, task=task))

    return records


def list_tasks(user_id: int) -> list[TaskRecord]:
    return get_tasks(user_id)


def delete_task_by_index(user_id: int, index: int) -> TaskRecord | None:
    tasks = get_tasks(user_id)
    if not (0 <= index < len(tasks)):
        return None

    record = tasks[index]
    delete_task(record.id)
    return record

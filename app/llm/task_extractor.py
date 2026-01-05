from app.schemas.task import Task
from app.dates.parser import parse_date


def extract_tasks(text: str) -> list[Task]:
    parts = [p.strip() for p in text.split(" и ") if p.strip()]
    tasks: list[Task] = []

    for part in parts:
        due = parse_date(part)
        clean_title = (
            part
            .replace("сегодня", "")
            .replace("завтра", "")
            .replace("послезавтра", "")
            .strip()
        )

        tasks.append(Task(title=clean_title.capitalize(), due_date=due))

    return tasks

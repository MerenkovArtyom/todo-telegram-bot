import re

from app.schemas.task import Task
from app.dates.parser import parse_date


def extract_tasks(text: str) -> list[Task]:
    if not text:
        return []

    parts = [p.strip() for p in re.split(r"\s+и\s+", text) if p.strip()]
    tasks: list[Task] = []

    for part in parts:
        due = parse_date(part)
        clean_title = _strip_date_tokens(part)
        if clean_title:
            tasks.append(Task(title=clean_title.capitalize(), due_date=due))

    return tasks


def _strip_date_tokens(text: str) -> str:
    clean = re.sub(r"\b(сегодня|завтра|послезавтра)\b", "", text, flags=re.IGNORECASE)
    clean = re.sub(r"\b\d{1,2}[./]\d{1,2}\b", "", clean)
    clean = " ".join(clean.split())
    return clean.strip(" ,.;:")

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Task:
    title: str
    due_date: Optional[date] = None


@dataclass(frozen=True)
class TaskRecord:
    id: int
    task: Task

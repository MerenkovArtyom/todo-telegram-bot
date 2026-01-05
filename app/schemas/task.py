from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Task:
    title: str
    due_date: Optional[date]

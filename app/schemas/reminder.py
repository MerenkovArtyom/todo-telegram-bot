from dataclasses import dataclass


@dataclass(frozen=True)
class Reminder:
    id: int
    user_id: int
    task_id: int
    time_hhmm: str
    next_fire_at: str
    is_active: int
    created_at: str
    last_fired_at: str | None

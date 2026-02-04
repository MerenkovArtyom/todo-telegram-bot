from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot

from app.bot import messages
from app.db.reminders_repo import create_reminder, delete_reminder, get_due_reminders, mark_fired
from app.db.tasks_repo import get_task_by_id

DEFAULT_TZ = ZoneInfo("Europe/Moscow")


def compute_next_fire_at(hhmm: str, now: datetime, tz: ZoneInfo) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    local_now = now.astimezone(tz)
    candidate = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= local_now:
        candidate = candidate + timedelta(days=1)
    return candidate.astimezone(timezone.utc)


def schedule_reminder(user_id: int, task_id: int, hhmm: str, tz: ZoneInfo = DEFAULT_TZ) -> int:
    now = datetime.now(timezone.utc)
    next_fire_at = compute_next_fire_at(hhmm, now, tz)
    return create_reminder(
        user_id=user_id,
        task_id=task_id,
        time_hhmm=hhmm,
        next_fire_at=next_fire_at.isoformat(timespec="seconds"),
    )


async def fire_due_reminders(bot: Bot, now: datetime | None = None) -> None:
    now_dt = now or datetime.now(timezone.utc)
    now_iso = now_dt.isoformat(timespec="seconds")
    reminders = get_due_reminders(now_iso)

    for reminder in reminders:
        task_record = get_task_by_id(reminder.user_id, reminder.task_id)
        if not task_record:
            delete_reminder(reminder.id)
            continue

        text = messages.REMIND_NOTIFICATION.format(text=task_record.task.title)
        try:
            await bot.send_message(reminder.user_id, text)
        except Exception:
            # Skip failures to avoid blocking other reminders; keep active to retry.
            continue

        mark_fired(reminder.id, now_iso)
        delete_reminder(reminder.id)


async def reminder_worker(bot: Bot, interval_seconds: int = 45) -> None:
    while True:
        await fire_due_reminders(bot)
        await asyncio.sleep(interval_seconds)

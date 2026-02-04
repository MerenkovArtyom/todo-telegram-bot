import re
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import messages
from app.db.reminders_repo import delete_reminder, list_user_reminders
from app.db.tasks_repo import get_task_by_id
from app.services.reminders import DEFAULT_TZ, schedule_reminder
from app.services.tasks import list_tasks

router = Router()

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


class RemindStates(StatesGroup):
    ChoosingTask = State()
    WaitingTime = State()


def _shorten(text: str, limit: int = 40) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit - 3]}..."


def _format_remaining(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        overdue = abs(total_seconds)
        if overdue < 60:
            return "?????????? ?? <1 ???"
        return f"?????????? ?? {overdue // 60} ???"

    minutes = total_seconds // 60
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts: list[str] = []
    if days:
        parts.append(f"{days} ?")
    if hours:
        parts.append(f"{hours} ?")
    if minutes or not parts:
        parts.append(f"{minutes} ???")
    return " ".join(parts)


def _build_reminders_list(user_id: int):
    reminders = list_user_reminders(user_id)
    if not reminders:
        return messages.REMIND_LIST_EMPTY, None

    now = datetime.now(timezone.utc)
    lines = [messages.REMIND_LIST_HEADER]
    builder = InlineKeyboardBuilder()
    for reminder in reminders:
        task_record = get_task_by_id(user_id, reminder.task_id)
        title = task_record.task.title if task_record else "(?????? ???????)"

        next_dt = datetime.fromisoformat(reminder.next_fire_at)
        if next_dt.tzinfo is None:
            next_dt = next_dt.replace(tzinfo=timezone.utc)
        remaining = _format_remaining(next_dt - now)
        local_dt = next_dt.astimezone(DEFAULT_TZ)

        lines.append(
            f"- {title} ? {reminder.time_hhmm} (????? {remaining}, "
            f"{local_dt.strftime('%Y-%m-%d %H:%M %Z')})"
        )
        builder.add(
            InlineKeyboardButton(
                text=f"?? {reminder.id}",
                callback_data=f"remind_del:{reminder.id}",
            )
        )
    builder.adjust(2)
    return "\n".join(lines), builder.as_markup()


@router.message(Command("remind"))
async def remind_start(message: Message, state: FSMContext):
    tasks = list_tasks(message.from_user.id)
    if not tasks:
        await message.answer(messages.REMIND_NO_TASKS)
        return

    builder = InlineKeyboardBuilder()
    for index, record in enumerate(tasks, start=1):
        title = _shorten(record.task.title)
        builder.add(
            InlineKeyboardButton(
                text=f"{index}. {title}",
                callback_data=f"remind_task:{record.id}",
            )
        )
    builder.adjust(1)

    await state.set_state(RemindStates.ChoosingTask)
    await message.answer(messages.REMIND_CHOOSE_TASK, reply_markup=builder.as_markup())


@router.message(Command("reminders"))
async def reminders_list(message: Message):
    text, markup = _build_reminders_list(message.from_user.id)
    await message.answer(text, reply_markup=markup)


@router.message(F.text == "? ???????????")
async def remind_button(message: Message, state: FSMContext):
    await remind_start(message, state)


@router.callback_query(F.data.startswith("remind_del:"))
async def delete_reminder_callback(callback: CallbackQuery):
    parts = callback.data.split(":", maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer()
        return

    reminder_id = int(parts[1])
    delete_reminder(reminder_id)
    text, markup = _build_reminders_list(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(messages.REMIND_DELETED)


@router.callback_query(F.data.startswith("remind_task:"))
async def remind_choose_task(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer()
        return

    task_id = int(parts[1])
    await state.update_data(task_id=task_id)
    await state.set_state(RemindStates.WaitingTime)
    await callback.message.answer(messages.REMIND_ASK_TIME)
    await callback.answer()


@router.message(RemindStates.WaitingTime)
async def remind_time_input(message: Message, state: FSMContext):
    value = message.text.strip()
    if not TIME_PATTERN.match(value):
        await message.answer(messages.REMIND_BAD_TIME)
        return

    hour, minute = map(int, value.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer(messages.REMIND_BAD_TIME)
        return

    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer(messages.REMIND_BAD_TIME)
        return

    schedule_reminder(message.from_user.id, task_id, value, tz=DEFAULT_TZ)
    await state.clear()
    await message.answer(messages.REMIND_SAVED)

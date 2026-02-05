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
            return "\u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e \u043d\u0430 <1 \u043c\u0438\u043d"
        return f"\u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e \u043d\u0430 {overdue // 60} \u043c\u0438\u043d"

    minutes = total_seconds // 60
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts: list[str] = []
    if days:
        parts.append(f"{days} \u0434")
    if hours:
        parts.append(f"{hours} \u0447")
    if minutes or not parts:
        parts.append(f"{minutes} \u043c\u0438\u043d")
    return " ".join(parts)


def _build_reminders_list(user_id: int):
    reminders = list_user_reminders(user_id)
    if not reminders:
        return messages.REMIND_LIST_EMPTY

    now = datetime.now(timezone.utc)
    lines = [messages.REMIND_LIST_HEADER]
    for i, reminder in enumerate(reminders, start=1):
        task_record = get_task_by_id(user_id, reminder.task_id)
        title = task_record.task.title if task_record else "(\u0437\u0430\u0434\u0430\u0447\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430)"

        next_dt = datetime.fromisoformat(reminder.next_fire_at)
        if next_dt.tzinfo is None:
            next_dt = next_dt.replace(tzinfo=timezone.utc)
        remaining = _format_remaining(next_dt - now)
        local_dt = next_dt.astimezone(DEFAULT_TZ)

        lines.append(
            f"{i}. {title} \u2014 {reminder.time_hhmm} (\u0447\u0435\u0440\u0435\u0437 {remaining}, "
            f"{local_dt.strftime('%Y-%m-%d %H:%M %Z')})"
        )
    return "\n".join(lines)


def _delete_reminder_by_index(user_id: int, index: int) -> bool:
    reminders = list_user_reminders(user_id)
    if not (0 <= index < len(reminders)):
        return False

    delete_reminder(reminders[index].id)
    return True


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
    text = _build_reminders_list(message.from_user.id)
    await message.answer(text)


@router.message(Command("unremind"))
async def unremind_handler(message: Message):
    parts = message.text.split()
    reminders = list_user_reminders(message.from_user.id)
    if not reminders:
        await message.answer(messages.REMIND_LIST_EMPTY)
        return

    if len(parts) != 2 or not parts[1].isdigit():
        builder = InlineKeyboardBuilder()
        for i in range(len(reminders)):
            builder.add(
                InlineKeyboardButton(
                    text=str(i + 1),
                    callback_data=f"unremind:{i+1}",
                )
            )
        builder.adjust(3)
        await message.answer(
            "\u0412\u044b\u0431\u0435\u0440\u0438 \u043d\u043e\u043c\u0435\u0440 \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0434\u043b\u044f \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u044f:",
            reply_markup=builder.as_markup(),
        )
        return

    index = int(parts[1]) - 1
    deleted = _delete_reminder_by_index(message.from_user.id, index)
    if not deleted:
        await message.answer(
            "\u041d\u0435\u0442 \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0441 \u0442\u0430\u043a\u0438\u043c \u043d\u043e\u043c\u0435\u0440\u043e\u043c."
        )
        return

    await message.answer(messages.REMIND_DELETED)


@router.message(F.text == "\u23f0 \u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435")
async def remind_button(message: Message, state: FSMContext):
    await remind_start(message, state)


@router.callback_query(F.data.startswith("unremind:"))
async def unremind_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer()
        return

    index = int(parts[1]) - 1
    deleted = _delete_reminder_by_index(callback.from_user.id, index)
    if not deleted:
        await callback.answer(
            "\u041d\u0435\u0442 \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0441 \u0442\u0430\u043a\u0438\u043c \u043d\u043e\u043c\u0435\u0440\u043e\u043c.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(messages.REMIND_DELETED)
    await callback.answer()


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

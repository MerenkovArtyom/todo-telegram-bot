from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import messages
from app.services.tasks import create_tasks, delete_task_by_index, list_tasks

router = Router()


@router.message(~Command("add", "start", "list", "done"))
async def handle_text(message: Message):
    tasks = create_tasks(message.from_user.id, message.text)

    if not tasks:
        await message.answer(messages.NO_TASKS_FOUND)
        return

    await message.answer(messages.TASKS_ADDED)


@router.message(Command("add"))
async def add_task_handler(message: types.Message):
    text = message.text.removeprefix("/add").strip()
    if not text:
        await message.answer(messages.ADD_USAGE)
        return

    tasks = create_tasks(message.from_user.id, text)
    if not tasks:
        await message.answer(messages.NO_TASKS_FOUND)
        return

    await message.answer(messages.TASKS_ADDED)


@router.message(Command("list"))
async def list_tasks_handler(message: types.Message):
    tasks = list_tasks(message.from_user.id)

    if not tasks:
        await message.answer(messages.NO_TASKS)
        return

    result = messages.LIST_HEADER
    for i, record in enumerate(tasks, start=1):
        line = record.task.title
        if record.task.due_date:
            line += f" — до {record.task.due_date.isoformat()}"
        result += f"{i}. {line}\n"

    await message.answer(result)


@router.message(Command("done"))
async def done_task_handler(message: types.Message):
    parts = message.text.split()
    tasks = list_tasks(message.from_user.id)

    if not tasks:
        await message.answer(messages.NO_TASKS)
        return

    if len(parts) != 2 or not parts[1].isdigit():
        builder = InlineKeyboardBuilder()
        for i in range(len(tasks)):
            builder.add(
                InlineKeyboardButton(
                    text=str(i + 1),
                    callback_data=f"done:{i+1}",
                )
            )
        builder.adjust(3)
        await message.answer(messages.DONE_PROMPT, reply_markup=builder.as_markup())
        return

    index = int(parts[1]) - 1
    record = delete_task_by_index(message.from_user.id, index)
    if not record:
        await message.answer(messages.INVALID_INDEX)
        return

    await message.answer(messages.DONE_CONFIRMED)


@router.callback_query(F.data.startswith("done:"))
async def process_done(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        index = int(parts[1]) - 1
        record = delete_task_by_index(callback.from_user.id, index)
        if not record:
            await callback.answer(messages.INVALID_INDEX, show_alert=True)
            return

        await callback.message.edit_text(messages.DONE_CONFIRMED)
        await callback.answer()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="/list"),
            types.KeyboardButton(text="/done"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Введите задачу",
    )

    await message.answer(messages.START_TEXT, reply_markup=keyboard)

from aiogram import Router
from aiogram.types import Message

from app.llm.task_extractor import extract_tasks

router = Router()


@router.message()
async def handle_text(message: Message):
    tasks = extract_tasks(message.text)

    if not tasks:
        await message.answer("Не смог найти задачи 🤷‍♂️")
        return

    reply = "📝 Задачи:\n"
    for i, task in enumerate(tasks, 1):
        date_str = task.due_date.isoformat() if task.due_date else "без даты"
        reply += f"{i}. {task.title} — {date_str}\n"

    await message.answer(reply)

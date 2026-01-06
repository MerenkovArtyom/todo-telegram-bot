from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from app.llm.task_extractor import extract_tasks
from app.db.tasks_repo import add_task, get_tasks, delete_task


router = Router()


@router.message() 
async def handle_text(message: Message):
    tasks = extract_tasks(message.text)

    if not tasks:
        await message.answer("Не смог найти задачи 🤷‍♂️")
        return

    for text in tasks:
        add_task(message.from_user.id, text)

    await message.answer("✅ Задачи добавлены")


@router.message(Command("add"))
async def add_task_handler(message: types.Message):
    text = message.text.removeprefix("/add").strip()
    if not text:
        await message.answer("❌ Используй: /add текст задачи")
        return

    add_task(message.from_user.id, text)
    await message.answer("✅ Задача добавлена")


@router.message(Command("list"))
async def list_tasks_handler(message: types.Message):
    tasks = get_tasks(message.from_user.id)

    if not tasks:
        await message.answer("📭 Список задач пуст")
        return

    result = "📋 Ваши задачи:\n\n"
    for task_id, text in tasks:
        result += f"{task_id}. {text}\n"

    await message.answer(result)


@router.message(Command("done"))
async def done_task_handler(message: types.Message):
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❌ Используй: /done 2")
        return

    task_id = int(parts[1])
    delete_task(task_id)

    await message.answer("🗑 Задача выполнена и удалена")
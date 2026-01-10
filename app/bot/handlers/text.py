from aiogram import Router, types, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.llm.task_extractor import extract_tasks
from app.db.tasks_repo import add_task, get_tasks, delete_task
from app.dates.parser import parse_date


router = Router()


@router.message(~Command('add', 'start', 'list', 'done')) 
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

    add_task(message.from_user.id, text) #TODO добавить добавление даты
    await message.answer("✅ Задача добавлена")


@router.message(Command("list"))
async def list_tasks_handler(message: types.Message):
    tasks = get_tasks(message.from_user.id)

    if not tasks:
        await message.answer("📭 Список задач пуст")
        return

    result = "📋 Ваши задачи:\n\n"
    for i, (_, text) in enumerate(tasks, start=1):
        result += f"{i}. {text}\n"

    await message.answer(result)


@router.message(Command("done"))
async def done_task_handler(message: types.Message):
    parts = message.text.split()

    tasks = get_tasks(message.from_user.id)

    if not tasks:
        await message.answer("📭 Список задач пуст")
        return

    if len(parts) != 2 or not parts[1].isdigit():
        builder = InlineKeyboardBuilder()

        for i in range(len(tasks)):
            builder.add(InlineKeyboardButton(
                text=str(i+1),
                callback_data=f"done:{i+1}"
            ))
        builder.adjust(3)
        await message.answer("Выберите задачу:", reply_markup=builder.as_markup())

        return
    
    index = int(parts[1]) - 1
    if not (0 <= index < len(tasks)):
        await message.answer("❌ Нет задачи с таким номером")
        return

    task_id = tasks[index][0]
    delete_task(task_id)
    await message.answer("🗑 Задача выполнена и удалена")


@router.callback_query(F.data.startswith("done:"))
async def process_done(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        index = int(parts[1]) - 1

        tasks = get_tasks(callback.from_user.id)
        if not (0 <= index < len(tasks)):
            await callback.answer("❌ Нет задачи с таким номером", show_alert=True)
            return

        task_id = tasks[index][0]
        delete_task(task_id)

        await callback.message.edit_text("🗑 Задача выполнена и удалена")
        await callback.answer()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="/list"),
            types.KeyboardButton(text="/done")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Введите задачу"
    )

    await message.answer("Привет!\nДоступные команды:\n"
                         "/list - список задач\n"
                         "/done <id_задачи> - удалить задачу",
                         reply_markup=keyboard)

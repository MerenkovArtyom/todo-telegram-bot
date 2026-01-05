from aiogram import Router, F
from aiogram.types import Message
from pathlib import Path
import uuid

from app.asr.whisper_asr import transcribe
from app.llm.task_extractor import extract_tasks

router = Router()

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.message(F.voice)
async def handle_voice(message: Message):
    # 1. Скачать голосовое
    file = await message.bot.get_file(message.voice.file_id)

    filename = f"{uuid.uuid4()}.ogg"
    ogg_path = AUDIO_DIR / filename

    await message.bot.download_file(file.file_path, destination=ogg_path)

    await message.answer("🎧 Распознаю голос...")

    # 2. Whisper → текст
    text = transcribe(ogg_path)

    if not text:
        await message.answer("Не удалось распознать речь 😕")
        return

    # 3. Текст → задачи
    tasks = extract_tasks(text)

    if not tasks:
        await message.answer(f"📝 Я услышал:\n{text}\n\nНо не смог выделить задачи 🤷‍♂️")
        return

    # 4. Ответ пользователю
    reply = "📝 Задачи:\n"
    for i, task in enumerate(tasks, 1):
        date_str = task.due_date.isoformat() if task.due_date else "без даты"
        reply += f"{i}. {task.title} — {date_str}\n"

    await message.answer(reply)

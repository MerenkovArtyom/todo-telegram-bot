from aiogram import Router, F
from aiogram.types import Message
from pathlib import Path
import uuid

from app.asr.whisper_asr import transcribe

router = Router()
AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.message(F.voice)
async def handle_voice(message: Message):
    file = await message.bot.get_file(message.voice.file_id)

    filename = f"{uuid.uuid4()}.ogg"
    ogg_path = AUDIO_DIR / filename

    await message.bot.download_file(file.file_path, destination=ogg_path)

    await message.answer("🎧 Распознаю голос...")

    text = transcribe(ogg_path)

    await message.answer(f"📝 Я услышал:\n{text}")

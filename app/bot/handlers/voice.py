from aiogram import Router, F
from aiogram.types import Message
from pathlib import Path
import uuid

router = Router()

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.message(F.voice)
async def handle_voice(message: Message):
    voice = message.voice

    file = await message.bot.get_file(voice.file_id)

    filename = f"{uuid.uuid4()}.ogg"
    file_path = AUDIO_DIR / filename

    await message.bot.download_file(file.file_path, destination=file_path)

    await message.answer("🎙 Голосовое сообщение сохранено")

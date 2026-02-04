import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.handlers.voice import router as voice_router
from app.bot.handlers.reminders import router as reminders_router
from app.bot.handlers.text import router as text_router
from app.config import BOT_TOKEN
from app.services.reminders import reminder_worker


async def register_handlers():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(voice_router)
    dp.include_router(reminders_router)
    dp.include_router(text_router)

    asyncio.create_task(reminder_worker(bot))
    await dp.start_polling(bot)

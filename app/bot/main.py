import asyncio
from aiogram import Bot, Dispatcher
from app.bot.handlers.voice import router as voice_router
from app.config import BOT_TOKEN
from app.bot.handlers.text import router as text_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(voice_router)
    dp.include_router(text_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

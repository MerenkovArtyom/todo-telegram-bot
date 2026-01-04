import asyncio
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def echo(message):
        await message.answer(f"Ты написал: {message.text}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

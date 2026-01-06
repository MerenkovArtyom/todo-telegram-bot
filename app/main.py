import asyncio
from app.db.database import init_db
from app.bot.main import register_handlers

async def main():
    init_db()
    await register_handlers()

if __name__ == "__main__":
    asyncio.run(main())

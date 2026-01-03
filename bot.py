import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import movies, start

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)   # ← ВАЖНО
    dp.include_router(movies.router)
    
    print ("uraaaaaa")

    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())



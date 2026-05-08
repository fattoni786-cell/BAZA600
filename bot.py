import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from utils.anti_spam import AntiSpamMiddleware
from utils.backup import create_daily_backup
from utils.error_middleware import ErrorLoggingMiddleware
from utils.init_db import init_all
from utils.security_middleware import SecurityMiddleware
from utils.user_middleware import UserMiddleware

from handlers import (
    start,
    security,
    search,
    premium,
    community,
    anime,
    movies,
    games,
    series,
    books,
    file_id_tool,
    admin_add_content,
    admin_stats,
    favorites,
    toggle_favorite,
    rating,
)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured. Set it in .env or server environment.")

    init_all()
    backup_path = create_daily_backup()

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(ErrorLoggingMiddleware())
    dp.callback_query.middleware(ErrorLoggingMiddleware())
    dp.message.middleware(SecurityMiddleware())
    dp.callback_query.middleware(SecurityMiddleware())
    dp.message.middleware(AntiSpamMiddleware())
    dp.callback_query.middleware(AntiSpamMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.include_router(start.router)
    dp.include_router(security.router)
    dp.include_router(search.router)
    dp.include_router(premium.router)
    dp.include_router(community.router)

    dp.include_router(favorites.router)
    dp.include_router(toggle_favorite.router)
    dp.include_router(rating.router)

    dp.include_router(anime.router)
    dp.include_router(movies.router)
    dp.include_router(games.router)
    dp.include_router(series.router)
    dp.include_router(books.router)

    dp.include_router(admin_stats.router)
    dp.include_router(file_id_tool.router)
    dp.include_router(admin_add_content.router)

    print("bot started")
    if backup_path:
        print(f"daily backup ready: {backup_path}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

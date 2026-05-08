from config_baze.admins import ADMINS


async def notify_admins(bot, text: str):
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass

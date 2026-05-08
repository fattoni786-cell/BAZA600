from html import escape

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config_baze.admins import ADMINS
from keyboards.menu import bottom_nav_kb
from utils.db import block_user, delete_user_data, get_blocked_users, unblock_user

router = Router()


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in ADMINS)


@router.message(Command("privacy"))
async def privacy(message: Message):
    await message.answer(
        (
            "<b>Приватность БАЗЫ №600</b>\n\n"
            "Бот хранит минимум данных, чтобы работали избранное, реакции, premium и персональные лимиты:\n"
            "• Telegram ID\n"
            "• premium-статус и историю оплат\n"
            "• избранное, реакции и недавно показанный контент\n"
            "• заявки, если ты сам отправляешь контент в базу\n\n"
            "Бот не хранит переписки вне сценариев подбора и не продаёт пользовательские данные.\n\n"
            "Удалить свои данные можно командой:\n"
            "<code>/delete_me confirm</code>"
        ),
        parse_mode="HTML",
        reply_markup=bottom_nav_kb(),
    )


@router.message(Command("delete_me"))
async def delete_me(message: Message, command: CommandObject):
    if not message.from_user:
        return

    if command.args != "confirm":
        await message.answer(
            (
                "Это удалит избранное, реакции, историю показов, настройки меню и premium-записи из базы бота.\n\n"
                "Если уверен, отправь:\n"
                "<code>/delete_me confirm</code>"
            ),
            parse_mode="HTML",
        )
        return

    delete_user_data(message.from_user.id)
    await message.answer(
        "Данные удалены. Если напишешь боту снова, будет создан свежий профиль.",
        reply_markup=bottom_nav_kb(),
    )


@router.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject):
    if not _is_admin(message):
        return

    if not command.args:
        await message.answer("Используй: /ban <user_id> [причина]")
        return

    parts = command.args.split(maxsplit=1)
    if not parts[0].isdigit():
        await message.answer("User ID должен быть числом.")
        return

    user_id = int(parts[0])
    reason = parts[1] if len(parts) > 1 else "Без причины"
    block_user(user_id, reason=reason, blocked_by=message.from_user.id)
    await message.answer(f"Пользователь {user_id} заблокирован.\nПричина: {escape(reason)}")


@router.message(Command("unban"))
async def unban_user(message: Message, command: CommandObject):
    if not _is_admin(message):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /unban <user_id>")
        return

    user_id = int(command.args)
    unblock_user(user_id)
    await message.answer(f"Пользователь {user_id} разблокирован.")


@router.message(Command("blocked"))
async def blocked_users(message: Message):
    if not _is_admin(message):
        return

    rows = get_blocked_users(limit=50)
    if not rows:
        await message.answer("Блок-лист пуст.")
        return

    lines = ["<b>Заблокированные пользователи</b>"]
    for user_id, reason, blocked_by, created_at in rows:
        lines.append(
            f"{user_id} • {escape(reason or '-')}"
            f"\nby: {blocked_by or '-'} • {created_at}"
        )

    await message.answer("\n\n".join(lines), parse_mode="HTML")

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def replace_screen(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    """
    Replace the current inline screen when possible.
    Falls back to a new message if Telegram cannot edit the old one.
    """
    try:
        await callback.answer()
    except Exception:
        pass

    message = callback.message
    if message is None:
        return

    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return
    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            return
    except Exception:
        pass

    try:
        await message.edit_caption(
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return
    except Exception:
        pass

    try:
        await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except Exception:
        pass


async def replace_with_new_screen(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    """
    Open a clean text screen by deleting the previous bot message first.
    Useful when the previous screen can be a media card: editing its caption
    would leave the old gif/video hanging above the new text.
    """
    try:
        await callback.answer()
    except Exception:
        pass

    message = callback.message
    if message is None:
        return

    try:
        await message.delete()
    except Exception:
        pass

    try:
        return await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except Exception:
        return None


async def delete_tracked_message(state, bot, chat_id: int, state_key: str):
    data = await state.get_data()
    message_id = data.get(state_key)

    if not message_id:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

    await state.update_data(**{state_key: None})


async def track_active_screen(state, message, state_key: str = "last_active_screen_message_id"):
    if message is None:
        return

    message_id = getattr(message, "message_id", None)
    if message_id:
        await state.update_data(**{state_key: message_id})


async def delete_active_screen(state, bot, chat_id: int):
    await delete_tracked_message(state, bot, chat_id, "last_active_screen_message_id")

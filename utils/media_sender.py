from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, Message

from utils.db import get_rating_summary


def build_caption(
    content_type: str,
    item: dict,
    extra_text: str | None = None,
    context_note: str | None = None,
) -> str:
    title = item.get("title", "")
    desc = item.get("desc", "")

    rating = get_rating_summary(
        content_type=content_type,
        content_id=title,
    )

    rating_parts = [
        f"🔥 {rating['likes']}",
        f"❄️ {rating['dislikes']}",
    ]
    if rating.get("mixed"):
        rating_parts.append(f"🤔 {rating['mixed']}")
    if rating.get("base_approves"):
        rating_parts.append(f"🎓 {rating['base_approves']}")

    rating_line = "\n\n" + "   ".join(rating_parts)
    extra_block = (
        f"\n\n────────────\n<u>Почему?</u>\n{extra_text}"
        if extra_text
        else ""
    )
    context_block = f"\n\n{context_note}" if context_note else ""

    return f"<b>{title}</b>{context_block}\n\n{desc}{extra_block}{rating_line}".strip()


async def send_media(
    callback: CallbackQuery | Message,
    item: dict,
    content_type: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    extra_text: str | None = None,
    context_note: str | None = None,
):
    target_message = callback.message if isinstance(callback, CallbackQuery) else callback
    caption = build_caption(
        content_type,
        item,
        extra_text=extra_text,
        context_note=context_note,
    )
    media = item.get("media")

    if not isinstance(media, dict):
        return await target_message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    media_type = media.get("type")
    file_id = media.get("file_id")
    file_path = media.get("file_path")
    media_source = file_id or (FSInputFile(file_path) if file_path else None)

    if not media_type or not media_source:
        return await target_message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    if media_type == "photo":
        return await target_message.answer_photo(
            photo=media_source,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    elif media_type == "animation":
        return await target_message.answer_animation(
            animation=media_source,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    elif media_type == "video":
        return await target_message.answer_video(
            video=media_source,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        return await target_message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

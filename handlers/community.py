from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config_baze.admins import ADMINS
from keyboards.common.community import (
    CONTENT_TYPE_LABELS,
    community_hub_keyboard,
    community_type_keyboard,
)
from states.community import CommunitySuggestionFlow
from utils.db import (
    create_admin_content_draft,
    create_content_suggestion,
    create_premium_reward_request,
    count_recent_content_suggestions,
    get_admin_content_drafts,
    get_contributor_overview,
    get_content_suggestion,
    get_content_suggestions_by_status,
    get_premium_reward_request,
    get_premium_reward_requests_by_status,
    get_reserved_reward_slots,
    get_user_suggestion_stats,
    has_pending_premium_reward_request,
    update_content_suggestion_status,
    update_premium_reward_request_status,
)
from utils.text_limits import (
    MAX_SUGGESTION_DESCRIPTION_LENGTH,
    MAX_SUGGESTION_TITLE_LENGTH,
    MAX_SUGGESTION_VIBE_LENGTH,
    clean_user_text,
    is_too_long,
    length_error_text,
)
from utils.ui import replace_screen
from utils.users import activate_premium

router = Router()

APPROVED_SUGGESTIONS_FOR_PREMIUM = 6
PREMIUM_REWARD_DAYS = 30
DAILY_SUGGESTION_LIMIT = 3


def get_available_reward_batches(user_id: int) -> tuple[int, int, int]:
    stats = get_user_suggestion_stats(user_id)
    approved = stats["approved"]
    reserved = get_reserved_reward_slots(user_id)
    available = max(0, approved - reserved)
    return approved, reserved, available // APPROVED_SUGGESTIONS_FOR_PREMIUM


def community_hub_text(user: dict) -> str:
    stats = get_user_suggestion_stats(user["telegram_id"])
    total_suggestions = stats["pending"] + stats["approved"] + stats["rejected"]
    approved, reserved, available_batches = get_available_reward_batches(user["telegram_id"])
    free_for_reward = max(0, approved - reserved)
    progress = free_for_reward % APPROVED_SUGGESTIONS_FOR_PREMIUM

    lines = [
        "🫶 <b>Вклад в базу</b>",
        "",
        "Вместе расширяем грани возможного.",
    ]

    if total_suggestions == 0:
        return "\n".join(lines)

    lines.extend([
        "",
        f"⏳ На проверке: <b>{stats['pending']}</b>",
        f"✅ Одобрено: <b>{approved}</b>",
        f"❌ Отклонено: <b>{stats['rejected']}</b>",
        "",
        f"🎁 Прогресс до reward-Premium: <b>{progress}/{APPROVED_SUGGESTIONS_FOR_PREMIUM}</b>",
    ])

    if available_batches > 0:
        lines.extend(
            [
                "",
                f"У тебя уже есть право запросить Premium: <b>{available_batches}</b> раз(а).",
            ]
        )
    else:
        remaining = APPROVED_SUGGESTIONS_FOR_PREMIUM - progress
        lines.append(f"Нужно ещё <b>{remaining}</b> одобренных вкладов.")

    return "\n".join(lines)


def community_content_type_name(content_type: str) -> str:
    return CONTENT_TYPE_LABELS.get(content_type, content_type)


def is_admin_user(user_id: int) -> bool:
    return user_id in ADMINS


@router.message(F.text.in_({"🫶 Внести", "🫶 Внести в базу"}))
async def community_hub_button(message: Message, user: dict, state: FSMContext):
    await state.clear()
    await message.answer(
        community_hub_text(user),
        reply_markup=community_hub_keyboard(is_admin=is_admin_user(user["telegram_id"])),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "community_hub")
async def community_hub(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.clear()
    await replace_screen(
        callback,
        text=community_hub_text(user),
        reply_markup=community_hub_keyboard(is_admin=is_admin_user(user["telegram_id"])),
    )


@router.callback_query(F.data == "community_suggest_start")
async def community_suggest_start(callback: CallbackQuery, user: dict, state: FSMContext):
    if count_recent_content_suggestions(user["telegram_id"], hours=24) >= DAILY_SUGGESTION_LIMIT:
        await callback.answer(
            "На сегодня хватит заявок. Завтра можно будет отправить ещё.",
            show_alert=True,
        )
        return

    await state.clear()
    await replace_screen(
        callback,
        text=(
            "🫶 <b>Предложить контент</b>\n\n"
            "Выбери тип контента, который хочешь предложить."
        ),
        reply_markup=community_type_keyboard(),
    )


@router.callback_query(F.data.startswith("community_type:"))
async def community_choose_type(callback: CallbackQuery, state: FSMContext):
    content_type = callback.data.split(":", 1)[1]

    await state.set_state(CommunitySuggestionFlow.waiting_title)
    await state.update_data(community_content_type=content_type)

    await replace_screen(
        callback,
        text=(
            f"🫶 <b>{community_content_type_name(content_type)}</b>\n\n"
            "Пришли <b>название</b>.\n"
            "Если передумаешь, можешь в любой момент нажать /start."
        ),
    )


@router.message(CommunitySuggestionFlow.waiting_title)
async def community_receive_title(message: Message, state: FSMContext):
    title = clean_user_text(message.text)
    if not title:
        await message.answer("Нужно прислать именно название текстом.")
        return
    if is_too_long(title, MAX_SUGGESTION_TITLE_LENGTH):
        await message.answer(length_error_text(MAX_SUGGESTION_TITLE_LENGTH))
        return

    await state.update_data(community_title=title)
    await state.set_state(CommunitySuggestionFlow.waiting_description)
    await message.answer(
        "📝 Теперь пришли <b>описание</b>.\n"
        "Коротко расскажи, что это за контент и чем он хорош.",
        parse_mode="HTML",
    )


@router.message(CommunitySuggestionFlow.waiting_description)
async def community_receive_description(message: Message, state: FSMContext):
    description = clean_user_text(message.text)
    if not description:
        await message.answer("Нужно прислать описание текстом.")
        return
    if is_too_long(description, MAX_SUGGESTION_DESCRIPTION_LENGTH):
        await message.answer(length_error_text(MAX_SUGGESTION_DESCRIPTION_LENGTH))
        return

    await state.update_data(community_description=description)
    await state.set_state(CommunitySuggestionFlow.waiting_vibe)
    await message.answer(
        "🌫 Теперь напиши, <b>под какой вайб</b> это заходит.\n"
        "Например: `одинокий ночной просмотр`, `мягкая меланхолия`, `залипнуть на выходных`.",
        parse_mode="HTML",
    )


@router.message(CommunitySuggestionFlow.waiting_vibe)
async def community_receive_vibe(message: Message, user: dict, state: FSMContext):
    vibe_text = clean_user_text(message.text)
    if not vibe_text:
        await message.answer("Нужно прислать вайб текстом.")
        return
    if is_too_long(vibe_text, MAX_SUGGESTION_VIBE_LENGTH):
        await message.answer(length_error_text(MAX_SUGGESTION_VIBE_LENGTH))
        return

    data = await state.get_data()
    content_type = data.get("community_content_type")
    title = data.get("community_title")
    description = data.get("community_description")

    if count_recent_content_suggestions(user["telegram_id"], hours=24) >= DAILY_SUGGESTION_LIMIT:
        await state.clear()
        await message.answer(
            "Лимит заявок на сегодня закончился. Завтра можно будет отправить ещё.",
            reply_markup=community_hub_keyboard(is_admin=is_admin_user(user["telegram_id"])),
        )
        return

    create_content_suggestion(
        user_id=user["telegram_id"],
        username=message.from_user.username,
        content_type=content_type,
        title=title,
        description=description,
        vibe_text=vibe_text,
    )

    await state.clear()

    await message.answer(
        (
            "✅ <b>Предложение сохранено</b>\n\n"
            f"Тип: <b>{community_content_type_name(content_type)}</b>\n"
            f"Название: <b>{escape(title)}</b>\n"
            f"Вайб: <b>{escape(vibe_text)}</b>\n\n"
            "Когда я одобрю контент, он пойдёт в копилку reward-Premium."
        ),
        parse_mode="HTML",
        reply_markup=community_hub_keyboard(is_admin=is_admin_user(user["telegram_id"])),
    )


@router.callback_query(F.data == "community_request_premium")
async def community_request_premium(callback: CallbackQuery, user: dict):
    approved, reserved, available_batches = get_available_reward_batches(user["telegram_id"])

    if has_pending_premium_reward_request(user["telegram_id"]):
        await callback.answer(
            "У тебя уже есть активный запрос на reward-Premium",
            show_alert=True,
        )
        return

    if available_batches <= 0:
        free_for_reward = max(0, approved - reserved)
        progress = free_for_reward % APPROVED_SUGGESTIONS_FOR_PREMIUM
        remaining = APPROVED_SUGGESTIONS_FOR_PREMIUM - progress
        await callback.answer(
            f"Пока рано: нужно ещё {remaining} одобренных вкладов",
            show_alert=True,
        )
        return

    create_premium_reward_request(
        user_id=user["telegram_id"],
        approved_count_snapshot=approved,
    )

    await replace_screen(
        callback,
        text=(
            "🎁 <b>Запрос на Premium отправлен</b>\n\n"
            f"После подтверждения тебе начислится <b>{PREMIUM_REWARD_DAYS} дней Premium</b>."
        ),
        reply_markup=community_hub_keyboard(is_admin=is_admin_user(user["telegram_id"])),
    )


@router.callback_query(F.data == "community_admin_drafts")
async def community_admin_drafts(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    rows = get_admin_content_drafts(status="pending", limit=20)
    text = "<b>Черновики</b>\n\n" + escape(_format_drafts(rows))

    await replace_screen(
        callback,
        text=text,
        reply_markup=_drafts_keyboard(rows),
    )


@router.callback_query(F.data == "community_admin_suggestions")
async def community_admin_suggestions(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    rows = get_content_suggestions_by_status("pending", limit=20)
    text = "<b>Заявки на проверке</b>\n\n" + escape(_format_suggestions(rows))

    await replace_screen(
        callback,
        text=text,
        reply_markup=_suggestions_keyboard(rows),
    )


@router.callback_query(F.data.startswith("community_approve_suggestion:"))
async def community_approve_suggestion(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    suggestion_id = int(callback.data.split(":", 1)[1])
    suggestion = get_content_suggestion(suggestion_id)

    if not suggestion:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if suggestion[7] != "pending":
        await callback.answer("Эта заявка уже обработана", show_alert=True)
        return

    update_content_suggestion_status(
        suggestion_id=suggestion_id,
        status="approved",
        reviewed_by=user["telegram_id"],
    )

    draft_id = create_admin_content_draft(
        suggestion_id=suggestion[0],
        suggested_by_user_id=suggestion[1],
        content_type=suggestion[3],
        title=suggestion[4],
        description=suggestion[5],
        vibe_text=suggestion[6],
    )

    stats = get_user_suggestion_stats(suggestion[1])

    try:
        await callback.message.bot.send_message(
            suggestion[1],
            (
                "✅ Твой контент одобрен и попал в копилку вкладов.\n\n"
                f"Всего одобрено: {stats['approved']}."
            ),
        )
    except Exception:
        pass

    await replace_screen(
        callback,
        text=(
            f"✅ <b>Заявка #{suggestion_id} одобрена</b>\n\n"
            f"Черновик создан: <b>#{draft_id}</b>\n"
            f"У автора теперь <b>{stats['approved']}</b> одобренных вкладов."
        ),
        reply_markup=_approval_result_keyboard(draft_id),
    )


@router.callback_query(F.data.startswith("community_reject_suggestion:"))
async def community_reject_suggestion(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    suggestion_id = int(callback.data.split(":", 1)[1])
    suggestion = get_content_suggestion(suggestion_id)

    if not suggestion:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if suggestion[7] != "pending":
        await callback.answer("Эта заявка уже обработана", show_alert=True)
        return

    update_content_suggestion_status(
        suggestion_id=suggestion_id,
        status="rejected",
        reviewed_by=user["telegram_id"],
    )

    try:
        await callback.message.bot.send_message(
            suggestion[1],
            "❌ Этот контент я пока не одобрил для базы, но можешь прислать другой вариант.",
        )
    except Exception:
        pass

    await replace_screen(
        callback,
        text=f"❌ <b>Заявка #{suggestion_id} отклонена</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 К заявкам",
                        callback_data="community_admin_suggestions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 В раздел вкладов",
                        callback_data="community_hub",
                    )
                ],
            ]
        ),
    )


def _admin_only(message: Message) -> bool:
    return is_admin_user(message.from_user.id)


def _format_suggestions(rows) -> str:
    if not rows:
        return "Пока пусто."

    blocks = []
    for suggestion_id, user_id, username, content_type, title, description, vibe_text, status, created_at in rows:
        username_part = f"@{username}" if username else "без username"
        blocks.append(
            "\n".join(
                [
                    f"#{suggestion_id} • {community_content_type_name(content_type)}",
                    f"User: {user_id} ({username_part})",
                    f"Title: {title}",
                    f"Vibe: {vibe_text}",
                    f"Desc: {description}",
                    f"Date: {created_at}",
                ]
            )
        )

    return "\n\n".join(blocks)


def _format_drafts(rows) -> str:
    if not rows:
        return "Пока пусто."

    blocks = []
    for draft_id, suggestion_id, suggested_by_user_id, content_type, title, description, vibe_text, status, created_at in rows:
        blocks.append(
            "\n".join(
                [
                    f"Draft #{draft_id} • {community_content_type_name(content_type)}",
                    f"From suggestion: {suggestion_id or '-'}",
                    f"Suggested by: {suggested_by_user_id or '-'}",
                    f"Title: {title}",
                    f"Vibe: {vibe_text or '-'}",
                    f"Date: {created_at}",
                ]
            )
        )

    return "\n\n".join(blocks)


def _suggestions_keyboard(rows) -> InlineKeyboardMarkup:
    keyboard = []

    for suggestion_id, *_rest in rows:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"✅ Одобрить #{suggestion_id}",
                    callback_data=f"community_approve_suggestion:{suggestion_id}",
                ),
                InlineKeyboardButton(
                    text=f"❌ Отклонить #{suggestion_id}",
                    callback_data=f"community_reject_suggestion:{suggestion_id}",
                ),
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="◀️ Назад", callback_data="community_hub")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _drafts_keyboard(rows) -> InlineKeyboardMarkup:
    keyboard = []

    for draft_id, *_rest in rows:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🚀 Открыть #{draft_id}",
                    callback_data=f"use_draft_cb:{draft_id}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="◀️ Назад", callback_data="community_hub")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _approval_result_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🚀 Открыть черновик #{draft_id}",
                    callback_data=f"use_draft_cb:{draft_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 К заявкам",
                    callback_data="community_admin_suggestions",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 К черновикам",
                    callback_data="community_admin_drafts",
                )
            ],
        ]
    )


def _format_contributors(rows) -> str:
    if not rows:
        return "Пока пусто."

    blocks = []
    for user_id, username, total_sent, pending_count, approved_count, rejected_count, last_submission_at in rows:
        username_part = f"@{username}" if username else "без username"
        reserved = get_reserved_reward_slots(user_id)
        pending_reward = has_pending_premium_reward_request(user_id)
        available_batches = max(0, approved_count - reserved) // APPROVED_SUGGESTIONS_FOR_PREMIUM

        reward_line = "есть pending-запрос" if pending_reward else "запроса сейчас нет"

        blocks.append(
            "\n".join(
                [
                    f"{user_id} ({username_part})",
                    f"Отправил: {total_sent}",
                    f"Одобрено: {approved_count}",
                    f"На проверке: {pending_count}",
                    f"Отклонено: {rejected_count}",
                    f"Premium-пакетов доступно: {available_batches}",
                    f"Reward-запрос: {reward_line}",
                    f"Последняя заявка: {last_submission_at}",
                ]
            )
        )

    return "\n\n".join(blocks)


@router.message(Command("suggestions"))
async def admin_suggestions_list(message: Message):
    if not _admin_only(message):
        return

    rows = get_content_suggestions_by_status("pending", limit=20)
    await message.answer(
        "<b>Pending suggestions</b>\n\n" + escape(_format_suggestions(rows)),
        parse_mode="HTML",
    )


@router.message(Command("contributors"))
async def admin_contributors(message: Message):
    if not _admin_only(message):
        return

    rows = get_contributor_overview(limit=50)
    await message.answer(
        "<b>Contributors</b>\n\n" + escape(_format_contributors(rows)),
        parse_mode="HTML",
    )


@router.message(Command("approve_suggestion"))
async def admin_approve_suggestion(message: Message, command: CommandObject):
    if not _admin_only(message):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /approve_suggestion <id>")
        return

    suggestion_id = int(command.args)
    suggestion = get_content_suggestion(suggestion_id)

    if not suggestion:
        await message.answer("Заявка не найдена")
        return

    if suggestion[7] != "pending":
        await message.answer("Эта заявка уже обработана")
        return

    update_content_suggestion_status(
        suggestion_id=suggestion_id,
        status="approved",
        reviewed_by=message.from_user.id,
    )

    draft_id = create_admin_content_draft(
        suggestion_id=suggestion[0],
        suggested_by_user_id=suggestion[1],
        content_type=suggestion[3],
        title=suggestion[4],
        description=suggestion[5],
        vibe_text=suggestion[6],
    )

    stats = get_user_suggestion_stats(suggestion[1])
    await message.answer(
        (
            f"✅ Заявка #{suggestion_id} одобрена. "
            f"У пользователя теперь {stats['approved']} одобренных вкладов.\n\n"
            f"Черновик для add создан: #{draft_id}\n"
            f"Открыть: /use_draft {draft_id}"
        )
    )

    try:
        await message.bot.send_message(
            suggestion[1],
            (
                "✅ Твой контент одобрен и попал в копилку вкладов.\n\n"
                f"Всего одобрено: {stats['approved']}."
            ),
        )
    except Exception:
        pass


@router.message(Command("reject_suggestion"))
async def admin_reject_suggestion(message: Message, command: CommandObject):
    if not _admin_only(message):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /reject_suggestion <id>")
        return

    suggestion_id = int(command.args)
    suggestion = get_content_suggestion(suggestion_id)

    if not suggestion:
        await message.answer("Заявка не найдена")
        return

    if suggestion[7] != "pending":
        await message.answer("Эта заявка уже обработана")
        return

    update_content_suggestion_status(
        suggestion_id=suggestion_id,
        status="rejected",
        reviewed_by=message.from_user.id,
    )

    await message.answer(f"❌ Заявка #{suggestion_id} отклонена.")

    try:
        await message.bot.send_message(
            suggestion[1],
            "❌ Этот контент я пока не одобрил для базы, но можешь прислать другой вариант.",
        )
    except Exception:
        pass


def _format_premium_requests(rows) -> str:
    if not rows:
        return "Пока пусто."

    blocks = []
    for request_id, user_id, approved_snapshot, slots_reserved, status, created_at in rows:
        stats = get_user_suggestion_stats(user_id)
        blocks.append(
            "\n".join(
                [
                    f"#{request_id}",
                    f"User: {user_id}",
                    f"Approved snapshot: {approved_snapshot}",
                    f"Current approved: {stats['approved']}",
                    f"Reserved slots: {slots_reserved}",
                    f"Date: {created_at}",
                ]
            )
        )

    return "\n\n".join(blocks)


@router.message(Command("premium_requests"))
async def admin_premium_requests(message: Message):
    if not _admin_only(message):
        return

    rows = get_premium_reward_requests_by_status("pending", limit=20)
    await message.answer(
        "<b>Pending premium requests</b>\n\n" + escape(_format_premium_requests(rows)),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "community_admin_contributors")
async def community_admin_contributors(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    rows = get_contributor_overview(limit=50)
    await replace_screen(
        callback,
        text="<b>Авторы и вклад</b>\n\n" + escape(_format_contributors(rows)),
        reply_markup=community_hub_keyboard(is_admin=True),
    )


@router.callback_query(F.data == "community_admin_reward_requests")
async def community_admin_reward_requests(callback: CallbackQuery, user: dict):
    if not is_admin_user(user["telegram_id"]):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    rows = get_premium_reward_requests_by_status("pending", limit=20)
    await replace_screen(
        callback,
        text="<b>Pending reward-запросы</b>\n\n" + escape(_format_premium_requests(rows)),
        reply_markup=community_hub_keyboard(is_admin=True),
    )


@router.message(Command("drafts"))
async def admin_drafts(message: Message):
    if not _admin_only(message):
        return

    rows = get_admin_content_drafts(status="pending", limit=20)
    await message.answer(
        "<b>Pending drafts</b>\n\n" + escape(_format_drafts(rows)),
        parse_mode="HTML",
    )


@router.message(Command("approve_premium_request"))
async def admin_approve_premium_request(message: Message, command: CommandObject):
    if not _admin_only(message):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /approve_premium_request <id>")
        return

    request_id = int(command.args)
    request = get_premium_reward_request(request_id)

    if not request:
        await message.answer("Запрос не найден")
        return

    if request[4] != "pending":
        await message.answer("Этот запрос уже обработан")
        return

    premium_until = activate_premium(request[1], PREMIUM_REWARD_DAYS)
    update_premium_reward_request_status(
        request_id=request_id,
        status="approved",
        reviewed_by=message.from_user.id,
        premium_until=premium_until,
    )

    await message.answer(
        f"💎 Reward-запрос #{request_id} подтверждён. Premium начислен до {premium_until}."
    )

    try:
        await message.bot.send_message(
            request[1],
            (
                "💎 Твой reward-запрос подтверждён.\n\n"
                f"Тебе начислено {PREMIUM_REWARD_DAYS} дней Premium."
            ),
        )
    except Exception:
        pass


@router.message(Command("reject_premium_request"))
async def admin_reject_premium_request(message: Message, command: CommandObject):
    if not _admin_only(message):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /reject_premium_request <id>")
        return

    request_id = int(command.args)
    request = get_premium_reward_request(request_id)

    if not request:
        await message.answer("Запрос не найден")
        return

    if request[4] != "pending":
        await message.answer("Этот запрос уже обработан")
        return

    update_premium_reward_request_status(
        request_id=request_id,
        status="rejected",
        reviewed_by=message.from_user.id,
    )

    await message.answer(f"❌ Reward-запрос #{request_id} отклонён.")

    try:
        await message.bot.send_message(
            request[1],
            "❌ Запрос на reward-Premium пока отклонён.",
        )
    except Exception:
        pass

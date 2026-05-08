from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.series import get_random_series, load_series
from keyboards.series.menu import series_mode_kb
from keyboards.series.personal import (
    personal_series_keyboard,
    series_personal_prompt_keyboard,
    series_personal_question_keyboard,
)
from keyboards.series.vibes import another_series_keyboard, series_vibe_keyboard
from keyboards.common.premium_collections import premium_collections_keyboard
from states.series_personal import SeriesPersonalQuiz
from utils.access import (
    consume_free_personal_use,
    free_personal_locked_text,
    free_personal_status,
    has_premium_access,
    premium_feature_locked_text,
)
from utils.ai_fallback import ai_unavailable_text
from utils.ai_clarification import combine_prompt_with_clarification, personal_clarification_question
from utils.ai_rate_limit import ai_rate_limit_text, check_ai_request_limit
from utils.ai_personal_content import recommend_content_from_prompt
from utils.content_history import get_recently_seen_titles, record_content_impression
from utils.db import get_user_rating, is_in_favorites
from utils.flow_fx import pick_phrase, pulse_chat_action, show_transition_screen
from utils.fast_vibes import has_more_in_fast_vibe
from utils.llm_client import LLMClientError, LLMNotConfiguredError
from utils.media_sender import send_media
from utils.premium_collections import (
    get_random_collection_names,
    get_random_item_from_collection,
    has_more_in_collection,
)
from utils.personal_series import (
    QUESTION_COUNT,
    get_question,
    pick_random_questions,
    recommend_series,
)
from utils.text_limits import (
    MAX_AI_PROMPT_LENGTH,
    MIN_AI_PROMPT_LENGTH,
    clean_user_text,
    is_too_long,
    length_error_text,
)
from utils.ui import delete_tracked_message, replace_screen, replace_with_new_screen, track_active_screen

router = Router()

SERIES_TRANSITION_LINES = [
    "Смотрю, где у тебя сейчас может случиться залипание с первой серии.",
    "Пытаюсь поймать сериал, который удержит твой ритм.",
    "Собираю не просто жанр, а нужную тебе длину волны.",
    "Проверяю, что сейчас захватит тебя сильнее остального.",
]


def get_series_by_title(title: str) -> dict | None:
    for series in load_series():
        if series["title"] == title:
            return series
    return None


async def show_series_collections_screen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get("series_collection_options", [])

    await replace_screen(
        callback,
        text=(
            "💎 <b>Premium-подборки сериалов</b>\n\n"
            "Здесь уже готовые тематические заходы под конкретный просмотр."
        ),
        reply_markup=premium_collections_keyboard(
            options=options,
            pick_prefix="series_collection_pick",
            refresh_callback="series_collections_refresh",
        ),
    )


async def show_series_personal_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("series_personal_question_ids", [])
    current_index = data.get("series_personal_question_index", 0)

    if current_index >= len(question_ids):
        await callback.answer("Вопросы закончились")
        return

    question = get_question(question_ids[current_index])
    total = len(question_ids)
    text = (
        "🧠 <b>Персональный подбор сериала</b>\n\n"
        "Отвечай быстро и по вайбу. Я попробую поймать твой текущий "
        "сериальный настрой.\n\n"
        f"<b>{question['text']}</b>"
    )

    await replace_screen(
        callback,
        text=text,
        reply_markup=series_personal_question_keyboard(
            answers=[answer["text"] for answer in question["answers"]],
            current_index=current_index,
            total=total,
        ),
    )


async def show_personal_series_result(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
    candidate_index: int,
):
    data = await state.get_data()
    candidates = data.get("series_personal_candidates", [])

    if candidate_index < 0 or candidate_index >= len(candidates):
        await callback.answer("Запасных вариантов больше нет", show_alert=True)
        return

    candidate = candidates[candidate_index]
    series = get_series_by_title(candidate["title"])

    if not series:
        await callback.answer("Сериал не найден", show_alert=True)
        return

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])
    has_backup = candidate_index < len(candidates) - 1

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=None,
        current_source="series_personal",
        current_caption_extra=candidate["explanation"],
        personal_candidate_index=candidate_index,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=personal_series_keyboard(
            has_backup=has_backup,
            title=series["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=candidate["explanation"],
    )


@router.callback_query(F.data == "choose_series")
async def choose_series(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.clear()

    await replace_screen(
        callback,
        text="📺 Как будем подбирать сериал?",
        reply_markup=series_mode_kb(),
    )


@router.callback_query(F.data == "series_fast")
async def series_fast(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.update_data(fast_vibe_seen_count=0)
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "series")
    keyboard = series_vibe_keyboard(excluded_titles=excluded_titles)
    text = "📺 Какой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "📺 По сериалам ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    sent_message = await replace_with_new_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "series_surprise")
async def series_surprise(callback: CallbackQuery, user: dict, state: FSMContext):
    series = get_random_series(
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "series"),
    )

    if not series:
        await callback.answer("Сериал не найден", show_alert=True)
        return

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=None,
        current_source="series_surprise",
        current_caption_extra=None,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=another_series_keyboard(
            vibe=None,
            title=series["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "series_personal")
async def series_personal(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        can_use, next_available_at = free_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=free_personal_locked_text("Персональный подбор сериалов", next_available_at),
                reply_markup=series_mode_kb(),
            )
            return
        consume_free_personal_use(user["telegram_id"])

    await state.set_state(SeriesPersonalQuiz.describing)
    await state.update_data(
        series_personal_candidates=[],
        personal_candidate_index=0,
        current_source=None,
        current_caption_extra=None,
        pending_ai_prompt=None,
    )

    await delete_tracked_message(state, callback.bot, callback.message.chat.id, "last_personal_prompt_message_id")
    prompt_message = await replace_with_new_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор сериала</b>\n\n"
            "Опиши, какой сериал хочется: темп, настроение, длина, "
            "что любишь и что точно не надо.\n\n"
            "Например:\n"
            "<i>Хочу что-то мрачное, умное и затягивающее, но без супергероики. "
            "Чтобы была тайна и взрослый нерв.</i>"
        ),
        reply_markup=series_personal_prompt_keyboard(),
    )
    if prompt_message:
        await state.update_data(last_personal_prompt_message_id=prompt_message.message_id)


@router.message(SeriesPersonalQuiz.describing, F.text)
async def series_personal_description(message: Message, user: dict, state: FSMContext):
    user_prompt = clean_user_text(message.text)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    state_data = await state.get_data()
    pending_ai_prompt = clean_user_text(state_data.get("pending_ai_prompt") or "")
    has_pending_ai_prompt = bool(pending_ai_prompt)
    if has_pending_ai_prompt:
        user_prompt = combine_prompt_with_clarification(pending_ai_prompt, user_prompt)
        await state.update_data(pending_ai_prompt=None)

    if len(user_prompt) < MIN_AI_PROMPT_LENGTH:
        await message.answer("Опиши чуть подробнее: настроение, темп и чего точно не хочется.")
        return
    if is_too_long(user_prompt, MAX_AI_PROMPT_LENGTH):
        await message.answer(length_error_text(MAX_AI_PROMPT_LENGTH))
        return

    if not has_pending_ai_prompt:
        clarification_question = personal_clarification_question("series", user_prompt)
        if clarification_question:
            clarification_message = await message.answer(clarification_question)
            await state.update_data(
                pending_ai_prompt=user_prompt,
                last_personal_prompt_message_id=clarification_message.message_id,
            )
            return

    can_request_ai, retry_after = check_ai_request_limit(user["telegram_id"])
    if not can_request_ai:
        await message.answer(ai_rate_limit_text(retry_after))
        return

    processing_message = await message.answer("🧠 Сверяю твой вайб с базой сериалов...")
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_PHOTO,
    )

    try:
        recommendations = await recommend_content_from_prompt(
            content_type="series",
            user_id=user["telegram_id"],
            user_prompt=user_prompt,
        )
    except (LLMNotConfiguredError, LLMClientError):
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=series_mode_kb(),
        )
        return

    if not recommendations:
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=series_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        series_personal_candidates=[
            {
                "title": result["item"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    series = recommendations[0]["item"]
    explanation = recommendations[0]["explanation"]
    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])
    has_backup = len(recommendations) > 1

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=None,
        current_source="series_personal",
        current_caption_extra=explanation,
        personal_candidate_index=0,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])

    try:
        await processing_message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=message,
        item=series,
        content_type="series",
        reply_markup=personal_series_keyboard(
            has_backup=has_backup,
            title=series["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=explanation,
    )


@router.callback_query(F.data == "series_collections")
async def series_collections(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        await replace_screen(
            callback,
            text=premium_feature_locked_text("Premium-подборки сериалов"),
            reply_markup=series_mode_kb(),
        )
        return

    options = get_random_collection_names("series", count=3)
    if not options:
        await replace_screen(
            callback,
            text="💎 Premium-подборок для сериалов пока нет. Добавь их через /add.",
            reply_markup=series_mode_kb(),
        )
        return

    await state.update_data(series_collection_options=options)
    await show_series_collections_screen(callback, state)


@router.callback_query(F.data == "series_collections_refresh")
async def series_collections_refresh(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        await callback.answer("Подборки доступны только в Premium", show_alert=True)
        return

    options = get_random_collection_names("series", count=3)
    await state.update_data(series_collection_options=options)
    await show_series_collections_screen(callback, state)


@router.callback_query(F.data.startswith("series_collection_pick:"))
async def series_collection_pick(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    options = data.get("series_collection_options", [])
    index = int(callback.data.split(":", 1)[1])

    if index < 0 or index >= len(options):
        await callback.answer("Подборка не найдена", show_alert=True)
        return

    collection_name = options[index]
    series = get_random_item_from_collection(
        content_type="series",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not series:
        await callback.answer("В этой подборке пока ничего нет", show_alert=True)
        return

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=None,
        current_source="series_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])
    show_next_collection = has_more_in_collection(
        "series",
        collection_name,
        user["telegram_id"],
        current_title=series["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=another_series_keyboard(
            vibe=None,
            title=series["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "next_series_collection")
async def next_series_collection(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    collection_name = data.get("current_collection_name")

    if not collection_name:
        await callback.answer("Подборка уже закрыта", show_alert=True)
        return

    series = get_random_item_from_collection(
        content_type="series",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not series:
        await callback.answer("В этой подборке ты уже всё посмотрел за последнее время", show_alert=True)
        return

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=None,
        current_source="series_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])
    show_next_collection = has_more_in_collection(
        "series",
        collection_name,
        user["telegram_id"],
        current_title=series["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=another_series_keyboard(
            vibe=None,
            title=series["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "series_personal_progress")
async def series_personal_progress(callback: CallbackQuery):
    await callback.answer("Просто выбирай вариант ниже")


@router.callback_query(SeriesPersonalQuiz.answering, F.data.startswith("series_personal_answer:"))
async def series_personal_answer(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("series_personal_question_ids", [])
    current_index = data.get("series_personal_question_index", 0)
    answers_history = data.get("series_personal_answers", [])

    if current_index >= len(question_ids):
        await callback.answer("Вопрос уже закрыт")
        return

    question = get_question(question_ids[current_index])
    answer_index = int(callback.data.split(":", 1)[1])

    if answer_index < 0 or answer_index >= len(question["answers"]):
        await callback.answer("Ответ не найден", show_alert=True)
        return

    answers_history.append(
        {
            "question_id": question["id"],
            "answer_index": answer_index,
        }
    )

    current_index += 1
    await state.update_data(
        series_personal_answers=answers_history,
        series_personal_question_index=current_index,
    )

    if current_index < len(question_ids):
        await pulse_chat_action(callback)
        await show_series_personal_question(callback, state)
        return

    recommendations = recommend_series(
        user_id=user["telegram_id"],
        answer_history=answers_history,
    )

    if not recommendations:
        await state.clear()
        await replace_screen(
            callback,
            text=ai_unavailable_text(),
            reply_markup=series_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        series_personal_candidates=[
            {
                "title": result["series"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    await show_transition_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор сериала</b>\n\n"
            f"{pick_phrase(SERIES_TRANSITION_LINES)}"
        ),
        action="upload_photo",
    )
    await show_personal_series_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=0,
    )


@router.callback_query(F.data == "series_personal_backup")
async def series_personal_backup(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("personal_candidate_index", 0)

    await show_personal_series_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=current_index + 1,
    )


@router.callback_query(F.data.startswith("fast_series_vibe:"))
async def series_selected(callback: CallbackQuery, user: dict, state: FSMContext):
    vibe = callback.data.split(":", 1)[1]
    series = get_random_series(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "series"),
    )

    if not series:
        await callback.answer("Сериал не найден", show_alert=True)
        return

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=vibe,
        current_source="series_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=1,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])
    show_another = has_more_in_fast_vibe(
        "series",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "series"),
    )

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])

    await callback.message.delete()

    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=another_series_keyboard(
            vibe=vibe,
            title=series["title"],
            show_another=show_another,
            show_change_vibe=False,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data.startswith("another_series:"))
async def another_series(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    vibe = callback.data.split(":", 1)[1]
    series = get_random_series(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "series"),
    )

    if not series:
        await series_fast(callback, user, state)
        return

    seen_count = (
        int(data.get("fast_vibe_seen_count", 1)) + 1
        if data.get("current_vibe") == vibe and data.get("current_source") == "series_fast"
        else 1
    )

    await state.update_data(
        current_item=series,
        current_type="series",
        current_vibe=vibe,
        current_source="series_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=seen_count,
    )
    record_content_impression(user["telegram_id"], "series", series["title"])
    show_another = has_more_in_fast_vibe(
        "series",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "series"),
    )

    is_fav = is_in_favorites(user["telegram_id"], "series", series["title"])
    user_rating = get_user_rating(user["telegram_id"], "series", series["title"])

    await callback.message.delete()

    sent_message = await send_media(
        callback=callback,
        item=series,
        content_type="series",
        reply_markup=another_series_keyboard(
            vibe=vibe,
            title=series["title"],
            show_another=show_another,
            show_change_vibe=seen_count >= 2,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "refresh_series_vibes")
async def refresh_series_vibes(callback: CallbackQuery, user: dict, state: FSMContext):
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "series")
    keyboard = series_vibe_keyboard(excluded_titles=excluded_titles)
    text = "📺 Какой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "📺 По сериалам ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    await replace_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )

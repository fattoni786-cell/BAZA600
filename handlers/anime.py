from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.anime import get_random_anime, load_anime
from keyboards.anime.menu import anime_mode_kb
from keyboards.anime.personal import (
    anime_personal_question_keyboard,
    anime_personal_prompt_keyboard,
    personal_anime_keyboard,
)
from keyboards.anime.vibes import another_anime_keyboard, anime_vibe_keyboard
from keyboards.common.premium_collections import premium_collections_keyboard
from states.anime_personal import AnimePersonalQuiz
from utils.access import (
    consume_free_personal_use,
    consume_premium_personal_use,
    free_personal_locked_text,
    free_personal_status,
    has_premium_access,
    premium_feature_locked_text,
    premium_personal_locked_text,
    premium_personal_status,
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
from utils.personal_anime import (
    QUESTION_COUNT,
    get_question,
    pick_random_questions,
    recommend_anime,
)
from utils.text_limits import (
    MAX_AI_PROMPT_LENGTH,
    MIN_AI_PROMPT_LENGTH,
    clean_user_text,
    is_too_long,
    length_error_text,
)
from utils.premium_collections import (
    get_random_collection_names,
    get_random_item_from_collection,
    has_more_in_collection,
)
from utils.ui import delete_tracked_message, replace_screen, replace_with_new_screen, track_active_screen

router = Router()

ANIME_TRANSITION_LINES = [
    "Смотрю, какое аниме сейчас попадет точнее всего.",
    "Пытаюсь поймать не жанр, а твой аниме-ритм.",
    "Собираю из ответов довольно конкретный аниме-вектор.",
    "Проверяю, где сейчас у тебя случится лучший матч.",
]


def get_anime_by_title(title: str) -> dict | None:
    for item in load_anime():
        if item["title"] == title:
            return item
    return None


async def show_anime_collections_screen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get("anime_collection_options", [])

    await replace_screen(
        callback,
        text=(
            "💎 <b>Premium-подборки аниме</b>\n\n"
            "Здесь не про один тег, а про готовые тематические заходы."
        ),
        reply_markup=premium_collections_keyboard(
            options=options,
            pick_prefix="anime_collection_pick",
            refresh_callback="anime_collections_refresh",
        ),
    )


async def show_anime_personal_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("anime_personal_question_ids", [])
    current_index = data.get("anime_personal_question_index", 0)

    if current_index >= len(question_ids):
        await callback.answer("Вопросы закончились")
        return

    question = get_question(question_ids[current_index])
    total = len(question_ids)
    text = (
        "🧠 <b>Персональный подбор аниме</b>\n\n"
        "Отвечай быстро и по ощущению. Я попробую поймать именно твой "
        "текущий аниме-вайб.\n\n"
        f"<b>{question['text']}</b>"
    )

    await replace_screen(
        callback,
        text=text,
        reply_markup=anime_personal_question_keyboard(
            answers=[answer["text"] for answer in question["answers"]],
            current_index=current_index,
            total=total,
        ),
    )


async def show_personal_anime_result(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
    candidate_index: int,
):
    data = await state.get_data()
    candidates = data.get("anime_personal_candidates", [])

    if candidate_index < 0 or candidate_index >= len(candidates):
        await callback.answer("Запасных вариантов больше нет", show_alert=True)
        return

    candidate = candidates[candidate_index]
    item = get_anime_by_title(candidate["title"])

    if not item:
        await callback.answer("Аниме не найдено", show_alert=True)
        return

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])
    has_backup = candidate_index < len(candidates) - 1

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=None,
        current_source="anime_personal",
        current_caption_extra=candidate["explanation"],
        personal_candidate_index=candidate_index,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=personal_anime_keyboard(
            has_backup=has_backup,
            title=item["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=candidate["explanation"],
    )


@router.callback_query(F.data == "choose_anime")
async def choose_anime(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.clear()
    await replace_screen(
        callback,
        text="🎌 Как будем подбирать аниме?",
        reply_markup=anime_mode_kb(),
    )


@router.callback_query(F.data == "anime_fast")
async def anime_fast(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.update_data(fast_vibe_seen_count=0)
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "anime")
    keyboard = anime_vibe_keyboard(excluded_titles=excluded_titles)
    text = "🎌 Какой сейчас аниме-вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "🎌 По аниме ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    sent_message = await replace_with_new_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "anime_surprise")
async def anime_surprise(callback: CallbackQuery, user: dict, state: FSMContext):
    item = get_random_anime(
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "anime"),
    )

    if not item:
        await callback.answer("Аниме не найдено", show_alert=True)
        return

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=None,
        current_source="anime_surprise",
        current_caption_extra=None,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=another_anime_keyboard(
            vibe=None,
            title=item["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "anime_personal")
async def anime_personal(callback: CallbackQuery, user: dict, state: FSMContext):
    if has_premium_access(user):
        can_use, next_available_at, _remaining = premium_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=premium_personal_locked_text("Персональный подбор аниме", next_available_at),
                reply_markup=anime_mode_kb(),
            )
            return
        consume_premium_personal_use(user["telegram_id"])
    else:
        can_use, next_available_at = free_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=free_personal_locked_text("Персональный подбор аниме", next_available_at),
                reply_markup=anime_mode_kb(),
            )
            return
        consume_free_personal_use(user["telegram_id"])

    await state.set_state(AnimePersonalQuiz.describing)
    await state.update_data(
        anime_personal_candidates=[],
        personal_candidate_index=0,
        current_source=None,
        current_caption_extra=None,
        pending_ai_prompt=None,
    )

    await delete_tracked_message(state, callback.bot, callback.message.chat.id, "last_personal_prompt_message_id")
    prompt_message = await replace_with_new_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор аниме</b>\n\n"
            "Опиши аниме-вайб свободно: хочется тепла, жести, психологии, "
            "исекая, спорта, романтики или странного гения?\n\n"
            "Например:\n"
            "<i>Хочу что-то психологическое и мрачное, но не просто мясо. "
            "Чтобы после серии хотелось думать.</i>"
        ),
        reply_markup=anime_personal_prompt_keyboard(),
    )
    if prompt_message:
        await state.update_data(last_personal_prompt_message_id=prompt_message.message_id)


@router.message(AnimePersonalQuiz.describing, F.text)
async def anime_personal_description(message: Message, user: dict, state: FSMContext):
    user_prompt = clean_user_text(message.text)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    state_data = await state.get_data()
    pending_ai_prompt = clean_user_text(state_data.get("pending_ai_prompt") or "")
    has_pending_ai_prompt = bool(pending_ai_prompt)
    if has_pending_ai_prompt:
        user_prompt = combine_prompt_with_clarification(pending_ai_prompt, user_prompt)
        await state.update_data(pending_ai_prompt=None)

    if len(user_prompt) < MIN_AI_PROMPT_LENGTH:
        await message.answer("Опиши чуть подробнее: настроение, темп и чего избегаем.")
        return
    if is_too_long(user_prompt, MAX_AI_PROMPT_LENGTH):
        await message.answer(length_error_text(MAX_AI_PROMPT_LENGTH))
        return

    if not has_pending_ai_prompt:
        clarification_question = personal_clarification_question("anime", user_prompt)
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

    processing_message = await message.answer("🧠 Сверяю твой вайб с базой аниме...")
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_PHOTO,
    )

    try:
        recommendations = await recommend_content_from_prompt(
            content_type="anime",
            user_id=user["telegram_id"],
            user_prompt=user_prompt,
        )
    except (LLMNotConfiguredError, LLMClientError):
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=anime_mode_kb(),
        )
        return

    if not recommendations:
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=anime_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        anime_personal_candidates=[
            {
                "title": result["item"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    item = recommendations[0]["item"]
    explanation = recommendations[0]["explanation"]
    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])
    has_backup = len(recommendations) > 1

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=None,
        current_source="anime_personal",
        current_caption_extra=explanation,
        personal_candidate_index=0,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])

    try:
        await processing_message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=message,
        item=item,
        content_type="anime",
        reply_markup=personal_anime_keyboard(
            has_backup=has_backup,
            title=item["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=explanation,
    )


@router.callback_query(F.data == "anime_collections")
async def anime_collections(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        await replace_screen(
            callback,
            text=premium_feature_locked_text("Premium-подборки аниме"),
            reply_markup=anime_mode_kb(),
        )
        return

    options = get_random_collection_names("anime", count=3)
    if not options:
        await replace_screen(
            callback,
            text="💎 Premium-подборок для аниме пока нет. Добавь их через /add.",
            reply_markup=anime_mode_kb(),
        )
        return

    await state.update_data(anime_collection_options=options)
    await show_anime_collections_screen(callback, state)


@router.callback_query(F.data == "anime_collections_refresh")
async def anime_collections_refresh(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        await callback.answer("Подборки доступны только в Premium", show_alert=True)
        return

    options = get_random_collection_names("anime", count=3)
    await state.update_data(anime_collection_options=options)
    await show_anime_collections_screen(callback, state)


@router.callback_query(F.data.startswith("anime_collection_pick:"))
async def anime_collection_pick(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    options = data.get("anime_collection_options", [])
    index = int(callback.data.split(":", 1)[1])

    if index < 0 or index >= len(options):
        await callback.answer("Подборка не найдена", show_alert=True)
        return

    collection_name = options[index]
    item = get_random_item_from_collection(
        content_type="anime",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not item:
        await callback.answer("В этой подборке пока ничего нет", show_alert=True)
        return

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=None,
        current_source="anime_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])
    show_next_collection = has_more_in_collection(
        "anime",
        collection_name,
        user["telegram_id"],
        current_title=item["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=another_anime_keyboard(
            vibe=None,
            title=item["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "next_anime_collection")
async def next_anime_collection(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    collection_name = data.get("current_collection_name")

    if not collection_name:
        await callback.answer("Подборка уже закрыта", show_alert=True)
        return

    item = get_random_item_from_collection(
        content_type="anime",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not item:
        await callback.answer("В этой подборке ты уже всё посмотрел за последнее время", show_alert=True)
        return

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=None,
        current_source="anime_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])
    show_next_collection = has_more_in_collection(
        "anime",
        collection_name,
        user["telegram_id"],
        current_title=item["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=another_anime_keyboard(
            vibe=None,
            title=item["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "anime_personal_progress")
async def anime_personal_progress(callback: CallbackQuery):
    await callback.answer("Просто выбирай вариант ниже")


@router.callback_query(AnimePersonalQuiz.answering, F.data.startswith("anime_personal_answer:"))
async def anime_personal_answer(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("anime_personal_question_ids", [])
    current_index = data.get("anime_personal_question_index", 0)
    answers_history = data.get("anime_personal_answers", [])

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
        anime_personal_answers=answers_history,
        anime_personal_question_index=current_index,
    )

    if current_index < len(question_ids):
        await pulse_chat_action(callback)
        await show_anime_personal_question(callback, state)
        return

    recommendations = recommend_anime(
        user_id=user["telegram_id"],
        answer_history=answers_history,
    )

    if not recommendations:
        await state.clear()
        await replace_screen(
            callback,
            text=ai_unavailable_text(),
            reply_markup=anime_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        anime_personal_candidates=[
            {
                "title": result["anime"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    await show_transition_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор аниме</b>\n\n"
            f"{pick_phrase(ANIME_TRANSITION_LINES)}"
        ),
        action="typing",
    )
    await show_personal_anime_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=0,
    )


@router.callback_query(F.data == "anime_personal_backup")
async def anime_personal_backup(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("personal_candidate_index", 0)

    await show_personal_anime_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=current_index + 1,
    )


@router.callback_query(F.data.startswith("fast_anime_vibe:"))
async def anime_selected(callback: CallbackQuery, user: dict, state: FSMContext):
    vibe = callback.data.split(":", 1)[1]
    item = get_random_anime(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "anime"),
    )

    if not item:
        await callback.answer("Аниме не найдено", show_alert=True)
        return

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=vibe,
        current_source="anime_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=1,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])
    show_another = has_more_in_fast_vibe(
        "anime",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "anime"),
    )

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=another_anime_keyboard(
            vibe=vibe,
            title=item["title"],
            show_another=show_another,
            show_change_vibe=False,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data.startswith("another_anime:"))
async def another_anime(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    vibe = callback.data.split(":", 1)[1]
    item = get_random_anime(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "anime"),
    )

    if not item:
        await anime_fast(callback, user, state)
        return

    seen_count = (
        int(data.get("fast_vibe_seen_count", 1)) + 1
        if data.get("current_vibe") == vibe and data.get("current_source") == "anime_fast"
        else 1
    )

    await state.update_data(
        current_item=item,
        current_type="anime",
        current_vibe=vibe,
        current_source="anime_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=seen_count,
    )
    record_content_impression(user["telegram_id"], "anime", item["title"])
    show_another = has_more_in_fast_vibe(
        "anime",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "anime"),
    )

    is_fav = is_in_favorites(user["telegram_id"], "anime", item["title"])
    user_rating = get_user_rating(user["telegram_id"], "anime", item["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=item,
        content_type="anime",
        reply_markup=another_anime_keyboard(
            vibe=vibe,
            title=item["title"],
            show_another=show_another,
            show_change_vibe=seen_count >= 2,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "refresh_anime_vibes")
async def refresh_anime_vibes(callback: CallbackQuery, user: dict, state: FSMContext):
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "anime")
    keyboard = anime_vibe_keyboard(excluded_titles=excluded_titles)
    text = "🎌 Какой сейчас аниме-вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "🎌 По аниме ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    await replace_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )

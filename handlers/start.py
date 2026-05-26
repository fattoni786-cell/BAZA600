import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from keyboards.menu import bottom_nav_kb
from utils.analytics import track_event
from utils.db import get_user_content_menu_types, set_user_content_menu_types
from utils.ui import delete_active_screen, delete_tracked_message, replace_screen, track_active_screen

router = Router()

CONTENT_MENU_ITEMS = [
    {
        "key": "anime",
        "label": "🎌 Аниме",
        "callback": "choose_anime",
    },
    {
        "key": "book",
        "label": "📚 Книга",
        "callback": "choose_book",
    },
    {
        "key": "movie",
        "label": "🎬 Фильм",
        "callback": "choose_movie",
    },
    {
        "key": "game",
        "label": "🎮 Игра",
        "callback": "choose_game",
    },
    {
        "key": "series",
        "label": "📺 Сериал",
        "callback": "choose_series",
    },
]
DEFAULT_CONTENT_TYPES = [item["key"] for item in CONTENT_MENU_ITEMS]

START_PHRASES = [
    "Выбрал — правь.",
    "Лайкнул — властвуй.",
    "Сохранил — победил.",
    "Выбирай. Или страдай.",
    "Жми — и царствуй.",
    "Вкус есть? Докажи.",
    "Не думай. Выбирай.",
    "Выбери лучшее. Остальное — в изгнание.",
    "Один выбор — одна власть.",
    "Свайпай. Сохраняй. Властвуй.",
    "Твой вкус — закон.",
    "Корона за выбор.",
    "Сохранил? Значит, твоё.",
    "Выбирай, пока не выбрали за тебя.",
    "Архивируй прекрасное.",
    "Здарова, меченый.",
    "Контент сам себя не выберет.",
    "Добро пожаловать в культ хорошего выбора.",
    "Твой вкус принят на рассмотрение.",
    "База приветствует тебя, избранный.",
    "Здесь решается судьба твоего вечера.",
    "Твой вечер можно спасти.",
    "Кино, книги и прочие способы исчезнуть из реальности.",
    "Выбирай мудро. Или красиво.",
    "Мы не судим твой вкус. Пока что.",
    "Найди то, что зайдёт. Или хотя бы не бесит.",
    "Архив удовольствий и культурного алиби.",
    "Здесь твоя нерешительность получает интерфейс.",
    "Потерялся в контенте? Отлично, ты по адресу.",
    "Выбери. Потом сделай вид, что так и планировал.",
    "База открыта. Не жди на входе.",
    "Твой личный склад смыслов.",
    "Найди фильм. Сохрани книгу. Пропади на выходные.",
    "Для тех, кто хочет “что-нибудь нормальное”.",
    "Контентная дыра открыта. Прыгай.",
    "Тут можно найти всё, кроме низкосортного контента.",
    "Сервис спасения от вопроса “что посмотреть?”",
    "Немного культуры. Немного хаоса. Много кнопок.",
    "Выбор есть. Ответственность за него — твоя.",
    "Добро пожаловать в место, где “потом посмотрю” становится образом жизни.",
    "Официальный поставщик “закину в избранное и забуду”.",
    "Ищи то, что станет твоим выбором.",
    "Твой вкус странный. Нам нравится.",
    "Культурный бункер на случай скуки.",
    "Подборки для людей, которые устали выбирать.",
    "Нажимай осторожно: может понравиться.",
    "Здесь контент получает второй шанс. Как и ты.",
    "Сохраняй лучшее. Игнорируй реальность.",
    "Ты пришёл за рекомендацией. Мы сделали вид, что знаем.",
    "Всё, что нужно для вечернего самообмана.",
    "База загружена. Социализация отменяется.",
    "Добро пожаловать. Твой свободный вечер уже под угрозой.",
    "Здесь контент выбирает тебя. Ну почти.",
    "“что посмотреть?” — это диагноз, который лечит база.",
    "Введи запрос и доверься сомнительной магии.",
    "Мы нашли тебе занятие. Продуктивности не скажем.",
    "Книги, фильмы, игры, сериалы — всё для легального исчезновения.",
    "Твоя прокрастинация получила навигацию.",
    "Не знаешь, чего хочешь? Отлично, мы тоже, но попробуем.",
    "Здесь начинается культурное развитие с удобным меню.",
    "На случай, если жизнь слишком реальная.",
    "Контент для тех, кто устал от собственного вкуса.",
    "База открыта. Вечер закрыт.",
    "Тут можно выбрать всё, кроме нормального режима сна.",
    "Ищи с умом: можешь случайно найти шедевр.",
    "Твоё “на 10 минут” начинается здесь.",
    "Мы не обещаем гениальность. Только варианты.",
    "Выбор контента — тоже форма кризиса.",
    "Здесь твоя нерешительность превращается в возможность.",
    "Тыкай. Остальное — проблема алгоритма.",
    "Найди себе повод не выходить из дома.",
    "Добро пожаловать в храм “потом посмотрю”.",
    "Контентная зависимость? Нет, культурный интерес.",
    "Твой вкус странный, но мы настроены дипломатично.",
    "База600: склад вайбов с сомнительной вентиляцией.",
    "Один запрос — и ты снова занят.",
    "Ты выбираешь контент. Контент выбирает тебя.",
    "Для тех, кто открыл бот и забыл зачем.",
    "Сохрани, чтобы никогда не открыть.",
    "Мы поможем выбрать. Осуждать будем молча.",
    "Здесь “не знаю” превращается в “ладно, попробую”.",
    "Культурный бункер открыт. Заходи, не бойся...",
    "Нажал кнопку — потерял счёт времени.",
    "Книги, фильмы и прочие уважительные причины исчезнуть.",
    "Добро пожаловать в отдел спасения нерешительных.",
    "Тут начинается “ну ещё одну серию”.",
    "База загружена. Тревожность выбора активирована.",
    "Подборки для людей, которые уже всё видели. По их словам.",
    "Выбирай быстро. Сомневайся потом.",
    "Мы не лечим скуку. Мы её красиво уничтожаем.",
    "Твой личный поставщик “что-нибудь по душе”.",
    "Здесь даже плохой вкус найдёт дом.",
    "От вдохновения до полного овоща.",
    "Введи желаемое. Получи надежду.",
    "Система готова притвориться, что понимает твой вкус.",
    "База №600: здесь избранное растёт быстрее, чем планы на жизнь.",
    "Ты здесь не случайно. Ты просто опять не знаешь, что смотреть.",
    "Найди что-то достойное. Или хотя бы длинное.",
    "Контентный компас для потерянных.",
    "Добро пожаловать в зону культурной неопределённости.",
    "Сохраняй прекрасное. Узнавай нужное.",
]


async def delete_last_audio_message(state: FSMContext, chat_id: int, bot):
    data = await state.get_data()
    msg_id = data.get("last_audio_message_id")

    if not msg_id:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

    await state.update_data(last_audio_message_id=None)


def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Подобрать контент",
                    callback_data="choose_content_hub",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Поиск по базе",
                    callback_data="search_start",
                )
            ],
        ]
    )


def normalize_content_menu_types(content_types: list[str] | None) -> list[str]:
    if not content_types:
        return DEFAULT_CONTENT_TYPES.copy()

    allowed = set(DEFAULT_CONTENT_TYPES)
    result: list[str] = []
    for content_type in content_types:
        if content_type in allowed and content_type not in result:
            result.append(content_type)

    return result or DEFAULT_CONTENT_TYPES.copy()


def get_saved_content_menu_types(user_id: int) -> list[str]:
    return normalize_content_menu_types(get_user_content_menu_types(user_id))


def content_type_labels(content_types: list[str]) -> str:
    labels = [
        item["label"]
        for item in CONTENT_MENU_ITEMS
        if item["key"] in content_types
    ]
    return ", ".join(labels)


def content_hub_text(content_types: list[str]) -> str:
    return "<b>Что выбираем?</b>"


def content_hub_keyboard(content_types: list[str] | None = None):
    selected_types = normalize_content_menu_types(content_types)
    action_buttons = [
        InlineKeyboardButton(
            text=item["label"],
            callback_data=item["callback"],
        )
        for item in CONTENT_MENU_ITEMS
        if item["key"] in selected_types
    ]
    action_buttons.append(
        InlineKeyboardButton(
            text="⚙️ Меню",
            callback_data="content_menu_settings",
        )
    )

    buttons = [
        action_buttons[index:index + 2]
        for index in range(0, len(action_buttons), 2)
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def content_settings_text(selected_types: list[str]) -> str:
    return (
        "⚙️ Настройка разделов\n\n"
        "Отметь, что хочешь видеть в меню подбора. "
        "Например, можно оставить только игры и фильмы.\n\n"
        f"Сейчас выбрано: {content_type_labels(selected_types)}"
    )


def content_settings_keyboard(selected_types: list[str]):
    selected = set(selected_types)
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if item['key'] in selected else '⬜'} {item['label']}",
                callback_data=f"content_menu_toggle:{item['key']}",
            )
        ]
        for item in CONTENT_MENU_ITEMS
    ]

    buttons.extend([
        [
            InlineKeyboardButton(
                text="✨ Показать всё",
                callback_data="content_menu_select_all",
            )
        ],
        [
            InlineKeyboardButton(
                text="💾 Сохранить",
                callback_data="content_menu_save",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="content_menu_back",
            )
        ],
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def main_menu_text(user: dict) -> str:
    return f"<b>{random.choice(START_PHRASES)}</b>"


async def send_main_menu(message: Message, user: dict, refresh_bottom_nav: bool = False):
    if refresh_bottom_nav:
        await message.answer("Нижнее меню включено.", reply_markup=bottom_nav_kb())

    sent_message = await message.answer(
        main_menu_text(user),
        reply_markup=start_keyboard(),
        parse_mode="HTML",
    )
    return sent_message


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext, user: dict):
    track_event(user["telegram_id"], "start")
    await delete_active_screen(state, message.bot, message.chat.id)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    sent_message = await send_main_menu(message, user, refresh_bottom_nav=True)
    await track_active_screen(state, sent_message)


@router.message(F.text == "🏠 Меню")
async def main_menu_button(message: Message, state: FSMContext, user: dict):
    track_event(user["telegram_id"], "main_menu")
    await delete_last_audio_message(state, message.chat.id, message.bot)
    await delete_active_screen(state, message.bot, message.chat.id)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    await state.clear()
    sent_message = await send_main_menu(message, user)
    await track_active_screen(state, sent_message)


@router.message(F.text == "🎯 Подобрать контент")
async def content_hub_button(message: Message, state: FSMContext, user: dict):
    track_event(user["telegram_id"], "open_content_hub")
    content_types = get_saved_content_menu_types(user["telegram_id"])
    await delete_active_screen(state, message.bot, message.chat.id)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    await state.clear()
    sent_message = await message.answer(
        content_hub_text(content_types),
        reply_markup=content_hub_keyboard(content_types),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "choose_content_hub")
async def choose_content_hub(callback: CallbackQuery, user: dict):
    track_event(user["telegram_id"], "open_content_hub")
    content_types = get_saved_content_menu_types(user["telegram_id"])
    await replace_screen(
        callback,
        text=content_hub_text(content_types),
        reply_markup=content_hub_keyboard(content_types),
    )


@router.callback_query(F.data == "content_menu_settings")
async def content_menu_settings(callback: CallbackQuery, state: FSMContext, user: dict):
    content_types = get_saved_content_menu_types(user["telegram_id"])
    await state.update_data(content_menu_selected=content_types)
    await replace_screen(
        callback,
        text=content_settings_text(content_types),
        reply_markup=content_settings_keyboard(content_types),
    )


@router.callback_query(F.data.startswith("content_menu_toggle:"))
async def content_menu_toggle(callback: CallbackQuery, state: FSMContext):
    content_type = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected_types = normalize_content_menu_types(data.get("content_menu_selected"))

    if content_type in selected_types:
        if len(selected_types) == 1:
            await callback.answer(
                "Хотя бы один раздел должен остаться в меню.",
                show_alert=True,
            )
            return
        selected_types.remove(content_type)
    elif content_type in DEFAULT_CONTENT_TYPES:
        selected_types.append(content_type)

    await state.update_data(content_menu_selected=selected_types)
    await replace_screen(
        callback,
        text=content_settings_text(selected_types),
        reply_markup=content_settings_keyboard(selected_types),
    )


@router.callback_query(F.data == "content_menu_select_all")
async def content_menu_select_all(callback: CallbackQuery, state: FSMContext):
    selected_types = DEFAULT_CONTENT_TYPES.copy()
    await state.update_data(content_menu_selected=selected_types)
    await replace_screen(
        callback,
        text=content_settings_text(selected_types),
        reply_markup=content_settings_keyboard(selected_types),
    )


@router.callback_query(F.data == "content_menu_save")
async def content_menu_save(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    selected_types = normalize_content_menu_types(data.get("content_menu_selected"))
    set_user_content_menu_types(user["telegram_id"], selected_types)
    await state.update_data(content_menu_selected=selected_types)
    await callback.answer("Сохранил меню под тебя.")
    await replace_screen(
        callback,
        text=content_hub_text(selected_types),
        reply_markup=content_hub_keyboard(selected_types),
    )


@router.callback_query(F.data == "content_menu_back")
async def content_menu_back(callback: CallbackQuery, user: dict):
    content_types = get_saved_content_menu_types(user["telegram_id"])
    await replace_screen(
        callback,
        text=content_hub_text(content_types),
        reply_markup=content_hub_keyboard(content_types),
    )


@router.callback_query(F.data == "go_to_menu")
async def go_to_menu(callback: CallbackQuery, state: FSMContext, user: dict):
    await delete_last_audio_message(state, callback.message.chat.id, callback.message.bot)
    await state.clear()
    await callback.answer()

    message = callback.message

    if message.photo or message.video or message.animation or message.document:
        try:
            await message.delete()
        except Exception:
            pass

        await message.answer(
            main_menu_text(user),
            reply_markup=start_keyboard(),
            parse_mode="HTML",
        )
        return

    await replace_screen(
        callback,
        text=main_menu_text(user),
        reply_markup=start_keyboard(),
    )

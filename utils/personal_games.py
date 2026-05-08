import random
from collections import defaultdict

from data.games import load_games
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_favorites, get_user_rated_content

QUESTION_COUNT = 4
ANSWER_LABELS = ["0%", "50%", "75%", "600%"]


def _answers(weight_sets: list[dict[str, float]]) -> list[dict]:
    return [
        {"text": ANSWER_LABELS[index], "weights": weights}
        for index, weights in enumerate(weight_sets)
    ]


GAME_PERSONAL_QUESTIONS = [
    {"id": "g01", "text": "Хочется просто исчезнуть в игре на пару часов?", "answers": _answers([{"short_play": 2, "mindless_fun": 1}, {"chill": 2, "solo": 1}, {"atmospheric": 2, "story": 2}, {"long_play": 4, "solo": 2, "exploration": 1}])},
    {"id": "g02", "text": "Нужен ли сегодня реальный челлендж?", "answers": _answers([{"chill": 2, "mindless_fun": 1}, {"skill_based": 1, "fast": 1}, {"hardcore": 2, "skill_based": 2}, {"hardcore": 4, "skill_based": 3, "survival": 1}])},
    {"id": "g03", "text": "Хочется ли мощного сюжета?", "answers": _answers([{"mindless_fun": 2, "fast": 1}, {"story": 1, "choices_matter": 1}, {"story": 3, "emotional": 2}, {"story": 4, "choices_matter": 3, "emotional": 2}])},
    {"id": "g04", "text": "Ты сегодня больше про одиночество или движ с людьми?", "answers": _answers([{"multiplayer": 3, "fast": 1}, {"multiplayer": 1, "solo": 1}, {"solo": 3, "lonely": 2}, {"solo": 4, "lonely": 3, "story": 1}])},
    {"id": "g05", "text": "Хочется ли просто расслабиться под музыку и процесс?", "answers": _answers([{"hardcore": 1, "strategy": 1}, {"relax_music": 2, "chill": 1}, {"relax_music": 3, "flow_state": 2, "chill": 2}, {"relax_music": 4, "flow_state": 3, "chill": 3}])},
    {"id": "g06", "text": "Нужна ли скорость?", "answers": _answers([{"strategy": 1, "story": 1}, {"fast": 1, "shooting": 1}, {"fast": 3, "shooting": 2}, {"fast": 4, "shooting": 3, "mindless_fun": 1}])},
    {"id": "g07", "text": "Тянет ли в исследование мира?", "answers": _answers([{"short_play": 1, "mindless_fun": 1}, {"exploration": 2, "sandbox": 1}, {"exploration": 3, "atmospheric": 2}, {"exploration": 4, "sandbox": 2, "long_play": 2}])},
    {"id": "g08", "text": "Хочется создавать, строить, возиться?", "answers": _answers([{"story": 1}, {"creative": 2, "sandbox": 1}, {"creative": 3, "sandbox": 2}, {"creative": 4, "sandbox": 3, "flow_state": 1}])},
    {"id": "g09", "text": "Нужен ли вайб силы и доминации?", "answers": _answers([{"story": 1}, {"power_fantasy": 2, "fast": 1}, {"power_fantasy": 3, "shooting": 2}, {"power_fantasy": 4, "fast": 2, "shooting": 2}])},
    {"id": "g10", "text": "Есть настроение на что-то странное?", "answers": _answers([{"classic": 1}, {"weird": 2, "creative": 1}, {"weird": 3, "mr600_choice": 2}, {"weird": 4, "mr600_choice": 3, "sandbox": 1}])},
    {"id": "g11", "text": "Хочется ли старого доброго ностальгического вайба?", "answers": _answers([{"weird": 1}, {"classic": 1, "nostalgic": 2}, {"nostalgic": 3, "classic": 2}, {"nostalgic": 4, "classic": 3}])},
    {"id": "g12", "text": "Нужен ли длинный запой, а не короткий заход?", "answers": _answers([{"short_play": 3, "mindless_fun": 1}, {"short_play": 1, "long_play": 1}, {"long_play": 3, "story": 1}, {"long_play": 4, "choices_matter": 2, "solo": 1}])},
    {"id": "g13", "text": "Готов ли ты сегодня что-то реально менеджерить?", "answers": _answers([{"mindless_fun": 2}, {"strategy": 1, "sandbox": 1}, {"strategy": 3, "survival": 1}, {"strategy": 4, "survival": 2, "choices_matter": 1}])},
    {"id": "g14", "text": "Нужна ли игра, в которой решения имеют вес?", "answers": _answers([{"mindless_fun": 2}, {"choices_matter": 1, "story": 1}, {"choices_matter": 3, "story": 2}, {"choices_matter": 4, "story": 3, "emotional": 1}])},
    {"id": "g15", "text": "Хочется ли мрачности?", "answers": _answers([{"chill": 2, "relax_music": 1}, {"dark": 1, "atmospheric": 1}, {"dark": 3, "survival": 2}, {"dark": 4, "survival": 2, "lonely": 1}])},
    {"id": "g16", "text": "Ты сейчас больше про сюжет или про чистый геймплей?", "answers": _answers([{"story": 3, "emotional": 1}, {"story": 1, "mindless_fun": 1}, {"mindless_fun": 3, "fast": 1}, {"mindless_fun": 4, "flow_state": 2, "skill_based": 1}])},
    {"id": "g17", "text": "Хочется ли сегодня пострелять?", "answers": _answers([{"story": 1}, {"shooting": 1, "fast": 1}, {"shooting": 3, "fast": 2}, {"shooting": 4, "fast": 3, "power_fantasy": 1}])},
    {"id": "g18", "text": "Тянет ли к выживанию и давлению?", "answers": _answers([{"chill": 1}, {"survival": 1, "dark": 1}, {"survival": 3, "dark": 2}, {"survival": 4, "dark": 3, "strategy": 1}])},
    {"id": "g19", "text": "Нужен ли поток, где можно просто залипнуть и потеряться во времени?", "answers": _answers([{"short_play": 1}, {"flow_state": 2, "chill": 1}, {"flow_state": 3, "addictive": 2}, {"flow_state": 4, "addictive": 3, "relax_music": 1}])},
    {"id": "g20", "text": "Хочется ли игры, в которой можно жить долго?", "answers": _answers([{"short_play": 2}, {"long_play": 2, "sandbox": 1}, {"long_play": 3, "solo": 1}, {"long_play": 4, "sandbox": 2, "story": 1}])},
    {"id": "g21", "text": "Нужна ли концентрация и скилл?", "answers": _answers([{"chill": 1}, {"skill_based": 2, "fast": 1}, {"skill_based": 3, "hardcore": 2}, {"skill_based": 4, "hardcore": 3}])},
    {"id": "g22", "text": "Тебе сегодня ближе одиночное приключение?", "answers": _answers([{"multiplayer": 2}, {"solo": 1, "story": 1}, {"solo": 3, "atmospheric": 1}, {"solo": 4, "story": 2, "exploration": 1}])},
    {"id": "g23", "text": "Хочется ли просто кайфануть без сильной умственной нагрузки?", "answers": _answers([{"strategy": 1, "choices_matter": 1}, {"mindless_fun": 2, "short_play": 1}, {"mindless_fun": 3, "addictive": 2}, {"mindless_fun": 4, "addictive": 3, "fast": 1}])},
    {"id": "g24", "text": "Готов ли ты сегодня читать, слушать и вникать?", "answers": _answers([{"mindless_fun": 2}, {"story": 1, "choices_matter": 1}, {"story": 3, "choices_matter": 2}, {"story": 4, "choices_matter": 3, "emotional": 1}])},
    {"id": "g25", "text": "Тянет ли к монстрам, чудовищам и опасным тварям?", "answers": _answers([{"classic": 1}, {"monsters": 2, "dark": 1}, {"monsters": 3, "survival": 1}, {"monsters": 4, "dark": 2, "survival": 1}])},
    {"id": "g26", "text": "Хочется ли чего-то уютного, но не скучного?", "answers": _answers([{"hardcore": 1}, {"chill": 2, "creative": 1}, {"chill": 3, "creative": 2, "sandbox": 1}, {"chill": 4, "creative": 2, "flow_state": 2}])},
    {"id": "g27", "text": "Нужен ли сегодня аддиктивный крючок?", "answers": _answers([{"story": 1}, {"addictive": 2, "short_play": 1}, {"addictive": 3, "fast": 1}, {"addictive": 4, "fast": 2, "mindless_fun": 1}])},
    {"id": "g28", "text": "Хочется ли потеряться в атмосфере, а не в экшене?", "answers": _answers([{"fast": 1}, {"atmospheric": 2, "exploration": 1}, {"atmospheric": 3, "exploration": 2}, {"atmospheric": 4, "exploration": 2, "solo": 1}])},
    {"id": "g29", "text": "Тебе нужна игра, которая держит в одиночку, а не за счёт друзей?", "answers": _answers([{"multiplayer": 3}, {"solo": 1, "story": 1}, {"solo": 3, "long_play": 1}, {"solo": 4, "story": 2, "choices_matter": 1}])},
    {"id": "g30", "text": "Хочется ли, чтобы игра была прям 'твоя тема' на сегодня?", "answers": _answers([{"classic": 1}, {"mr600_choice": 2, "weird": 1}, {"mr600_choice": 3, "weird": 2}, {"mr600_choice": 4, "weird": 2, "story": 1}])},
]

QUESTION_BY_ID = {question["id"]: question for question in GAME_PERSONAL_QUESTIONS}

TAG_EXPLANATIONS = {
    "addictive": [
        "тебе нужен липкий игровой цикл",
        "сейчас хочется просто залипнуть без лишних разговоров",
        "тебе важно, чтобы игра не отпускала",
        "нужен процесс, в который легко провалиться на часы",
        "сейчас хочется постоянного дофаминового цикла",
    ],

    "atmospheric": [
        "тебе важен сам воздух игры",
        "сегодня атмосферность для тебя важнее шума",
        "хочется раствориться в ощущении мира",
        "тебе важна не механика, а настроение вокруг неё",
        "сейчас ты ловишь именно атмосферу, а не действия",
    ],

    "chill": [
        "тебе нужен более мягкий режим",
        "сейчас лучше ложится спокойный темп",
        "хочется расслабиться без давления",
        "тебе нужен ненапряжный игровой поток",
        "сейчас игра должна скорее разгружать, чем напрягать",
    ],

    "choices_matter": [
        "тебе нравится, когда решения реально что-то значат",
        "сегодня хочется веса в каждом выборе",
        "важно чувствовать последствия своих действий",
        "тебе интереснее влиять на ход событий",
        "сейчас тебе нужна ответственность за каждое решение",
    ],

    "creative": [
        "в тебе есть запрос что-то строить и собирать",
        "сейчас тебе подходит творческая свобода",
        "хочется самому создавать, а не только проходить",
        "тебе важно выражаться через игру",
        "сейчас лучше заходит режим конструктора",
    ],

    "dark": [
        "сегодня тебя не отпугивает мрак",
        "тянет в более холодную и тёмную сторону",
        "хочется чего-то более тяжёлого по настроению",
        "тебе комфортен более мрачный тон",
        "сейчас ты готов к более жёсткой атмосфере",
    ],

    "emotional": [
        "тебе нужен не просто процесс, а внутренний отклик",
        "сейчас тебя цепляют игры с эмоцией",
        "важно что-то почувствовать, а не просто поиграть",
        "тебе нужен эмоциональный контакт с игрой",
        "сейчас хочется, чтобы игра оставляла след",
    ],

    "exploration": [
        "хочется блуждать и открывать",
        "тебе нужен мир, а не просто набор механик",
        "важен сам процесс исследования",
        "тебе интересно находить, а не только выполнять",
        "сейчас тебе нужен простор для открытия",
    ],

    "fast": [
        "тебе нужен темп",
        "сегодня хочется скорости и движения",
        "важно, чтобы игра не тормозила",
        "тебе нужен быстрый отклик и динамика",
        "сейчас хочется активного геймплея без пауз",
    ],

    "flow_state": [
        "ты хочешь войти в поток",
        "сегодня тебе нужен игровой транс",
        "важно потеряться во времени во время игры",
        "тебе нужен непрерывный, затягивающий процесс",
        "сейчас хочется состояния, где всё идёт само",
    ],

    "hardcore": [
        "есть настроение на серьёзный вызов",
        "сегодня тебя не пугает боль ради кайфа",
        "хочется преодолевать, а не просто играть",
        "тебе нужен челлендж, который требует усилий",
        "сейчас важнее сложность, чем комфорт",
    ],

    "lonely": [
        "в ответах чувствуется одиночный вайб",
        "сегодня игра должна разговаривать с тобой один на один",
        "хочется уединённого опыта",
        "тебе сейчас комфортнее быть внутри игры в одиночку",
        "важно личное, тихое взаимодействие с игрой",
    ],

    "long_play": [
        "тебе нужен не короткий заход, а глубокое погружение",
        "сегодня хочется провалиться надолго",
        "важно, чтобы игра держала долго",
        "ты готов вкладываться во время и процесс",
        "сейчас хочется длинного, насыщенного опыта",
    ],

    "mindless_fun": [
        "нужен чистый кайф без перегруза",
        "сегодня лучше работает прямое удовольствие от процесса",
        "хочется играть без лишних мыслей",
        "тебе нужен лёгкий, интуитивный геймплей",
        "сейчас важнее фан, чем глубина",
    ],

    "nostalgic": [
        "внутри есть запрос на знакомое чувство",
        "сегодня ностальгия ложится особенно метко",
        "хочется вернуться в знакомые ощущения",
        "тебе важен вайб старых впечатлений",
        "сейчас тянет к чему-то родному по духу",
    ],

    "power_fantasy": [
        "тебе хочется почувствовать силу",
        "сегодня заходит ощущение контроля и мощи",
        "важно доминировать над ситуацией",
        "тебе нужно ощущение превосходства",
        "сейчас хочется быть тем, кто решает всё",
    ],

    "relax_music": [
        "тебе нужен мягкий аудиовизуальный вайб",
        "сегодня хочется расслабляться через музыку и ритм",
        "важно, как игра звучит и ощущается",
        "тебе нужен почти медитативный опыт",
        "сейчас хочется синхронизации с ритмом",
    ],

    "sandbox": [
        "тебе подходит свобода без жёстких рамок",
        "сегодня хочется самому задавать игру",
        "важно отсутствие строгих ограничений",
        "тебе нужен простор для своих решений",
        "сейчас ты не хочешь, чтобы тебя вели за руку",
    ],

    "shooting": [
        "тебе нужно что-то более прямое и боевое",
        "сегодня хочется решать вопросы нажатием кнопок",
        "нужен активный и понятный экшен",
        "тебе важно быстрое взаимодействие с игрой",
        "сейчас хочется чёткого и прямого геймплея",
    ],

    "skill_based": [
        "тебя заводит ощущение мастерства",
        "сегодня важен личный скилл, а не только контент",
        "хочется расти через игру",
        "тебе важно чувствовать прогресс в умении",
        "сейчас решает то, насколько хорошо ты играешь",
    ],

    "solo": [
        "игра должна держать тебя без компании",
        "сегодня тебе нужен одиночный опыт",
        "важно не зависеть от других игроков",
        "тебе комфортнее играть самому",
        "сейчас хочется уйти с головой от остального мира в новое путешествие",
    ],

    "story": [
        "тебе нужна история, а не просто бездумная механика",
        "сейчас хочется, чтобы игра что-то рассказывала",
        "важен сюжет и развитие событий",
        "тебе нужен нарратив, а не только геймплей",
        "сейчас хочется прожить историю",
    ],

    "strategy": [
        "тебе хочется думать и планировать",
        "сегодня хочется не суеты, а контроля",
        "важно принимать продуманные решения",
        "тебе нужен более тактический подход",
        "сейчас ты хочешь управлять процессом, а не реагировать",
    ],

    "survival": [
        "тебе подходит давление и борьба за ресурсы",
        "сейчас в тебе есть тяга к выживанию",
        "хочется напряжения и риска",
        "важно ощущение нехватки и борьбы",
        "сейчас тебе интересен режим постоянного давления",
    
    ],

    "weird": [
        "можно позволить себе странности",
        "сегодня тебя тянет к не самому очевидному выбору",
        "хочется чего-то нестандартного",
        "тебе интересны необычные ощущения",
        "сейчас ты открыт к экспериментам",
    ],
}

EXPLANATION_OPENERS = [
    "По твоим ответам получился такой игровой профиль.",
    "Я постарался поймать не жанр, а именно твой сегодняшний настрой.",
    "Здесь сработал не случайный выбор, а поиск по состоянию.",
    "Твой вайб считался в конкретику.",
    "Я собрал твой запрос в цельную картину.",
    "По твоим ответам вырисовался довольно чёткий профиль.",
    "Я ориентировался не только на предпочтения, но и на настроение.",
    "Твои ответы сложились в понятное направление.",
    "Я отталкивался от того, что тебе сейчас хочется.",
    "Здесь важнее состояние, чем просто жанр.",
    "Я собрал из твоих ответов общую картину.",
    "Похоже, ты сейчас ищешь конкретный тип ощущений.",
    "Я постарался прочитать между строк твоих ответов.",
    "Картина по тебе сложилась почти ясная, хотя что-то ещё предстоит узнать..",
    "На основе твоих ответов сформировался интересный профиль предпочтений.",
    "Я сопоставил твои ответы и выделил ключевые критерии.",
    "Ответы дали достаточно данных для точного подбора.",
    "Я проанализировал твои ответы и выделил основные ориентиры.",
    "По совокупности факторов вырисовалась чёткая картина."
]

EXPLANATION_CLOSERS = [
    "Поэтому именно эта игра сейчас выглядит той самой.",
    "Так что из доступного именно эта игра легла в твой ритм лучше всего.",
    "Поэтому это не просто рекомендация, а довольно личное попадание.",
    "Из всех вариантов именно она держит нужный тебе баланс.",
    "Здесь всё складывается в твою сторону.",
    "Прям чувствуется, что тебе должно зайти.",
    "Сейчас это выглядит как оптимальный выбор под твой профиль.",
    "По совокупности факторов она выигрывает у остальных.",
    "Это наиболее релевантная рекомендация из всех возможных.",
    "В итоге она сейчас максимально точно закрывает твой запрос.",
    "По ощущениям, это как раз тот вариант, который ты искал.",
    "Поэтому выбор в её сторону выглядит самым логичным.",
    "Судя по твоим ответам, она подходит лучше остальных.",
    "Именно она сейчас совпадает с тем, что тебе хочется.",
    "Так что это не случайный выбор — она реально тебе зайдёт.",
    "Поэтому она сейчас выглядит наиболее точным попаданием.",
]


def pick_random_questions(count: int = QUESTION_COUNT) -> list[dict]:
    return random.sample(GAME_PERSONAL_QUESTIONS, k=min(count, len(GAME_PERSONAL_QUESTIONS)))


def get_question(question_id: str) -> dict:
    return QUESTION_BY_ID[question_id]


def accumulate_answer_weights(answer_history: list[dict]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)

    for answer in answer_history:
        answer_data = get_question(answer["question_id"])["answers"][answer["answer_index"]]
        for tag, value in answer_data["weights"].items():
            weights[tag] += value

    return dict(weights)


def build_preference_profile(user_id: int) -> tuple[dict[str, float], dict[str, float], set[str]]:
    games = load_games(include_premium_collection_only=False)
    by_title = {game["title"]: game for game in games}

    favorite_titles = {title for (title,) in get_user_favorites(user_id, "game")}
    liked_titles = set(get_user_rated_content(user_id, "game", value=1))
    disliked_titles = set(get_user_rated_content(user_id, "game", value=-1))

    positive_weights: dict[str, float] = defaultdict(float)
    negative_weights: dict[str, float] = defaultdict(float)

    for title in favorite_titles:
        game = by_title.get(title)
        if game:
            for tag in game.get("tags", []):
                positive_weights[tag] += 1.8

    for title in liked_titles:
        game = by_title.get(title)
        if game:
            for tag in game.get("tags", []):
                positive_weights[tag] += 1.2

    for title in disliked_titles:
        game = by_title.get(title)
        if game:
            for tag in game.get("tags", []):
                negative_weights[tag] += 1.3

    return dict(positive_weights), dict(negative_weights), disliked_titles | favorite_titles | liked_titles


def score_game(
    game: dict,
    answer_weights: dict[str, float],
    positive_profile: dict[str, float],
    negative_profile: dict[str, float],
) -> tuple[float, list[tuple[str, float]]]:
    tag_scores: list[tuple[str, float]] = []
    score = 0.0

    for tag in game.get("tags", []):
        tag_score = answer_weights.get(tag, 0.0)
        tag_score += positive_profile.get(tag, 0.0) * 0.8
        tag_score -= negative_profile.get(tag, 0.0) * 0.9

        if tag == "mr600_choice":
            tag_score += 0.4

        if tag_score:
            tag_scores.append((tag, tag_score))
            score += tag_score

    score += random.uniform(0, 0.35)
    tag_scores.sort(key=lambda item: item[1], reverse=True)
    return score, tag_scores


def build_explanation(tag_scores: list[tuple[str, float]]) -> str:
    top_tags = [tag for tag, score in tag_scores if score > 0][:3]
    fragments = []

    for tag in top_tags:
        options = TAG_EXPLANATIONS.get(tag)
        if options:
            fragments.append(random.choice(options))

    if not fragments:
        fragments.append("тебе нужен точный игровой вайб, а не просто случайный тайтл")

    opener = random.choice(EXPLANATION_OPENERS)
    closer = random.choice(EXPLANATION_CLOSERS)

    if len(fragments) == 1:
        middle = fragments[0]
    elif len(fragments) == 2:
        middle = f"{fragments[0]}, и одновременно {fragments[1]}"
    else:
        middle = f"{fragments[0]}, {fragments[1]} и {fragments[2]}"

    return f"✨ <b><i>{opener} Похоже, {middle}. {closer}</i></b>"


def recommend_games(
    user_id: int,
    answer_history: list[dict],
    excluded_titles: set[str] | None = None,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[dict]:
    games = load_games(platform=platform)
    answer_weights = accumulate_answer_weights(answer_history)
    positive_profile, negative_profile, blocked_titles = build_preference_profile(user_id)
    blocked_titles |= excluded_titles or set()
    blocked_titles |= get_recently_seen_titles(user_id, "game")

    scored_games = []
    fallback_games = []

    for game in games:
        if game["title"] in blocked_titles:
            continue

        score, tag_scores = score_game(game, answer_weights, positive_profile, negative_profile)
        fallback_games.append((score, tag_scores, game))

        if score > 0:
            scored_games.append((score, tag_scores, game))

    candidates = scored_games or fallback_games
    candidates.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "game": game,
            "score": score,
            "explanation": build_explanation(tag_scores),
        }
        for score, tag_scores, game in candidates[:5]
    ]

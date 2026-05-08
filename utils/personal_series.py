import random
from collections import defaultdict

from data.series import load_series
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_favorites, get_user_rated_content

QUESTION_COUNT = 4
ANSWER_LABELS = ["0%", "50%", "75%", "600%"]


def _answers(weight_sets: list[dict[str, float]]) -> list[dict]:
    return [
        {"text": ANSWER_LABELS[index], "weights": weights}
        for index, weights in enumerate(weight_sets)
    ]


SERIES_PERSONAL_QUESTIONS = [
    {"id": "s01", "text": "Хочется ли надолго провалиться в историю?", "answers": _answers([{"short_series": 2}, {"long_immersion": 2}, {"long_immersion": 3, "drama": 1}, {"long_immersion": 4, "drama": 2}])},
    {"id": "s02", "text": "Нужен ли тебе сериал с сильной драмой?", "answers": _answers([{"comedy": 2, "relax_chill": 1}, {"drama": 1}, {"drama": 3, "life_stories": 1}, {"drama": 4, "psychological": 2}])},
    {"id": "s03", "text": "Тянет ли к мрачной атмосфере?", "answers": _answers([{"relax_chill": 2}, {"dark": 1, "slow_burn": 1}, {"dark": 3, "psychological": 1}, {"dark": 4, "psychological": 2, "crime": 1}])},
    {"id": "s04", "text": "Хочется ли закрученного сюжета?", "answers": _answers([{"life_stories": 1}, {"twisted_plot": 2}, {"twisted_plot": 3, "mind_blown": 1}, {"twisted_plot": 4, "mind_blown": 2, "psychological": 1}])},
    {"id": "s05", "text": "Нужен ли сериал, который будет уютным фоном?", "answers": _answers([{"crime": 1}, {"relax_chill": 2, "comedy": 1}, {"relax_chill": 3, "life_stories": 1}, {"relax_chill": 4, "comedy": 2}])},
    {"id": "s06", "text": "Тянет ли к психологическому напряжению?", "answers": _answers([{"comedy": 1}, {"psychological": 2}, {"psychological": 3, "dark": 1}, {"psychological": 4, "twisted_plot": 2}])},
    {"id": "s07", "text": "Хочется ли чего-то криминального?", "answers": _answers([{"life_stories": 1}, {"crime": 2}, {"crime": 3, "realistic": 1}, {"crime": 4, "dark": 2, "twisted_plot": 1}])},
    {"id": "s08", "text": "Нужен ли сейчас сериал с жизненными историями?", "answers": _answers([{"mind_blown": 1}, {"life_stories": 2}, {"life_stories": 3, "drama": 1}, {"life_stories": 4, "drama": 2, "realistic": 1}])},
    {"id": "s09", "text": "Насколько ты сейчас готов к slow burn?", "answers": _answers([{"action_speed": 2}, {"slow_burn": 2}, {"slow_burn": 3, "atmospheric": 1}, {"slow_burn": 4, "psychological": 2}])},
    {"id": "s10", "text": "Хочется ли легкости и юмора?", "answers": _answers([{"dark": 1}, {"comedy": 2, "relax_chill": 1}, {"comedy": 3, "relax_chill": 2}, {"comedy": 4, "relax_chill": 3}])},
    {"id": "s11", "text": "Нужен ли сериал, который реально удивляет?", "answers": _answers([{"classic_must_watch": 1}, {"mind_blown": 2}, {"mind_blown": 3, "twisted_plot": 1}, {"mind_blown": 4, "twisted_plot": 2}])},
    {"id": "s12", "text": "Насколько тебе сейчас нужен драйв, а не густая атмосфера?", "answers": _answers([{"atmospheric": 3}, {"action_speed": 1, "atmospheric": 1}, {"action_speed": 3, "twisted_plot": 1}, {"action_speed": 4, "crime": 1}])},
    {"id": "s13", "text": "Хочется ли короткого сериала без длинного марафона?", "answers": _answers([{"long_immersion": 2}, {"short_series": 2}, {"short_series": 3, "twisted_plot": 1}, {"short_series": 4, "mind_blown": 1}])},
    {"id": "s14", "text": "Нужен ли тебе сериал, который выглядит как must-watch?", "answers": _answers([{"hidden_gems": 1}, {"classic_must_watch": 2}, {"classic_must_watch": 3, "drama": 1}, {"classic_must_watch": 4, "long_immersion": 2}])},
    {"id": "s15", "text": "Насколько тебя сейчас тянет к скрытым бриллиантам, а не к очевидному хиту?", "answers": _answers([{"classic_must_watch": 2}, {"hidden_gems": 2}, {"hidden_gems": 3, "atmospheric": 1}, {"hidden_gems": 4, "mr600_choice": 2}])},
    {"id": "s16", "text": "Хочется ли монстров, нечисти или чего-то опасного?", "answers": _answers([{"life_stories": 1}, {"monsters": 2}, {"monsters": 3, "dark": 1}, {"monsters": 4, "dark": 2, "action_speed": 1}])},
    {"id": "s17", "text": "Нужен ли сейчас реализм?", "answers": _answers([{"mind_blown": 1}, {"realistic": 2}, {"realistic": 3, "drama": 1}, {"realistic": 4, "crime": 2, "life_stories": 1}])},
    {"id": "s18", "text": "Хочется ли сериала, который прожует тебе мозг?", "answers": _answers([{"relax_chill": 1}, {"mind_blown": 2}, {"mind_blown": 3, "psychological": 1}, {"mind_blown": 4, "psychological": 2, "twisted_plot": 1}])},
    {"id": "s19", "text": "Тебе нужен сериал для долгой привязанности к героям?", "answers": _answers([{"short_series": 1}, {"drama": 2, "long_immersion": 1}, {"long_immersion": 3, "life_stories": 1}, {"long_immersion": 4, "drama": 2, "life_stories": 1}])},
    {"id": "s20", "text": "Хочется ли плотного сюжетного крючка с первой серии?", "answers": _answers([{"slow_burn": 2}, {"twisted_plot": 2}, {"twisted_plot": 3, "action_speed": 1}, {"twisted_plot": 4, "action_speed": 2}])},
    {"id": "s21", "text": "Нужен ли сериал, который можно смотреть запоем?", "answers": _answers([{"short_series": 1}, {"long_immersion": 2}, {"long_immersion": 3, "crime": 1}, {"long_immersion": 4, "twisted_plot": 2}])},
    {"id": "s22", "text": "Насколько тебя сейчас тянет к человечному, а не к концептуальному?", "answers": _answers([{"mind_blown": 2}, {"life_stories": 2}, {"life_stories": 3, "drama": 1}, {"life_stories": 4, "drama": 2}])},
    {"id": "s23", "text": "Хочется ли сериал, который будет не расслаблять, а держать?", "answers": _answers([{"relax_chill": 2}, {"psychological": 2}, {"psychological": 3, "crime": 1}, {"psychological": 4, "dark": 2, "twisted_plot": 1}])},
    {"id": "s24", "text": "Нужна ли атмосфера важнее экшена?", "answers": _answers([{"action_speed": 2}, {"atmospheric": 2}, {"atmospheric": 3, "slow_burn": 1}, {"atmospheric": 4, "slow_burn": 2, "dark": 1}])},
    {"id": "s25", "text": "Насколько тебе нужен сериал, который почувствуется твоим личным хитом?", "answers": _answers([{"classic_must_watch": 2}, {"mr600_choice": 2}, {"mr600_choice": 3, "hidden_gems": 1}, {"mr600_choice": 4, "hidden_gems": 2}])},
    {"id": "s26", "text": "Нужен ли более взрослый и тяжелый вайб?", "answers": _answers([{"comedy": 1}, {"drama": 2}, {"drama": 3, "dark": 1}, {"drama": 4, "dark": 2, "realistic": 1}])},
    {"id": "s27", "text": "Насколько тебе сейчас ближе тревожный сериал, чем уютный?", "answers": _answers([{"relax_chill": 3}, {"relax_chill": 2, "dark": 1}, {"dark": 3, "psychological": 1}, {"dark": 4, "psychological": 2}])},
    {"id": "s28", "text": "Нужен ли сериал, который будет обсуждаться потом в голове?", "answers": _answers([{"comedy": 1}, {"mind_blown": 2}, {"mind_blown": 3, "psychological": 1}, {"mind_blown": 4, "twisted_plot": 2, "dark": 1}])},
    {"id": "s29", "text": "Насколько тебе сейчас хочется чего-то масштабного, а не локального?", "answers": _answers([{"life_stories": 2}, {"long_immersion": 2}, {"long_immersion": 3, "classic_must_watch": 1}, {"long_immersion": 4, "classic_must_watch": 2, "monsters": 1}])},
    {"id": "s30", "text": "Нужен ли сериал, который будет казаться очень личным попаданием сегодня?", "answers": _answers([{"classic_must_watch": 1}, {"hidden_gems": 2}, {"hidden_gems": 3, "mr600_choice": 1}, {"hidden_gems": 4, "mr600_choice": 2, "psychological": 1}])},
]

QUESTION_BY_ID = {question["id"]: question for question in SERIES_PERSONAL_QUESTIONS}

TAG_EXPLANATIONS = {
    "action_speed": [
        "тебе нужен темп, а не медленное раскачивание",
        "сегодня хочется более бодрого хода событий",
        "важно, чтобы сериал не тормозил",
        "тебе нужен быстрый ритм и постоянное движение",
        "сейчас хочется динамики без пауз",
    ],

    "atmospheric": [
        "тебе важна густая атмосфера",
        "сегодня тебя держит именно настроение сериала",
        "хочется раствориться в мире сериала",
        "тебе важнее ощущение, чем события",
        "сейчас ты смотришь ради вайба, а не только ради сюжета",
    ],

    "classic_must_watch": [
        "хочется чего-то большого и проверенного",
        "сегодня тянет к по-настоящему статусному сериалу",
        "хочется посмотреть то, что уже стало классикой",
        "тебе важен масштаб и признание",
        "сейчас ты ищешь нечто культовое",
    ],

    "comedy": [
        "тебе нужен более легкий тон",
        "сейчас юмор тебе явно не мешает",
        "хочется разгрузиться через смех",
        "тебе нужен сериал, который не будет давить",
        "сейчас важнее лёгкость, чем напряжение",
    ],

    "crime": [
        "тебя тянет к криминальному напряжению",
        "сегодня интереснее грязные схемы и риск",
        "хочется интриг и серых зон",
        "тебе интересны люди на грани закона",
        "сейчас тебя цепляют истории про риск и последствия",
    ],

    "dark": [
        "сейчас тебя не пугает темнота",
        "тянет в более мрачную сторону",
        "хочется более тяжёлой атмосферы",
        "тебе комфортен холодный тон",
        "сейчас ты готов к более жёсткому настроению",
    ],

    "drama": [
        "тебе нужен человеческий нерв",
        "сегодня хочется проживать, а не просто наблюдать",
        "важны эмоции и конфликты",
        "тебе интересны отношения и внутренние переживания",
        "сейчас хочется сильного человеческого слоя",
    ],

    "hidden_gems": [
        "тебе можно предложить что-то менее очевидное",
        "сегодня хочется найти свой личный бриллиант",
        "хочется уйти от мейнстрима",
        "тебе интересны недооценённые вещи",
        "сейчас ты открыт к неожиданным находкам",
    ],

    "life_stories": [
        "тебе близки истории про людей",
        "сейчас хочется более жизненного материала",
        "важно ощущение реальной жизни",
        "тебе интересны повседневные судьбы",
        "сейчас хочется чего-то приземлённого и настоящего",
    ],

    "long_immersion": [
        "тебе нужен длинный заход и полное погружение",
        "сегодня хочется провалиться в мир надолго",
        "важно, чтобы сериал держал долго",
        "ты готов жить в этом мире несколько сезонов",
        "сейчас хочется длительного опыта, а не короткой истории",
    ],

    "mind_blown": [
        "хочется, чтобы сериал остался в голове",
        "сейчас тебе заходят вещи с эффектом 'что это было'",
        "нужен сильный эффект после просмотра",
        "тебе важны неожиданные идеи и повороты",
        "сейчас хочется, чтобы сериал ломал ожидания",
    ],

    "monsters": [
        "не пугает более опасный и дикий вайб",
        "сегодня хочется монстров и внешней угрозы",
        "хочется явной опасности",
        "тебе интересен конфликт с чем-то нечеловеческим",
        "сейчас нужен внешний источник напряжения",
    ],

    "psychological": [
        "тебе интереснее внутреннее напряжение",
        "сейчас тебе подходит психологическое давление",
        "важны игры разума и мотивации",
        "тебе интересны внутренние конфликты",
        "сейчас ты хочешь не действия, а напряжения внутри",
    ],

    "realistic": [
        "сегодня лучше работает реализм",
        "тебе важнее приземленная правда, чем концепт",
        "хочется верить в происходящее",
        "тебе важна жизненная достоверность",
        "сейчас ты ищешь что-то максимально близкое к реальности",
    ],

    "relax_chill": [
        "нужен мягкий режим просмотра",
        "сейчас хочется сериала, который не будет давить",
        "хочется расслабленного просмотра",
        "тебе нужен фон, который не перегружает",
        "сейчас важен комфорт, а не напряжение",
    ],

    "short_series": [
        "хочется более короткой дистанции",
        "сегодня лучше заходит компактный сериал",
        "важно быстро дойти до финала",
        "тебе нужен завершённый опыт без растягивания",
        "сейчас формат должен быть плотным",
    ],

    "slow_burn": [
        "ты готов к медленному прогреву",
        "сейчас тебя не смущает неспешный разгон",
        "тебе важна постепенная раскрутка",
        "хочется, чтобы сериал раскрывался со временем",
        "сейчас ты готов инвестировать внимание в развитие",
    ],

    "twisted_plot": [
        "нужен сюжетный крючок и повороты",
        "сегодня хочется, чтобы история тебя водила за нос",
        "важны неожиданные развороты",
        "тебе нравится, когда сюжет играет с ожиданиями",
        "сейчас хочется интриги и нестабильности",
    ],
}

EXPLANATION_OPENERS = [
    "По ответам сложился очень конкретный сериальный вайб.",
    "Я поймал не просто жанр, а твой сегодняшний ритм просмотра.",
    "Здесь считывается довольно ясный запрос по состоянию.",
    "Это не случайный сериал, а вполне точное попадание по твоему настроению.",
    "Кажется, я уловил твой сериальный вайб.",
    "Похоже, сейчас тебе нужен определённый тип сериала.",
    "Я примерно понял, в каком ты сейчас настроении для просмотра.",
    "Судя по ответам, ты сейчас ищешь не просто сериал, а ощущение.",
    "Картина по тебе сложилась довольно чётко.",
    "Я постарался прочитать между строк твоих ответов.",
    "Если опираться на твои ответы, вырисовывается примерно такая картина.",
    "Я попробовал собрать из твоих ответов общее направление.",
    "Судя по ответам, можно предположить такой вектор просмотра.",
    "Картина получилась немного нестандартной.",
    "Здесь вышел довольно неожиданный, но логичный результат.",
    "Похоже, ты сейчас ищешь что-то более точечное, чем кажется.",
]

EXPLANATION_CLOSERS = [
    "Поэтому именно этот сериал сейчас выглядит самым точным вариантом.",
    "Так что из доступных вариантов именно он лучше всего попадает в твой ритм.",
    "Из всего списка именно он держит нужный тебе баланс.",
    "Поэтому выбор получился не случайным, а довольно личным.",
    "В итоге он сейчас максимально точно закрывает твой запрос.",
    "По ощущениям, это как раз тот сериал, который тебе сейчас нужен.",
    "Поэтому именно к нему сейчас логично прийти.",
    "Судя по твоим ответам, он подходит лучше остальных.",
    "Именно он сейчас совпадает с тем, что тебе хочется посмотреть.",
    "Так что это не случайный выбор — он реально в твоём вайбе.",
    "Короче, это прям твой сериал сейчас.",
    "Если коротко — это оно.",
    "Тут очень чёткое совпадение с твоим настроением.",
    "Очень похоже на идеальный матч под тебя.",
    "Почти стопроцентное попадание.",
    "Это как будто под твой текущий вайб снято.",
    "Здесь всё сходится под твое состояние.",
    "Один из тех случаев, когда сложно остановиться после первой серии.",
    "Он очень точно ложится в формат «включить и залипнуть».",
    "Это тот тип сериала, который быстро затягивает.",
    "С высокой вероятностью он зайдёт тебе уже с первых серий.",
    "Он аккуратно попадает в твой текущий запрос.",
    "Здесь совпадает и темп, и содержание.",
    "Это наиболее выверенный вариант под твое состояние.",
    "Если опираться на твои ответы, он выглядит наиболее подходящим.",
    "С большой вероятностью это именно то, что тебе сейчас зайдёт.",
    "Это, пожалуй, самый близкий вариант к тому, что ты описал.",
]


def pick_random_questions(count: int = QUESTION_COUNT) -> list[dict]:
    return random.sample(SERIES_PERSONAL_QUESTIONS, k=min(count, len(SERIES_PERSONAL_QUESTIONS)))


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
    series_list = load_series(include_premium_collection_only=False)
    by_title = {series["title"]: series for series in series_list}

    favorite_titles = {title for (title,) in get_user_favorites(user_id, "series")}
    liked_titles = set(get_user_rated_content(user_id, "series", value=1))
    disliked_titles = set(get_user_rated_content(user_id, "series", value=-1))

    positive_weights: dict[str, float] = defaultdict(float)
    negative_weights: dict[str, float] = defaultdict(float)

    for title in favorite_titles:
        series = by_title.get(title)
        if series:
            for tag in series.get("tags", []):
                positive_weights[tag] += 1.8

    for title in liked_titles:
        series = by_title.get(title)
        if series:
            for tag in series.get("tags", []):
                positive_weights[tag] += 1.2

    for title in disliked_titles:
        series = by_title.get(title)
        if series:
            for tag in series.get("tags", []):
                negative_weights[tag] += 1.3

    return dict(positive_weights), dict(negative_weights), disliked_titles | favorite_titles | liked_titles


def score_series(
    series: dict,
    answer_weights: dict[str, float],
    positive_profile: dict[str, float],
    negative_profile: dict[str, float],
) -> tuple[float, list[tuple[str, float]]]:
    tag_scores: list[tuple[str, float]] = []
    score = 0.0

    for tag in series.get("tags", []):
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
        fragments.append("тебе нужен не просто сериал, а точное попадание по состоянию")

    opener = random.choice(EXPLANATION_OPENERS)
    closer = random.choice(EXPLANATION_CLOSERS)

    if len(fragments) == 1:
        middle = fragments[0]
    elif len(fragments) == 2:
        middle = f"{fragments[0]}, и одновременно {fragments[1]}"
    else:
        middle = f"{fragments[0]}, {fragments[1]} и {fragments[2]}"

    return f"✨ <b><i>{opener} Похоже, {middle}. {closer}</i></b>"


def recommend_series(
    user_id: int,
    answer_history: list[dict],
    excluded_titles: set[str] | None = None,
) -> list[dict]:
    series_list = load_series()
    answer_weights = accumulate_answer_weights(answer_history)
    positive_profile, negative_profile, blocked_titles = build_preference_profile(user_id)
    blocked_titles |= excluded_titles or set()
    blocked_titles |= get_recently_seen_titles(user_id, "series")

    scored_series = []
    fallback_series = []

    for series in series_list:
        if series["title"] in blocked_titles:
            continue

        score, tag_scores = score_series(series, answer_weights, positive_profile, negative_profile)
        fallback_series.append((score, tag_scores, series))

        if score > 0:
            scored_series.append((score, tag_scores, series))

    candidates = scored_series or fallback_series
    candidates.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "series": series,
            "score": score,
            "explanation": build_explanation(tag_scores),
        }
        for score, tag_scores, series in candidates[:5]
    ]

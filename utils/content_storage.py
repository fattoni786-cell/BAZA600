import json

FILES = {
    "movie": "data/movies.json",
    "series": "data/series.json",
    "game": "data/games.json",
    "book": "data/books.json",
}

def save_content(item: dict):
    path = FILES[item["type"]]

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    data.append(item)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

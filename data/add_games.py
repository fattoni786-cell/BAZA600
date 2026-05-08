import json
import random
from pathlib import Path

DATA_PATH = Path("data/games.json")


def load_games():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_game(tag: str):
    games = load_games()
    filtered = [g for g in games if tag in g.get("tags", [])]
    return random.choice(filtered if filtered else games)

import random

def get_random_vibes(allowed_vibes: list[str], count: int = 5):
    if len(allowed_vibes) <= count:
        return allowed_vibes
    return random.sample(allowed_vibes, k=count)

import random


def choose_random_action(capacities: list[int], rng: random.Random) -> int:
    available = [idx for idx, cap in enumerate(capacities) if cap > 0]
    if available:
        return rng.choice(available)
    return rng.randrange(len(capacities))


from dataclasses import dataclass


@dataclass
class HeuristicDecision:
    action: int
    used_overload: bool


def choose_action(
    *,
    capacities: list[int],
    waits: list[float],
    travel_times: list[float],
    overload_penalty: float,
) -> HeuristicDecision:
    # Prefer centres with available capacity; fallback to least loaded when all are full.
    best_idx = 0
    best_score = float("inf")
    used_overload = False

    has_capacity = any(cap > 0 for cap in capacities)
    for idx, (cap, wait, travel) in enumerate(zip(capacities, waits, travel_times)):
        score = (travel + wait) / max(cap, 1)
        if cap <= 0:
            score += overload_penalty
        if has_capacity and cap <= 0:
            continue
        if score < best_score:
            best_score = score
            best_idx = idx

    if not has_capacity:
        used_overload = True

    return HeuristicDecision(action=best_idx, used_overload=used_overload)

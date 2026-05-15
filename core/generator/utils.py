# -*- coding: utf-8 -*-

import random


def weighted_choice(values, fallback):
    return random.choice(values) if values else fallback


def build_allowed_notes(root, scale, register_range):
    low, high = register_range
    return [pitch for pitch in [root + octv * 12 + interval for octv in range(-1, 3) for interval in scale] if low <= pitch <= high]


def choose_next_pitch(last_pitch, allowed, jump_limit):
    if last_pitch is None:
        return random.choice(allowed)

    if not allowed:
        return last_pitch

    low = min(allowed)
    high = max(allowed)
    center = (low + high) / 2.0
    nearby = [pitch for pitch in allowed if abs(pitch - last_pitch) <= jump_limit]
    if not nearby:
        nearby = list(allowed)

    if random.random() < 0.12:
        far = [pitch for pitch in allowed if abs(pitch - last_pitch) > jump_limit and abs(pitch - last_pitch) <= (jump_limit + 6)]
        if far:
            far_weights = [1.0 / (1.0 + abs(p - center)) for p in far]
            return random.choices(far, weights=far_weights, k=1)[0]

    weights = []
    for pitch in nearby:
        delta = pitch - last_pitch
        w = 1.0 / (1.0 + abs(delta))
        if (last_pitch > center and delta < 0) or (last_pitch < center and delta > 0):
            w *= 1.35
        if delta == 0:
            w *= 0.6
        if pitch <= low + 1 or pitch >= high - 1:
            w *= 0.85
        weights.append(w)
    return random.choices(nearby, weights=weights, k=1)[0]


def choose_next_pitch_classic(last_pitch, allowed, jump_limit):
    if last_pitch is None:
        return random.choice(allowed)
    nearby = [pitch for pitch in allowed if abs(pitch - last_pitch) <= jump_limit]
    if nearby and random.random() < 0.8:
        return random.choice(nearby)
    return random.choice(allowed)


def merge_unique(values):
    return list(dict.fromkeys(values))


def solo_theme_mods(theme_name: str, theme_profile: dict) -> dict:
    theme_l = str(theme_name or "").strip().lower()
    tp = theme_profile or {}
    density_mult = float(tp.get("density", 1.0))
    register_shift = int(tp.get("register_shift", 0))
    dur_mode = "normal"
    run_mult = 1.0
    center_steps = 0

    if "dark" in theme_l or "evil" in theme_l or "horror" in theme_l:
        density_mult *= 0.80
        register_shift -= 4
        dur_mode = "long"
        run_mult *= 0.75
        center_steps -= 1
    if "rainy" in theme_l or "dreamy" in theme_l or "sad" in theme_l or "lofi" in theme_l:
        density_mult *= 0.86
        register_shift -= 1
        if dur_mode == "normal":
            dur_mode = "long"
        run_mult *= 0.85
    if "jazz" in theme_l or "soul" in theme_l or "neo" in theme_l:
        density_mult *= 1.05
        register_shift += 2
        run_mult *= 1.10
        center_steps += 1
    if "aggressive" in theme_l or "hard" in theme_l or "street" in theme_l or "trap" in theme_l:
        density_mult *= 1.12
        if dur_mode == "normal":
            dur_mode = "short"
        run_mult *= 1.18

    density_mult = max(0.55, min(1.35, density_mult))
    run_mult = max(0.55, min(1.55, run_mult))
    register_shift = int(max(-12, min(12, register_shift)))
    center_steps = int(max(-3, min(3, center_steps)))
    return {"density_mult": density_mult, "register_shift": register_shift, "dur_mode": dur_mode, "run_mult": run_mult, "center_steps": center_steps}


def solo_duration_pool(theme_profile: dict, dur_mode: str, base: list[float]) -> list[float]:
    tp = theme_profile or {}
    pool = merge_unique([float(x) for x in (base or [])] + [float(x) for x in (tp.get("durations") or [])])
    pool = [p for p in pool if p > 0]
    if not pool:
        pool = [0.25, 0.5, 1.0]
    dur_mode = str(dur_mode or "normal").strip().lower()
    if dur_mode.startswith("long"):
        preferred = [p for p in pool if p >= 0.5] or pool
        preferred = merge_unique(preferred + [1.5, 2.0])
        return [p for p in preferred if p <= 4.0]
    if dur_mode.startswith("short"):
        preferred = [p for p in pool if p <= 0.5] or pool
        preferred = merge_unique(preferred + [0.25])
        return [p for p in preferred if p <= 2.0]
    return [p for p in pool if p <= 4.0]

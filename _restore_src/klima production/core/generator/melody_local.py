# -*- coding: utf-8 -*-

import random

import numpy as np

from core.generator.theme_profiles import DEFAULT_PROFILE, build_theme_profile, get_producer_profile, split_theme
from core.generator.utils import (
    build_allowed_notes as _build_allowed_notes,
    choose_next_pitch as _choose_next_pitch,
    merge_unique as _merge_unique,
    weighted_choice as _weighted_choice,
)


def smart_generate_classic(num_bars, theme="Freestyle", energy=5):
    producer, theme_name = split_theme(theme)
    producer_profile = get_producer_profile(producer)
    theme_profile = build_theme_profile(theme_name)

    root = random.choice([55, 57, 58, 60, 62]) + theme_profile["register_shift"]
    register_low, register_high = producer_profile["register"]
    register = (max(48, register_low + theme_profile["register_shift"]), min(84, register_high + theme_profile["register_shift"]))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (52, 72))

    motif_length = _weighted_choice(producer_profile["motif"], 2.0)
    step = producer_profile["step"]
    density = min(0.95, producer_profile["density"] * theme_profile["density"] * (0.65 + energy / 12.0))
    swing_amount = producer_profile["swing"] * theme_profile["swing"]
    durations = _merge_unique(producer_profile["durations"] + theme_profile["durations"])
    jump_limit = max(2, producer_profile["jump"] + theme_profile["jump"])
    offbeat_bias = float(producer_profile.get("offbeat_bias", 0.0)) + float(theme_profile.get("offbeat_bias", 0.0) or 0.0)
    cadence_prob = float(producer_profile.get("cadence_prob", DEFAULT_PROFILE.get("cadence_prob", 0.24)))
    variation = float(producer_profile.get("variation", DEFAULT_PROFILE.get("variation", 0.22)))
    variation = max(0.06, min(0.55, variation))

    allowed_sorted = sorted(allowed)
    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    try:
        home_idx = allowed_sorted.index(home_pitch)
    except Exception:
        home_idx = 0
    cadence_candidates = []
    for off in (0, -2, 2, -4, 4):
        if allowed_sorted:
            idx = max(0, min(len(allowed_sorted) - 1, home_idx + off))
            cadence_candidates.append(int(allowed_sorted[idx]))
    cadence_candidates = list(dict.fromkeys(cadence_candidates)) or [int(home_pitch)]

    motif = []
    last_pitch = None
    accent_boost = theme_profile["accent"]
    for t in np.arange(0, motif_length, step):
        strong_beat = abs(t % 1.0) < 0.001
        is_offbeat = (not strong_beat) and (t % 0.5 != 0)
        hit_chance = density + (0.09 if strong_beat else -0.03)
        if is_offbeat:
            hit_chance += offbeat_bias * 0.60
        else:
            hit_chance -= offbeat_bias * 0.30
        if random.random() < max(0.15, min(0.98, hit_chance)):
            if strong_beat and random.random() < cadence_prob:
                pitch = int(random.choice(cadence_candidates))
            else:
                pitch = _choose_next_pitch(last_pitch, allowed, jump_limit)
            duration = _weighted_choice(durations, 0.5)
            velocity = random.randint(68, 102) + (10 if strong_beat else 0) + accent_boost
            swing = swing_amount if (t % 0.5 != 0) else 0.0
            motif.append([float(round(t + swing, 3)), pitch, float(duration), max(1, min(127, velocity))])
            last_pitch = pitch
    if not motif:
        motif.append([0.0, random.choice(allowed), 0.5, 90])

    data = []
    repeats = int(np.ceil((num_bars * 4) / motif_length))
    pitch_mut_chance = max(0.06, min(0.35, 0.10 + variation * 0.45))
    dur_mut_chance = max(0.06, min(0.35, 0.08 + variation * 0.35))
    for bar in range(repeats):
        for note in motif:
            start_time = note[0] + bar * motif_length
            if start_time < num_bars * 4:
                variation_roll = random.random()
                new_pitch = note[1]
                new_duration = note[2]
                if variation_roll < pitch_mut_chance:
                    new_pitch = _choose_next_pitch(int(note[1]), allowed, max(2, jump_limit - 1))
                if variation_roll > 1.0 - dur_mut_chance:
                    new_duration = _weighted_choice(durations, note[2])
                strong_rep = abs(float(note[0]) % 1.0) < 0.001
                if strong_rep and random.random() < (cadence_prob * 0.55):
                    new_pitch = int(random.choice(cadence_candidates))
                data.append([float(round(start_time, 3)), int(new_pitch), float(new_duration), int(note[3])])
    data.sort(key=lambda x: x[0])
    return data

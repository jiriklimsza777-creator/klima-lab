# -*- coding: utf-8 -*-

import random

import numpy as np

from core.generator.theme_profiles import DEFAULT_PROFILE, build_theme_profile, get_producer_profile, split_theme


def chord_generate(num_bars, theme="Freestyle", energy=5):
    producer, theme_name = split_theme(theme)
    producer_profile = get_producer_profile(producer)
    theme_profile = build_theme_profile(theme_name)

    root = random.choice([48, 50, 53, 55, 57, 60]) + max(-5, min(5, theme_profile["register_shift"]))
    chord_step = float(producer_profile.get("chord_step", DEFAULT_PROFILE.get("chord_step", 2.0)))
    chord_complexity = float(producer_profile.get("chord_complexity", DEFAULT_PROFILE.get("chord_complexity", 0.35)))
    chord_arp_prob = float(producer_profile.get("chord_arp_prob", DEFAULT_PROFILE.get("chord_arp_prob", 0.20)))
    chord_step = 1.0 if chord_step <= 1.0 else 2.0
    chord_complexity = max(0.0, min(1.0, chord_complexity))
    chord_arp_prob = max(0.0, min(0.75, chord_arp_prob))

    beat_step = chord_step
    if energy >= 8 and random.random() < 0.60:
        beat_step = 1.0
    if "Dreamy" in theme_name or "Rainy" in theme_name or "Sad" in theme_name:
        beat_step = 2.0

    prog_pool = list(theme_profile.get("progression") or [0, 5, 7, 10])
    if not prog_pool:
        prog_pool = [0, 5, 7, 10]
    progression_steps = [0]
    while len(progression_steps) < 4:
        cand = int(random.choice(prog_pool))
        if chord_complexity >= 0.55 and cand in progression_steps and random.random() < 0.70:
            continue
        progression_steps.append(cand)
    data = []

    def _choose_chord_shape():
        base = list(random.choice(theme_profile.get("chords") or [[0, 3, 7]]))
        base = [int(x) for x in base if isinstance(x, (int, float))]
        base = list(dict.fromkeys(base)) or [0, 3, 7]
        theme_l = theme_name.lower()
        jazzish = ("jazz" in theme_l) or ("soul" in theme_l) or ("neo" in theme_l)
        darkish = ("dark" in theme_l) or ("evil" in theme_l) or ("horror" in theme_l)
        ext_p = 0.18 + (0.55 * chord_complexity) + (0.12 if jazzish else 0.0)
        if darkish:
            ext_p -= 0.05
        ext_p = max(0.0, min(0.85, ext_p))
        if random.random() < ext_p:
            if 10 not in base and 11 not in base:
                base.append(10)
        if random.random() < (ext_p * 0.60):
            if 14 not in base:
                base.append(14)
        if random.random() < (0.08 + 0.22 * chord_complexity):
            if 5 in base and 3 in base and random.random() < 0.6:
                base = [x for x in base if x != 3]
                base.append(5)
        base = sorted(list(dict.fromkeys(int(x) for x in base)))
        if len(base) > 4:
            if 14 in base and 7 in base and len(base) >= 5:
                base = [x for x in base if x != 7]
            if len(base) > 4:
                base = base[:4]
        return base

    def _voice_chord(pitches, prev_center=None):
        pitches = sorted(int(p) for p in pitches)
        if not pitches:
            return []
        low = 40
        high = 80
        target_center = 60 if prev_center is None else int(prev_center)
        voiced = []
        for p in pitches:
            cands = [p - 24, p - 12, p, p + 12, p + 24]
            cands = [c for c in cands if low <= c <= high]
            if not cands:
                continue
            best = min(cands, key=lambda c: abs(int(c) - int(target_center)))
            voiced.append(int(best))
        voiced = sorted(list(dict.fromkeys(voiced)))
        if not voiced:
            return []
        if chord_complexity >= 0.55 and len(voiced) >= 3:
            if voiced[-1] - voiced[-2] <= 2 and voiced[-1] + 12 <= high:
                voiced[-1] = voiced[-1] + 12
                voiced = sorted(list(dict.fromkeys(voiced)))
        return voiced

    prev_center = None
    for idx, start in enumerate(np.arange(0, num_bars * 4, beat_step)):
        prog_root = root + progression_steps[idx % len(progression_steps)]
        chord_shape = _choose_chord_shape()
        base_duration = 1.5 if beat_step == 1.0 else random.choice([2.0, 3.0])
        if producer in {"Nujabes", "Apollo Brown", "Dr Dre"}:
            base_duration += 0.5
        velocity_base = random.randint(66, 94) + theme_profile["accent"]
        raw_pitches = [int(prog_root + int(interval)) for interval in chord_shape]
        voiced = _voice_chord(raw_pitches, prev_center=prev_center)
        if voiced:
            prev_center = sum(voiced) / float(len(voiced))
        for tone_idx, pitch in enumerate(voiced):
            velocity = velocity_base - tone_idx * random.randint(4, 8)
            data.append([float(round(start, 3)), int(pitch), float(min(4.0, base_duration)), int(max(1, min(127, velocity)))])
        if random.random() < chord_arp_prob and len(voiced) <= 3:
            top = int(max(voiced) if voiced else (prog_root + random.choice(chord_shape)))
            t_off = 0.5 if beat_step == 1.0 else 1.0
            data.append([float(round(start + t_off, 3)), int(top), float(0.25 if beat_step == 1.0 else 0.5), int(max(1, min(127, velocity_base + 6)))])

    data.sort(key=lambda x: (x[0], x[1]))
    return data


def build_chord_loop(theme_name, bars, energy=5):
    _, theme_only = split_theme(theme_name)
    theme_profile = build_theme_profile(theme_only)
    energy = max(1, min(10, int(energy)))
    root = random.choice([48, 50, 53, 55, 57, 60]) + max(-5, min(5, theme_profile["register_shift"]))
    progression = theme_profile.get("progression") or [0, 5, 7, 10]
    chord_shapes = theme_profile.get("chords") or [[0, 3, 7], [0, 5, 7], [0, 3, 7, 10]]
    prog_steps = [0, progression[1 % len(progression)], progression[2 % len(progression)], progression[3 % len(progression)]]
    data = []
    for bar in range(int(bars)):
        start = float(bar * 4.0)
        step = prog_steps[bar % 4]
        chord = chord_shapes[(bar + (0 if energy < 7 else 1)) % len(chord_shapes)]
        base_pitch = root + int(step)
        vel_base = random.randint(62, 92)
        for idx, interval in enumerate(chord[:4]):
            pitch = base_pitch + int(interval)
            if 36 <= pitch <= 90:
                vel = max(1, min(127, int(vel_base - idx * 7)))
                data.append([start, int(pitch), 4.0, int(vel)])
    data.sort(key=lambda x: (x[0], x[1]))
    return data

# -*- coding: utf-8 -*-

import random

from core.generator.theme_profiles import build_theme_profile, get_producer_profile, split_theme
from core.generator.utils import (
    build_allowed_notes as _build_allowed_notes,
    solo_duration_pool as _solo_duration_pool,
    solo_theme_mods as _solo_theme_mods,
    weighted_choice as _weighted_choice,
)


def generate_sax_solo(*args, **kwargs):
    from core.generator.solos_sax_impl import generate_sax_solo as impl

    return impl(*args, **kwargs)


def generate_piano_solo(*args, **kwargs):
    from core.generator.solos_piano_impl import generate_piano_solo as impl

    return impl(*args, **kwargs)


def generate_trumpet_solo(*args, **kwargs):
    from core.generator.solos_trumpet_impl import generate_trumpet_solo as impl

    return impl(*args, **kwargs)


def generate_flute_solo(*args, **kwargs):
    from core.generator.solos_flute_impl import generate_flute_solo as impl

    return impl(*args, **kwargs)


def generate_marimba_solo(*args, **kwargs):
    from core.generator.solos_marimba_impl import generate_marimba_solo as impl

    return impl(*args, **kwargs)


def generate_vibraphone_solo(*args, **kwargs):
    from core.generator.solos_vibraphone_impl import generate_vibraphone_solo as impl

    return impl(*args, **kwargs)


def generate_acoustic_bass_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    try:
        total_bars = int(bars)
    except Exception:
        total_bars = 8
    total_bars = max(4, min(8, total_bars))
    beats_total = float(total_bars * 4)

    producer, theme_name = split_theme(theme)
    theme_profile = build_theme_profile(theme_name)
    solo_mods = _solo_theme_mods(theme_name, theme_profile)
    reg_shift = int(solo_mods["register_shift"])
    root = random.choice([40, 43, 45, 47]) + reg_shift
    register = (max(36, 40 + reg_shift), min(64, 64 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(40, [0, 3, 5, 7, 10], (36, 64))
    allowed_sorted = sorted(allowed)
    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    home_idx = allowed_sorted.index(home_pitch) if allowed_sorted else 0
    targets = []
    for off in (0, 2, 4, -2, -4):
        idx = max(0, min(len(allowed_sorted) - 1, home_idx + off)) if allowed_sorted else 0
        if allowed_sorted:
            targets.append(int(allowed_sorted[idx]))
    targets = list(dict.fromkeys(targets)) or [int(home_pitch)]

    def _nudge_scale_steps(pitch: int, steps: int) -> int:
        if not allowed_sorted:
            return int(pitch)
        p = int(pitch)
        idx = min(range(len(allowed_sorted)), key=lambda i: abs(int(allowed_sorted[i]) - p))
        idx2 = max(0, min(len(allowed_sorted) - 1, idx + int(steps)))
        return int(allowed_sorted[idx2])

    char_s = str(character or "Klidné").strip().lower()
    is_wild = char_s.startswith("div")
    use_story = bool(story) if story is not None else False
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    dur_pool_motif = _solo_duration_pool(theme_profile, dur_mode, base=[0.5, 0.75, 1.0, 1.5, 2.0])
    if is_wild:
        sections = [
            {"dens": 0.42, "grid": 0.5, "vel": 92, "leap": 3, "dur": [0.5, 0.75, 1.0]},
            {"dens": 0.48, "grid": 0.5, "vel": 96, "leap": 4, "dur": [0.5, 0.75, 1.0]},
            {"dens": 0.54, "grid": 0.5, "vel": 102, "leap": 4, "dur": [0.5, 0.75, 1.0]},
            {"dens": 0.44, "grid": 0.5, "vel": 94, "leap": 3, "dur": [0.5, 0.75, 1.0]},
        ]
        flat = {"dens": 0.50, "grid": 0.5, "vel": 98, "leap": 4, "dur": [0.5, 0.75, 1.0]}
    else:
        sections = [
            {"dens": 0.26, "grid": 1.0, "vel": 76, "leap": 2, "dur": [1.0, 1.5, 2.0]},
            {"dens": 0.30, "grid": 1.0, "vel": 80, "leap": 2, "dur": [1.0, 1.5, 2.0]},
            {"dens": 0.34, "grid": 0.5, "vel": 86, "leap": 3, "dur": [0.75, 1.0, 1.5]},
            {"dens": 0.28, "grid": 1.0, "vel": 78, "leap": 2, "dur": [1.0, 1.5, 2.0]},
        ]
        flat = {"dens": 0.30, "grid": 1.0, "vel": 82, "leap": 2, "dur": [1.0, 1.5, 2.0]}

    per_section = [total_bars, 0, 0, 0] if not use_story else [1, 1, 1, 1]
    if use_story:
        extra = total_bars - 4
        for sec_i in (2, 1, 0, 3):
            if extra <= 0:
                break
            per_section[sec_i] += 1
            extra -= 1
        while extra > 0:
            for sec_i in range(4):
                if extra <= 0:
                    break
                per_section[sec_i] += 1
                extra -= 1

    motif = []
    if motif_source:
        try:
            src = []
            for n in motif_source:
                if not isinstance(n, (list, tuple)) or len(n) < 3:
                    continue
                t = float(n[0])
                if t < 0 or t >= min(4.0, beats_total):
                    continue
                src.append([t, int(n[1]), float(n[2]), int(n[3]) if len(n) > 3 else 90])
            src.sort(key=lambda x: (float(x[0]), int(x[1])))
            if src:
                step_take = max(1, int(len(src) / 5))
                picked = src[::step_take][:5]
                for it in picked:
                    motif.append([float(round(it[0], 3)), int(it[1]), float(round(max(0.5, min(2.0, it[2])), 3)), int(it[3])])
        except Exception:
            motif = []

    if not motif:
        motif_len = 2.0 if random.random() < 0.65 else 4.0
        last_p = int(random.choice(targets))
        t = 0.0
        while t < motif_len - 1e-6:
            strong = abs((t % 1.0)) < 1e-6
            if (not strong) and random.random() < 0.55:
                t += 0.5
                continue
            p = int(random.choice(targets)) if strong and random.random() < 0.65 else _nudge_scale_steps(last_p, random.choice([-1, 1, 2, -2]))
            dur = float(_weighted_choice(dur_pool_motif, 1.0))
            vel = int((96 if is_wild else 84) + (10 if strong else 0) + random.randint(-8, 8) + theme_profile["accent"])
            motif.append([float(round(t, 3)), int(p), float(round(dur, 3)), int(max(1, min(127, vel)))])
            last_p = int(p)
            t += 0.5

    def _pick_pitch(last_pitch, leap_limit: int) -> int:
        if not allowed_sorted:
            return int(home_pitch)
        if last_pitch is None:
            return int(random.choice(targets))
        if random.random() < 0.58:
            return int(random.choice(targets))
        steps = random.choice([-leap_limit, -(leap_limit - 1), -1, 1, (leap_limit - 1), leap_limit])
        return _nudge_scale_steps(int(last_pitch), int(steps))

    out = []
    bar_cursor = 0
    last_pitch = None
    for sec_i, bars_in_sec in enumerate(per_section):
        if bars_in_sec <= 0:
            continue
        sec = sections[sec_i] if use_story else flat
        grid = float(sec["grid"])
        steps_per_bar = int(round(4.0 / grid))
        for bar in range(int(bars_in_sec)):
            bar_start = float((bar_cursor + bar) * 4)
            if random.random() < (0.62 if is_wild else 0.72):
                for m in motif:
                    t = float(round(bar_start + float(m[0]), 3))
                    if t >= beats_total:
                        continue
                    dens_eff = float(sec["dens"]) * dens_mult + 0.15
                    dens_eff = max(0.06, min(0.98, dens_eff))
                    if random.random() > dens_eff:
                        continue
                    p = int(m[1])
                    if random.random() < (0.22 if is_wild else 0.14):
                        p = _pick_pitch(p, int(sec["leap"]))
                    dur = float(m[2])
                    if random.random() < 0.25:
                        dur = float(_weighted_choice(_solo_duration_pool(theme_profile, dur_mode, base=sec["dur"]), dur))
                    strong = abs((t % 1.0)) < 1e-6
                    vel = int(sec["vel"] + (12 if strong else 0) + random.randint(-8, 10) + theme_profile["accent"])
                    out.append([t, int(p), float(round(dur, 3)), int(max(1, min(127, vel)))])
                    last_pitch = int(p)
            for k in range(steps_per_bar):
                t = float(round(bar_start + k * grid, 3))
                if t >= beats_total:
                    continue
                strong = abs((t % 1.0)) < 1e-6
                if (not strong) and random.random() < 0.70:
                    continue
                dens_eff = float(sec["dens"]) * dens_mult + (0.12 if strong else 0.0)
                dens_eff = max(0.06, min(0.98, dens_eff))
                if random.random() > dens_eff:
                    continue
                p = _pick_pitch(last_pitch, int(sec["leap"]))
                dur = float(_weighted_choice(_solo_duration_pool(theme_profile, dur_mode, base=sec["dur"]), 1.0))
                vel = int(sec["vel"] + (14 if strong else 0) + random.randint(-8, 10) + theme_profile["accent"])
                out.append([t, int(p), float(round(dur, 3)), int(max(1, min(127, vel)))])
                last_pitch = int(p)
            if random.random() < 0.50:
                out.append([float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 1.0, int(sec["vel"] + 12)])
        bar_cursor += int(bars_in_sec)

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    cleaned = []
    for n in out:
        try:
            start = float(n[0])
            pitch = int(n[1])
            dur = float(n[2])
            vel = int(n[3]) if len(n) > 3 else 90
        except Exception:
            continue
        if dur <= 0:
            continue
        if start < 0 or start >= beats_total:
            continue
        if start + dur > beats_total:
            dur = max(0.25, beats_total - start)
        if not cleaned:
            cleaned.append([float(round(start, 3)), pitch, float(round(dur, 3)), int(max(1, min(127, vel)))])
            continue
        prev = cleaned[-1]
        prev_start = float(prev[0])
        prev_dur = float(prev[2])
        prev_end = prev_start + prev_dur
        if abs(start - prev_start) < 1e-6:
            if vel > int(prev[3]):
                cleaned[-1] = [float(round(start, 3)), pitch, float(round(dur, 3)), int(max(1, min(127, vel)))]
            continue
        if start < prev_end - 1e-6:
            gap = max(0.0, start - prev_start)
            if gap < 0.25:
                continue
            prev[2] = float(round(gap, 3))
            cleaned[-1] = prev
        cleaned.append([float(round(start, 3)), pitch, float(round(dur, 3)), int(max(1, min(127, vel)))])
    cleaned.sort(key=lambda x: (float(x[0]), int(x[1])))
    return cleaned

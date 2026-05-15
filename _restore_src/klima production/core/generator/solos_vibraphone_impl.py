# -*- coding: utf-8 -*-

import random
import numpy as np

from core.generator.theme_profiles import build_theme_profile, get_producer_profile, split_theme
from core.generator.solos import _build_allowed_notes, _solo_duration_pool, _solo_theme_mods, _weighted_choice

_split_theme = split_theme
_get_producer_profile = get_producer_profile
_build_theme_profile = build_theme_profile

def generate_vibraphone_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local vibraphone solo generator (short + loop-friendly), monophonic.

    Vibraphone works well for jazzy/boombap lines: medium-long tones, gentle runs,
    and repeated motifs without getting too busy.
    """
    try:
        total_bars = int(bars)
    except Exception:
        total_bars = 8
    total_bars = max(4, min(8, total_bars))
    beats_total = float(total_bars * 4)

    producer, theme_name = _split_theme(theme)
    producer_profile = _get_producer_profile(producer)
    theme_profile = _build_theme_profile(theme_name)
    solo_mods = _solo_theme_mods(theme_name, theme_profile)

    reg_shift = int(solo_mods["register_shift"])
    root = random.choice([55, 57, 58, 60, 62]) + reg_shift
    # Vibes: comfortable mid-high range.
    register = (max(55, 60 + reg_shift), min(92, 88 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (60, 88))
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

    char_s = str(character or "KlidnĂ©").strip().lower()
    is_wild = char_s.startswith("div")
    use_story = bool(story) if story is not None else False
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)

    if is_wild:
        sections = [
            {"dens": 0.42, "center": 2, "grid": 0.25, "run_prob": 0.22, "vel": 90, "dur": [0.5, 0.75, 1.0]},
            {"dens": 0.50, "center": 3, "grid": 0.25, "run_prob": 0.26, "vel": 94, "dur": [0.5, 0.75, 1.0, 1.5]},
            {"dens": 0.56, "center": 4, "grid": 0.25, "run_prob": 0.34, "vel": 100, "dur": [0.5, 0.75, 1.0]},
            {"dens": 0.44, "center": 2, "grid": 0.25, "run_prob": 0.24, "vel": 92, "dur": [0.75, 1.0, 1.5]},
        ]
        flat = {"dens": 0.50, "center": 3, "grid": 0.25, "run_prob": 0.28, "vel": 96, "dur": [0.5, 0.75, 1.0, 1.5]}
    else:
        sections = [
            {"dens": 0.24, "center": 1, "grid": 0.5, "run_prob": 0.10, "vel": 74, "dur": [1.0, 1.5, 2.0]},
            {"dens": 0.28, "center": 2, "grid": 0.5, "run_prob": 0.12, "vel": 78, "dur": [1.0, 1.5, 2.0]},
            {"dens": 0.34, "center": 3, "grid": 0.5, "run_prob": 0.18, "vel": 84, "dur": [0.75, 1.0, 1.5, 2.0]},
            {"dens": 0.26, "center": 1, "grid": 0.5, "run_prob": 0.11, "vel": 76, "dur": [1.0, 1.5, 2.0]},
        ]
        flat = {"dens": 0.30, "center": 2, "grid": 0.5, "run_prob": 0.13, "vel": 80, "dur": [1.0, 1.5, 2.0]}

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
                step_take = max(1, int(len(src) / 6))
                picked = src[::step_take][:6]
                for it in picked:
                    motif.append([float(it[0]), int(it[1]), float(max(0.5, min(2.0, it[2]))), int(it[3])])
        except Exception:
            motif = []

    if not motif:
        # Simple signature motif: a few target tones that can be repeated/varied.
        motif_len = 2.0 if random.random() < 0.65 else 4.0
        t = 0.0
        last_p = int(random.choice(targets))
        while t < motif_len - 1e-6:
            if random.random() < (0.18 if is_wild else 0.28):
                t += 0.5
                continue
            steps = random.choice([-2, -1, 1, 2, 3]) if is_wild else random.choice([-1, 1, 2])
            p = _nudge_scale_steps(last_p, steps)
            dur = float(_weighted_choice([0.75, 1.0, 1.5], 1.0))
            vel = int((92 if is_wild else 80) + random.randint(-10, 10) + theme_profile["accent"])
            motif.append([float(round(t, 3)), int(p), float(round(dur, 3)), int(max(1, min(127, vel)))])
            last_p = int(p)
            t += 0.5

    def _pick_pitch(last_pitch: int | None, center_steps: int) -> int:
        if not allowed_sorted:
            return int(home_pitch)
        if last_pitch is None:
            idx = max(0, min(len(allowed_sorted) - 1, home_idx + int(center_steps)))
            return int(allowed_sorted[idx])
        if random.random() < 0.55:
            return int(random.choice(targets))
        steps = random.choice([-3, -2, -1, 1, 2, 3]) if is_wild else random.choice([-2, -1, 1, 2])
        return _nudge_scale_steps(int(last_pitch), steps)

    out = []
    bar_cursor = 0
    last_pitch = None
    motif_len = max(0.5, float(max((m[0] + m[2]) for m in motif) if motif else 2.0))
    motif_len = float(round(min(4.0, max(1.0, motif_len)), 3))
    for sec_i, bars_in_sec in enumerate(per_section):
        if bars_in_sec <= 0:
            continue
        sec = sections[sec_i] if use_story else flat
        for bar in range(int(bars_in_sec)):
            bar_start = float((bar_cursor + bar) * 4)
            # Repeat the motif but with small pitch/duration tweaks.
            if random.random() < (0.55 if is_wild else 0.60):
                for m in motif:
                    t = float(round(bar_start + float(m[0]), 3))
                    if t >= beats_total:
                        continue
                    p = int(m[1])
                    if random.random() < (0.28 if is_wild else 0.18):
                        p = _pick_pitch(p, sec["center"])
                    dur = float(m[2])
                    if random.random() < (0.30 if is_wild else 0.22):
                        dur = float(_weighted_choice(_solo_duration_pool(theme_profile, dur_mode, base=sec["dur"]), dur))
                    vel = int(sec["vel"] + random.randint(-10, 12) + theme_profile["accent"])
                    out.append([t, int(p), float(round(max(0.5, min(2.0, dur)), 3)), int(max(1, min(127, vel)))])

            # Fill a few extra notes (more space than marimba).
            grid = float(sec["grid"])
            steps = int(round(4.0 / grid))
            for k in range(steps):
                dens_eff = float(sec["dens"]) * dens_mult
                dens_eff = max(0.06, min(0.98, dens_eff))
                if random.random() > dens_eff:
                    continue
                t = float(round(bar_start + k * grid, 3))
                if t >= beats_total:
                    continue
                strong = abs((t % 1.0)) < 1e-6
                if strong and random.random() < 0.12:
                    continue
                if random.random() < (float(sec["run_prob"]) * run_mult):
                    run_len = 3 if random.random() < 0.65 else 4
                    run_p = _pick_pitch(last_pitch, sec["center"])
                    for r in range(run_len):
                        tt = float(round(t + r * grid, 3))
                        if tt >= beats_total:
                            break
                        run_p = _nudge_scale_steps(run_p, random.choice([-2, -1, 1, 2, 3] if is_wild else [-1, 1, 2]))
                        vel = int(sec["vel"] + random.randint(-8, 10) + (10 if strong else 0) + theme_profile["accent"])
                        out.append([tt, int(run_p), float(round(_weighted_choice([0.5, 0.75, 1.0], 0.75), 3)), int(max(1, min(127, vel)))])
                        last_pitch = int(run_p)
                    continue

                p = _pick_pitch(last_pitch, sec["center"])
                dur = float(_weighted_choice(_solo_duration_pool(theme_profile, dur_mode, base=sec["dur"]), 1.0))
                vel = int(sec["vel"] + random.randint(-8, 10) + (10 if strong else 0) + theme_profile["accent"])
                out.append([t, int(p), float(round(dur, 3)), int(max(1, min(127, vel)))])
                last_pitch = int(p)

            if random.random() < 0.45:
                out.append([float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 1.5, int(sec["vel"] + 10)])

        bar_cursor += int(bars_in_sec)

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    # Ensure monophonic (no overlaps) to keep layering simple in a DAW.
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



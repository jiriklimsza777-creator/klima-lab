# -*- coding: utf-8 -*-

import random
import numpy as np

from core.generator.theme_profiles import build_theme_profile, get_producer_profile, split_theme
from core.generator.solos import _build_allowed_notes, _solo_duration_pool, _solo_theme_mods, _weighted_choice

_split_theme = split_theme
_get_producer_profile = get_producer_profile
_build_theme_profile = build_theme_profile

def generate_flute_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local flute solo generator (short + loop-friendly), monophonic.

    Flute works well as airy, smooth melodic phrases with fewer aggressive jumps.
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
    # Flute sweet spot: higher but gentle.
    register = (max(60, 67 + reg_shift), min(96, 92 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (67, 92))
    allowed_sorted = sorted(allowed)

    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    home_idx = allowed_sorted.index(home_pitch) if allowed_sorted else 0
    targets = []
    for off in (0, 2, -2, 4, -4):
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
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.5, 0.75, 1.0, 1.5, 2.0])

    if is_wild:
        sections = [
            {"dens": 0.40, "center": 5, "grid": 0.5, "run_prob": 0.18, "vel": 86},
            {"dens": 0.46, "center": 6, "grid": 0.5, "run_prob": 0.22, "vel": 90},
            {"dens": 0.54, "center": 7, "grid": 0.25, "run_prob": 0.30, "vel": 96},
            {"dens": 0.42, "center": 5, "grid": 0.5, "run_prob": 0.20, "vel": 88},
        ]
        flat = {"dens": 0.48, "center": 6, "grid": 0.5, "run_prob": 0.24, "vel": 92}
    else:
        sections = [
            {"dens": 0.22, "center": 4, "grid": 0.5, "run_prob": 0.08, "vel": 72},
            {"dens": 0.26, "center": 5, "grid": 0.5, "run_prob": 0.10, "vel": 76},
            {"dens": 0.32, "center": 6, "grid": 0.5, "run_prob": 0.14, "vel": 80},
            {"dens": 0.24, "center": 4, "grid": 0.5, "run_prob": 0.09, "vel": 74},
        ]
        flat = {"dens": 0.26, "center": 5, "grid": 0.5, "run_prob": 0.10, "vel": 76}

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
                for _, p, d, v in picked:
                    p2 = int(min(allowed_sorted, key=lambda ap: abs(int(ap) - int(p)))) if allowed_sorted else int(p)
                    motif.append([0.0, p2, float(max(0.25, min(1.5, d))), int(max(1, min(127, v)))])
        except Exception:
            motif = []

    out = []
    def _add(start, pitch, dur, vel):
        if start < 0 or start >= beats_total:
            return
        dur = float(max(0.25, dur))
        if start + dur > beats_total:
            dur = max(0.25, beats_total - start)
        out.append([float(round(start, 3)), int(pitch), float(round(dur, 3)), int(max(1, min(127, vel)))])

    bar_cursor = 0
    last_p = int(random.choice(targets))
    step_choices_calm = [-2, -1, 1, 2]
    step_choices_wild = [-3, -2, -1, 1, 2, 3]

    for sec_i in range(4):
        sec = sections[sec_i] if use_story else flat
        bars_in_sec = int(per_section[sec_i])
        dens = float(sec["dens"]) + (0.04 * (float(energy) - 5.0) / 5.0)
        dens = dens * dens_mult
        dens = max(0.12, min(0.82, dens))
        grid = float(sec["grid"])

        for b in range(bars_in_sec):
            bar = bar_cursor + b
            bar_start = float(bar * 4.0)
            slots = [float(round(t, 3)) for t in np.arange(bar_start, bar_start + 4.0, grid)]
            if not slots:
                continue
            # Flute: fewer notes, longer tones.
            max_notes = int(round(len(slots) * (0.12 + dens * 0.26)))
            max_notes = max(2, min(8, max_notes))
            random.shuffle(slots)
            chosen = sorted(slots[:max_notes])

            for t in chosen:
                strong = abs(t % 1.0) < 0.001
                use_motif = bool(motif) and (bar == 0 or random.random() < 0.30)
                if use_motif:
                    mi = min(chosen.index(t), len(motif) - 1)
                    p = int(motif[mi][1])
                    if random.random() < 0.25:
                        p = _nudge_scale_steps(p, random.choice([-1, 1, 2, -2]))
                elif strong and random.random() < 0.42:
                    p = int(random.choice(targets))
                else:
                    steps = step_choices_wild if is_wild else step_choices_calm
                    if random.random() < (float(sec["run_prob"]) * run_mult):
                        steps = step_choices_wild
                    p = _nudge_scale_steps(last_p, random.choice(steps))

                dur = float(_weighted_choice(dur_pool_main, 1.0))
                vel = int(sec["vel"] + random.randint(-8, 10) + (8 if strong else 0) + theme_profile["accent"])
                _add(t, p, dur, vel)
                last_p = int(p)

            if random.random() < 0.60:
                _add(float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 1.5, int(sec["vel"] + 8))

        bar_cursor += bars_in_sec

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out



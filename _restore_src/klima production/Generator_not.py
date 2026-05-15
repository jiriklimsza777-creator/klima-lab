# -*- coding: utf-8 -*-
import random

import numpy as np

from core.generator.theme_profiles import (
    DEFAULT_PROFILE,
    build_theme_profile as _build_theme_profile,
    get_producer_profile as _get_producer_profile,
    split_theme as _split_theme,
)
from core.generator.utils import (
    build_allowed_notes as _build_allowed_notes,
    choose_next_pitch as _choose_next_pitch,
    choose_next_pitch_classic as _choose_next_pitch_classic,
    merge_unique as _merge_unique,
    solo_duration_pool as _solo_duration_pool,
    solo_theme_mods as _solo_theme_mods,
    weighted_choice as _weighted_choice,
)
# Bridge imports are intentionally kept minimal while legacy implementations
# still live in this module.


def get_producer_energy(producer):
    mapping = {
        "Daringer": 3,
        "Apollo Brown": 4,
        "J Dilla": 5,
        "Madlib": 5,
        "Knxwledge": 5,
        "Nujabes": 5,
        "Pete Rock": 6,
        "9th Wonder": 6,
        "Q-Tip": 6,
        "Havoc": 6,
        "RZA": 6,
        "MF DOOM": 7,
        "Dr Dre": 7,
        "Kanye West": 7,
        "DJ Premier": 7,
        "The Alchemist": 6,
        "Just Blaze": 8,
        "Timbaland": 8,
        "Metro Boomin": 9,
    }
    return mapping.get(producer, random.randint(4, 7))


def smart_generate_classic(num_bars, theme="Freestyle", energy=5):
    """Legacy local melody generator (pre-boombap-loop)."""
    producer, theme_name = _split_theme(theme)
    producer_profile = _get_producer_profile(producer)
    theme_profile = _build_theme_profile(theme_name)

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

    # Producer/theme "signature" (Melodic should feel meaningfully different per producer/theme).
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
                # Keep the loop recognizable for "signature" producers (Premier, Dre),
                # but allow more mutation for more "wild" ones (Madlib).
                if variation_roll < pitch_mut_chance:
                    new_pitch = _choose_next_pitch(int(note[1]), allowed, max(2, jump_limit - 1))
                if variation_roll > 1.0 - dur_mut_chance:
                    new_duration = _weighted_choice(durations, note[2])

                # Occasionally re-anchor strong beats to home tones (hook feel).
                strong_rep = abs(float(note[0]) % 1.0) < 0.001
                if strong_rep and random.random() < (cadence_prob * 0.55):
                    new_pitch = int(random.choice(cadence_candidates))
                data.append([float(round(start_time, 3)), int(new_pitch), float(new_duration), int(note[3])])

    data.sort(key=lambda x: x[0])
    return data


def generate_sax_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local sax solo generator (short + loop-friendly).

    Shape (scaled to bars, 4..8 recommended):
      - Bez pĹ™Ă­bÄ›hu: konzistentnĂ­ charakter po celou dobu (klidnĂ© nebo divokĂ©)
      - PĹ™Ă­bÄ›h: jemnĂ˝ vĂ˝voj (intro -> develop -> peak -> outro) bez brutĂˇlnĂ­ho zlomu

    Output is still just MIDI-like notes, but phrasing + rests makes it feel "sax".
    """
    try:
        total_bars = int(bars)
    except Exception:
        total_bars = 8
    total_bars = max(4, min(8, total_bars))
    producer, theme_name = _split_theme(theme)
    producer_profile = _get_producer_profile(producer)
    theme_profile = _build_theme_profile(theme_name)
    solo_mods = _solo_theme_mods(theme_name, theme_profile)

    # Sax sweet spot: keep the register mostly around C4..C6 (60..84).
    reg_shift = int(solo_mods["register_shift"])
    root = random.choice([55, 57, 58, 60, 62]) + reg_shift
    register = (max(56, 60 + reg_shift), min(84, 84 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (60, 84))
    allowed_sorted = sorted(allowed)

    # Cadence tones (home-ish) for phrase endings.
    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    home_idx = allowed_sorted.index(home_pitch) if allowed_sorted else 0
    cadence_candidates = []
    for off in (0, -2, 2, -4, 4):
        idx = max(0, min(len(allowed_sorted) - 1, home_idx + off)) if allowed_sorted else 0
        if allowed_sorted:
            cadence_candidates.append(int(allowed_sorted[idx]))
    cadence_candidates = list(dict.fromkeys(cadence_candidates)) or [int(home_pitch)]

    def _nudge_scale_steps(pitch: int, steps: int) -> int:
        if not allowed_sorted:
            return int(pitch)
        p = int(pitch)
        idx = min(range(len(allowed_sorted)), key=lambda i: abs(int(allowed_sorted[i]) - p))
        idx2 = max(0, min(len(allowed_sorted) - 1, idx + int(steps)))
        return int(allowed_sorted[idx2])

    def _pick_center_pitch(center_steps: int = 0) -> int:
        if not allowed_sorted:
            return int(home_pitch)
        idx = max(0, min(len(allowed_sorted) - 1, home_idx + int(center_steps)))
        return int(allowed_sorted[idx])

    def _phrase_slots(start_t: float, length: float, grid: float):
        # Leave a little breath at the end of the phrase.
        end_t = max(start_t, float(start_t + max(0.0, length - grid)))
        slots = [float(round(t, 3)) for t in np.arange(start_t, end_t + 1e-9, grid)]
        return slots

    # Motif (short signature). If we have a locked base melody, extract a motif from it
    # so new proposals become variations around that locked one.
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
            # Take up to 6 notes, spaced out.
            if src:
                step_take = max(1, int(len(src) / 6))
                picked = src[::step_take][:6]
                for _, p, d, v in picked:
                    # Keep motif in scale by snapping to nearest allowed.
                    p2 = int(min(allowed_sorted, key=lambda ap: abs(int(ap) - int(p)))) if allowed_sorted else int(p)
                    motif.append([0.0, p2, float(max(0.25, min(1.5, d))), int(max(1, min(127, v)))])
        except Exception:
            motif = []

    if not motif:
        motif_center = _pick_center_pitch(center_steps=1)
        last_p = motif_center
        motif_grid = 0.5
        motif_slots = _phrase_slots(0.0, 2.5, motif_grid)
        random.shuffle(motif_slots)
        motif_slots = sorted(motif_slots[:5])
        for t in motif_slots:
            strong = abs(t % 1.0) < 0.001
            if strong and random.random() < 0.55:
                p = int(random.choice(cadence_candidates))
            else:
                # Gentle motion for the motif.
                p = _nudge_scale_steps(int(last_p), steps=random.choice([-2, -1, 1, 2]))
            dur = float(_weighted_choice([0.25, 0.5, 1.0, 1.5], 0.5))
            vel = int(max(1, min(127, random.randint(70, 92) + (10 if strong else 0) + theme_profile["accent"])))
            motif.append([float(round(t, 3)), int(p), dur, vel])
            last_p = p
        motif.sort(key=lambda x: float(x[0]))

    # Light motif variation so "locked variations" are similar but not identical.
    for i in range(len(motif)):
        if random.random() < (0.25 if motif_source else 0.12):
            motif[i][1] = _nudge_scale_steps(int(motif[i][1]), steps=random.choice([-1, 1, 2, -2]))

    char_s = str(character or "KlidnĂ©").strip().lower()
    is_wild = char_s.startswith("div")  # divoke/divokĂ©
    use_story = bool(story) if story is not None else False
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    dur_pool_motif = _solo_duration_pool(theme_profile, dur_mode, base=[0.5, 0.75, 1.0, 1.5, 2.0])
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.25, 0.5, 0.75, 1.0])
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.5, 0.75, 1.0, 1.5, 2.0])
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    center_add = int(solo_mods.get("center_steps") or 0)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.5, 0.5, 0.75, 1.0, 1.5])

    # Section settings (intro/develop/peak/outro).
    # IMPORTANT: keep the contrast mild so the second half doesn't sound like a different song.
    if is_wild:
        # "DivokĂ©" overall.
        sections = [
            {"dens": 0.48, "center": 3, "grid": 0.5, "run_prob": 0.14, "vel": 88},
            {"dens": 0.54, "center": 4, "grid": 0.5, "run_prob": 0.18, "vel": 92},
            {"dens": 0.62, "center": 6, "grid": 0.25, "run_prob": 0.26, "vel": 98},
            {"dens": 0.50, "center": 3, "grid": 0.5, "run_prob": 0.16, "vel": 90},
        ]
        flat_section = {"dens": 0.56, "center": 5, "grid": 0.5, "run_prob": 0.22, "vel": 94}
    else:
        # "KlidnĂ©" overall.
        sections = [
            {"dens": 0.26, "center": 0, "grid": 0.5, "run_prob": 0.04, "vel": 72},
            {"dens": 0.30, "center": 1, "grid": 0.5, "run_prob": 0.06, "vel": 76},
            {"dens": 0.38, "center": 2, "grid": 0.5, "run_prob": 0.10, "vel": 82},
            {"dens": 0.28, "center": 0, "grid": 0.5, "run_prob": 0.05, "vel": 74},
        ]
        flat_section = {"dens": 0.30, "center": 1, "grid": 0.5, "run_prob": 0.06, "vel": 76}

    out = []
    beats_total = float(total_bars * 4)
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    center_add = int(solo_mods.get("center_steps") or 0)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.5, 1.0, 1.5])
    dur_pool_peak = _solo_duration_pool(theme_profile, "short" if dur_mode == "short" else "normal", base=[0.25, 0.25, 0.5, 0.5, 1.0])

    def _add_note(start_t: float, pitch: int, dur: float, vel: int):
        if start_t < 0 or start_t >= beats_total:
            return
        dur = float(max(0.25, dur))
        out.append([float(round(start_t, 3)), int(pitch), float(round(dur, 3)), int(max(1, min(127, vel)))])

    # Distribute bars across 4 sections only when "PĹ™Ă­bÄ›h" is enabled.
    # 4 bars: 1/1/1/1, 5 bars: 1/1/2/1, 6 bars: 1/2/2/1, 7 bars: 2/2/2/1, 8 bars: 2/2/2/2.
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

    bar_cursor = 0
    for sec_i in range(4):
        sec = sections[sec_i] if use_story else flat_section
        bars_in_sec = int(per_section[sec_i])
        center_pitch = _pick_center_pitch(center_steps=int(sec["center"]) + center_add)
        base_grid = float(sec["grid"])
        dens = float(sec["dens"]) + (0.04 * (float(energy) - 5.0) / 5.0)
        dens = dens * dens_mult
        dens = max(0.14, min(0.86, dens))

        for b in range(bars_in_sec):
            bar = bar_cursor + b
            bar_start = float(bar * 4.0)

            # Phrasing: 1â€“2 phrases per bar; peak section can do 2.
            phrase_count = 2 if sec_i == 2 and random.random() < 0.80 else 1
            phrase_starts = [0.0] if phrase_count == 1 else [0.0, 2.0]
            for ps in phrase_starts:
                # Keep some space: sometimes skip the 2nd phrase in non-peak.
                if phrase_count == 2 and sec_i != 2 and ps > 0 and random.random() < 0.55:
                    continue

                phrase_len = 2.5 if ps == 0.0 else 1.75
                grid = base_grid
                if sec_i == 2 and random.random() < 0.55:
                    grid = 0.25  # allow runs in the peak
                slots = _phrase_slots(bar_start + ps + (0.5 if random.random() < 0.30 else 0.0), phrase_len, grid)

                # Decide note count: density + phrase length; always leave breath.
                max_notes = max(2, int(round((phrase_len / grid) * (0.22 + dens))))
                max_notes = min(max_notes, 8 if sec_i != 2 else 12)
                if random.random() < 0.25:
                    max_notes = max(2, max_notes - 1)

                if not slots:
                    continue
                random.shuffle(slots)
                chosen = sorted(slots[:max_notes])

                # Call/response feel inside each 2-bar pair.
                in_pair = (bar % 2 == 0)
                pair_shift = -2 if (not in_pair) else 0

                # Use motif at section starts, then vary it.
                use_motif = (sec_i == 0 and b == 0 and ps == 0.0) or (sec_i > 0 and b == 0 and ps == 0.0 and random.random() < 0.55)
                if use_motif and motif:
                    # Place motif relative to phrase start.
                    t0 = float(chosen[0])
                    for i_m, m in enumerate(motif):
                        if i_m >= len(chosen):
                            break
                        t = float(chosen[i_m])
                        p = _nudge_scale_steps(int(m[1]), steps=sec["center"] + pair_shift)
                        # Keep within a "sax-ish" band around center.
                        p = _nudge_scale_steps(p, steps=random.choice([0, 0, 1, -1]))
                        dur = float(m[2])
                        vel = int(sec["vel"] + (8 if sec_i == 2 else 0) + (6 if abs(t % 1.0) < 0.001 else 0))
                        _add_note(t, p, dur, vel)
                    last_p = int(out[-1][1]) if out else int(center_pitch)
                else:
                    # Build a phrase from the center with gentle to wilder movement.
                    last_p = int(center_pitch)
                    for t in chosen:
                        strong = abs(t % 1.0) < 0.001
                        if strong and random.random() < (0.28 if sec_i < 2 else 0.18):
                            p = int(random.choice(cadence_candidates))
                        else:
                            step_choices = [-2, -1, 1, 2]
                            if sec_i == 2 and random.random() < (float(sec["run_prob"]) * run_mult):
                                step_choices += [-4, 3, 4]
                            p = _nudge_scale_steps(int(last_p), steps=random.choice(step_choices))
                            p = _nudge_scale_steps(p, steps=pair_shift)

                        # Duration/velocity: more bite in peak, more sustain in intro/outro.
                        if sec_i == 2 and grid <= 0.25 and random.random() < (0.55 * run_mult):
                            dur = float(_weighted_choice(dur_pool_peak, 0.25))
                        else:
                            dur = float(_weighted_choice(dur_pool_main, 0.5))
                        vel = int(sec["vel"] + random.randint(-6, 10) + (10 if strong else 0) + theme_profile["accent"])
                        _add_note(t, p, dur, vel)
                        last_p = int(p)

                # End-of-phrase cadence (helps it sound like a "sentence").
                if random.random() < (0.78 if sec_i != 2 else 0.58):
                    end_t = float(round((bar_start + ps + phrase_len) - max(grid, 0.5), 3))
                    if end_t >= bar_start and end_t < (bar_start + 4.0):
                        end_pitch = int(random.choice(cadence_candidates))
                        end_pitch = _nudge_scale_steps(end_pitch, steps=sec["center"] + (0 if sec_i < 3 else -1))
                        _add_note(end_t, end_pitch, float(_weighted_choice([0.5, 1.0, 1.5], 1.0)), int(sec["vel"] + 10))

        bar_cursor += bars_in_sec

    # Final resolve: descending to home with a longer last note.
    if allowed_sorted:
        end_bar_start = float((total_bars - 1) * 4.0)
        p = int(_pick_center_pitch(center_steps=0))
        for k, t in enumerate([end_bar_start + 0.0, end_bar_start + 1.0, end_bar_start + 2.0]):
            p = _nudge_scale_steps(p, steps=-2 if k == 0 else -1)
            _add_note(t, p, 0.75, 86)
        _add_note(end_bar_start + 3.0, int(home_pitch), 1.5, 90)

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    # Sax solo should be monophonic: no overlapping notes (it should not form chords).
    # We preserve the *later* note timing and shorten the previous note to end before it.
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

        # Clamp into the solo length.
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

        # If the new note starts at (nearly) the same time as the previous, keep only one.
        if abs(start - prev_start) < 1e-6:
            # Keep the stronger note (higher velocity).
            if vel > int(prev[3]):
                cleaned[-1] = [float(round(start, 3)), pitch, float(round(dur, 3)), int(max(1, min(127, vel)))]
            continue

        # If overlap, shorten previous note to make space.
        if start < prev_end - 1e-6:
            gap = max(0.0, start - prev_start)
            # If there isn't even a 1/16 (0.25 beat) of space, drop the later note to avoid jitter.
            # (This keeps phrasing clean and avoids "machine-gun" overlaps.)
            if gap < 0.25:
                continue
            prev[2] = float(round(gap, 3))
            cleaned[-1] = prev

        cleaned.append([float(round(start, 3)), pitch, float(round(dur, 3)), int(max(1, min(127, vel)))])

    cleaned.sort(key=lambda x: (float(x[0]), int(x[1])))
    return cleaned


def generate_piano_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local piano solo generator (short + loop-friendly), monophonic by design so it's easy to layer in a DAW.

    Uses more arpeggio-like motion + chord-tone targets than sax.
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
    # Piano can sit a bit wider, but keep it musical.
    register = (max(52, 56 + reg_shift), min(88, 88 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (56, 88))
    allowed_sorted = sorted(allowed)

    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    home_idx = allowed_sorted.index(home_pitch) if allowed_sorted else 0
    chord_tones = []
    for off in (0, 2, 4, -2, -4):
        idx = max(0, min(len(allowed_sorted) - 1, home_idx + off)) if allowed_sorted else 0
        if allowed_sorted:
            chord_tones.append(int(allowed_sorted[idx]))
    chord_tones = list(dict.fromkeys(chord_tones)) or [int(home_pitch)]

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
            {"dens": 0.52, "center": 2, "grid": 0.5, "run_prob": 0.20, "vel": 88},
            {"dens": 0.60, "center": 3, "grid": 0.5, "run_prob": 0.24, "vel": 92},
            {"dens": 0.70, "center": 4, "grid": 0.25, "run_prob": 0.34, "vel": 98},
            {"dens": 0.56, "center": 2, "grid": 0.5, "run_prob": 0.22, "vel": 90},
        ]
        flat = {"dens": 0.62, "center": 3, "grid": 0.5, "run_prob": 0.26, "vel": 94}
    else:
        sections = [
            {"dens": 0.30, "center": 0, "grid": 0.5, "run_prob": 0.10, "vel": 72},
            {"dens": 0.34, "center": 1, "grid": 0.5, "run_prob": 0.12, "vel": 76},
            {"dens": 0.42, "center": 2, "grid": 0.5, "run_prob": 0.18, "vel": 82},
            {"dens": 0.32, "center": 0, "grid": 0.5, "run_prob": 0.12, "vel": 74},
        ]
        flat = {"dens": 0.34, "center": 1, "grid": 0.5, "run_prob": 0.12, "vel": 76}

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

    # Optional motif extracted from a locked base melody (to create variations around it).
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
                    motif.append([0.0, p2, float(max(0.25, min(1.0, d))), int(max(1, min(127, v)))])
        except Exception:
            motif = []

    # Light motif variation.
    def _vary_motif_pitch(p):
        return _nudge_scale_steps(int(p), steps=random.choice([-1, 1, 2, -2, 0]))

    out = []
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.5, 0.75, 1.0, 1.5])
    step_choices_calm = [-2, -1, 1, 2, 3]
    step_choices_wild = [-4, -3, -2, -1, 1, 2, 3, 4]

    def _add(start, pitch, dur, vel):
        if start < 0 or start >= beats_total:
            return
        dur = float(max(0.25, dur))
        if start + dur > beats_total:
            dur = max(0.25, beats_total - start)
        out.append([float(round(start, 3)), int(pitch), float(round(dur, 3)), int(max(1, min(127, vel)))])

    bar_cursor = 0
    last_p = int(random.choice(chord_tones))
    for sec_i in range(4):
        sec = sections[sec_i] if use_story else flat
        bars_in_sec = int(per_section[sec_i])
        dens = float(sec["dens"]) + (0.04 * (float(energy) - 5.0) / 5.0)
        dens = dens * dens_mult
        dens = max(0.14, min(0.90, dens))
        grid = float(sec["grid"])

        for b in range(bars_in_sec):
            bar = bar_cursor + b
            bar_start = float(bar * 4.0)

            # Simple arpeggio-like phrase with breathy gaps handled later by DAW if needed.
            slots = [float(round(t, 3)) for t in np.arange(bar_start, bar_start + 4.0, grid)]
            if not slots:
                continue
            # Keep fewer starts, even in wild mode.
            max_notes = int(round(len(slots) * (0.18 + dens * 0.35)))
            max_notes = max(3, min(10, max_notes))
            random.shuffle(slots)
            chosen = sorted(slots[:max_notes])

            for t in chosen:
                strong = abs(t % 1.0) < 0.001
                use_motif = bool(motif) and (bar == 0 or random.random() < (0.35 if not is_wild else 0.22))
                if use_motif:
                    mi = chosen.index(t) if t in chosen else 0
                    mi = min(mi, len(motif) - 1)
                    p = _vary_motif_pitch(motif[mi][1]) if random.random() < 0.45 else int(motif[mi][1])
                elif strong and random.random() < (0.42 if not is_wild else 0.32):
                    p = int(random.choice(chord_tones))
                else:
                    steps = step_choices_wild if is_wild else step_choices_calm
                    if random.random() < (float(sec["run_prob"]) * run_mult):
                        steps = step_choices_wild
                    p = _nudge_scale_steps(last_p, random.choice(steps))
                dur = float(_weighted_choice(dur_pool_main, 0.5))
                vel = int(sec["vel"] + random.randint(-6, 10) + (8 if strong else 0) + theme_profile["accent"])
                _add(t, p, dur, vel)
                last_p = int(p)

            # Phrase end target.
            if random.random() < 0.70:
                end_t = float(round(bar_start + 3.0, 3))
                _add(end_t, int(random.choice(chord_tones)), 1.0, int(sec["vel"] + 10))

        bar_cursor += bars_in_sec

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


def generate_trumpet_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local trumpet solo generator (short + loop-friendly), monophonic.

    Trumpet in boombap often works as punchy stabs + small runs.
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
    # Trumpet sweet spot: a bit higher and tighter than piano.
    register = (max(58, 62 + reg_shift), min(88, 86 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (62, 86))
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
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.5, 0.5, 0.75, 1.0, 1.5])

    if is_wild:
        sections = [
            {"dens": 0.46, "center": 4, "grid": 0.5, "run_prob": 0.16, "vel": 92},
            {"dens": 0.52, "center": 5, "grid": 0.5, "run_prob": 0.20, "vel": 96},
            {"dens": 0.60, "center": 7, "grid": 0.25, "run_prob": 0.30, "vel": 104},
            {"dens": 0.48, "center": 4, "grid": 0.5, "run_prob": 0.18, "vel": 94},
        ]
        flat = {"dens": 0.54, "center": 6, "grid": 0.5, "run_prob": 0.24, "vel": 98}
    else:
        sections = [
            {"dens": 0.26, "center": 2, "grid": 0.5, "run_prob": 0.08, "vel": 80},
            {"dens": 0.30, "center": 3, "grid": 0.5, "run_prob": 0.10, "vel": 84},
            {"dens": 0.36, "center": 4, "grid": 0.5, "run_prob": 0.14, "vel": 88},
            {"dens": 0.28, "center": 2, "grid": 0.5, "run_prob": 0.09, "vel": 82},
        ]
        flat = {"dens": 0.30, "center": 3, "grid": 0.5, "run_prob": 0.10, "vel": 84}

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

    # Motif from locked base (optional).
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
                for _, p, d, v in picked:
                    p2 = int(min(allowed_sorted, key=lambda ap: abs(int(ap) - int(p)))) if allowed_sorted else int(p)
                    motif.append([0.0, p2, float(max(0.25, min(1.0, d))), int(max(1, min(127, v)))])
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
    step_choices_calm = [-2, -1, 1, 2, 3]
    step_choices_wild = [-4, -3, -2, -1, 1, 2, 3, 4]

    for sec_i in range(4):
        sec = sections[sec_i] if use_story else flat
        bars_in_sec = int(per_section[sec_i])
        dens = float(sec["dens"]) + (0.04 * (float(energy) - 5.0) / 5.0)
        dens = dens * dens_mult
        dens = max(0.14, min(0.86, dens))
        grid = float(sec["grid"])

        for b in range(bars_in_sec):
            bar = bar_cursor + b
            bar_start = float(bar * 4.0)
            slots = [float(round(t, 3)) for t in np.arange(bar_start, bar_start + 4.0, grid)]
            if not slots:
                continue
            # Trumpet: fewer starts, more punch.
            max_notes = int(round(len(slots) * (0.14 + dens * 0.28)))
            max_notes = max(2, min(9, max_notes))
            random.shuffle(slots)
            chosen = sorted(slots[:max_notes])

            for t in chosen:
                strong = abs(t % 1.0) < 0.001
                use_motif = bool(motif) and (bar == 0 or random.random() < 0.25)
                if use_motif:
                    mi = min(chosen.index(t), len(motif) - 1)
                    p = int(motif[mi][1])
                    if random.random() < 0.35:
                        p = _nudge_scale_steps(p, random.choice([-1, 1, 2, -2]))
                elif strong and random.random() < 0.45:
                    p = int(random.choice(targets))
                else:
                    steps = step_choices_wild if is_wild else step_choices_calm
                    if random.random() < (float(sec["run_prob"]) * run_mult):
                        steps = step_choices_wild
                    p = _nudge_scale_steps(last_p, random.choice(steps))

                dur = float(_weighted_choice(dur_pool_main, 0.5))
                vel = int(sec["vel"] + random.randint(-8, 12) + (12 if strong else 0) + theme_profile["accent"])
                _add(t, p, dur, vel)
                last_p = int(p)

            if random.random() < 0.65:
                _add(float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 1.0, int(sec["vel"] + 10))

        bar_cursor += bars_in_sec

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


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


def generate_marimba_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local marimba/mallet solo generator (short + loop-friendly), monophonic.
    Percussive notes with a bit of motif repetition.
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
    register = (max(55, 60 + reg_shift), min(92, 90 + reg_shift))
    allowed = _build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = _build_allowed_notes(60, [0, 3, 5, 7, 10], (60, 90))
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
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.25, 0.5, 0.75, 1.0])

    if is_wild:
        sections = [
            {"dens": 0.52, "center": 2, "grid": 0.25, "run_prob": 0.22, "vel": 90},
            {"dens": 0.58, "center": 3, "grid": 0.25, "run_prob": 0.26, "vel": 94},
            {"dens": 0.66, "center": 4, "grid": 0.25, "run_prob": 0.32, "vel": 100},
            {"dens": 0.54, "center": 2, "grid": 0.25, "run_prob": 0.24, "vel": 92},
        ]
        flat = {"dens": 0.60, "center": 3, "grid": 0.25, "run_prob": 0.28, "vel": 96}
    else:
        sections = [
            {"dens": 0.34, "center": 1, "grid": 0.5, "run_prob": 0.10, "vel": 74},
            {"dens": 0.38, "center": 2, "grid": 0.5, "run_prob": 0.12, "vel": 78},
            {"dens": 0.46, "center": 3, "grid": 0.25, "run_prob": 0.18, "vel": 84},
            {"dens": 0.36, "center": 1, "grid": 0.5, "run_prob": 0.11, "vel": 76},
        ]
        flat = {"dens": 0.40, "center": 2, "grid": 0.5, "run_prob": 0.13, "vel": 80}

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
                    motif.append([0.0, p2, float(max(0.25, min(0.75, d))), int(max(1, min(127, v)))])
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
    for sec_i in range(4):
        sec = sections[sec_i] if use_story else flat
        bars_in_sec = int(per_section[sec_i])
        dens = float(sec["dens"]) + (0.04 * (float(energy) - 5.0) / 5.0)
        dens = dens * dens_mult
        dens = max(0.14, min(0.92, dens))
        grid = float(sec["grid"])

        for b in range(bars_in_sec):
            bar = bar_cursor + b
            bar_start = float(bar * 4.0)
            slots = [float(round(t, 3)) for t in np.arange(bar_start, bar_start + 4.0, grid)]
            if not slots:
                continue
            max_notes = int(round(len(slots) * (0.16 + dens * 0.32)))
            max_notes = max(3, min(14, max_notes))
            random.shuffle(slots)
            chosen = sorted(slots[:max_notes])

            for t in chosen:
                strong = abs(t % 1.0) < 0.001
                use_motif = bool(motif) and (bar == 0 or random.random() < 0.28)
                if use_motif:
                    mi = min(chosen.index(t), len(motif) - 1)
                    p = int(motif[mi][1])
                    if random.random() < 0.35:
                        p = _nudge_scale_steps(p, random.choice([-1, 1, 2, -2]))
                elif strong and random.random() < 0.40:
                    p = int(random.choice(targets))
                else:
                    steps = [-3, -2, -1, 1, 2, 3] if is_wild else [-2, -1, 1, 2]
                    if random.random() < (float(sec["run_prob"]) * run_mult):
                        steps = [-4, -3, -2, -1, 1, 2, 3, 4]
                    p = _nudge_scale_steps(last_p, random.choice(steps))

                dur = float(_weighted_choice(dur_pool_main, 0.25))
                vel = int(sec["vel"] + random.randint(-10, 12) + (10 if strong else 0) + theme_profile["accent"])
                _add(t, p, dur, vel)
                last_p = int(p)

            if random.random() < 0.55:
                _add(float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 0.75, int(sec["vel"] + 8))

        bar_cursor += bars_in_sec

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


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


def generate_acoustic_bass_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local acoustic bass solo generator (short + loop-friendly), monophonic.

    Goal: DAW-friendly bassline/solo that sits in the pocket:
      - fewer notes
      - strong-beat targeting
      - mostly stepwise motion, rare leaps
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

    # Bass register: roughly E1..E3, keep it tight.
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

    char_s = str(character or "KlidnĂ©").strip().lower()
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

    # Motif source: reuse 1 bar worth as a "signature" for locked variations.
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
        # Simple pocket motif: root-ish tones on strong beats.
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

    def _pick_pitch(last_pitch: int | None, leap_limit: int) -> int:
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

            # Motif repeat.
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

            # Extra pocket notes.
            for k in range(steps_per_bar):
                t = float(round(bar_start + k * grid, 3))
                if t >= beats_total:
                    continue
                strong = abs((t % 1.0)) < 1e-6
                # Prefer strong beats; keep space.
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

            # Bar ending cadence.
            if random.random() < 0.50:
                out.append([float(round(bar_start + 3.0, 3)), int(random.choice(targets)), 1.0, int(sec["vel"] + 12)])

        bar_cursor += int(bars_in_sec)

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    # Keep monophonic: no overlaps.
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


def smart_generate(
    num_bars,
    theme="Freestyle",
    energy=5,
    style=None,
    boombap_variation=None,
    sax_character=None,
    sax_story=None,
    piano_character=None,
    piano_story=None,
    trumpet_character=None,
    trumpet_story=None,
    flute_character=None,
    flute_story=None,
    rhodes_character=None,
    rhodes_story=None,
    marimba_character=None,
    marimba_story=None,
    vibraphone_character=None,
    vibraphone_story=None,
    acoustic_bass_character=None,
    acoustic_bass_story=None,
    solo_motif_source=None,
):
    from core.generator.melody_generate import smart_generate as _smart_generate_impl

    return _smart_generate_impl(
        num_bars,
        theme=theme,
        energy=energy,
        style=style,
        boombap_variation=boombap_variation,
        sax_character=sax_character,
        sax_story=sax_story,
        piano_character=piano_character,
        piano_story=piano_story,
        trumpet_character=trumpet_character,
        trumpet_story=trumpet_story,
        flute_character=flute_character,
        flute_story=flute_story,
        rhodes_character=rhodes_character,
        rhodes_story=rhodes_story,
        marimba_character=marimba_character,
        marimba_story=marimba_story,
        vibraphone_character=vibraphone_character,
        vibraphone_story=vibraphone_story,
        acoustic_bass_character=acoustic_bass_character,
        acoustic_bass_story=acoustic_bass_story,
        solo_motif_source=solo_motif_source,
    )


def chord_generate(num_bars, theme="Freestyle", energy=5):
    from core.generator.chords import chord_generate as _chord_generate_impl

    return _chord_generate_impl(num_bars, theme=theme, energy=energy)


def call_chatgpt_ai(
    api_key,
    user_prompt,
    bars,
    chords_mode,
    theme_name,
    secret_rule="",
    energy=5,
    role="Lead",
    creativity=50,
    counter_style="Smooth",
):
    from core.generator.ai_generate import call_chatgpt_ai as _call_chatgpt_ai_impl

    return _call_chatgpt_ai_impl(
        api_key,
        user_prompt,
        bars,
        chords_mode,
        theme_name,
        secret_rule=secret_rule,
        energy=energy,
        role=role,
        creativity=creativity,
        counter_style=counter_style,
    )


# Compatibility aliases for bridge modules that still call legacy symbols.
_smart_generate_legacy = smart_generate
_generate_sax_solo_legacy = generate_sax_solo
_generate_piano_solo_legacy = generate_piano_solo
_generate_trumpet_solo_legacy = generate_trumpet_solo
_generate_flute_solo_legacy = generate_flute_solo
_generate_marimba_solo_legacy = generate_marimba_solo
_generate_vibraphone_solo_legacy = generate_vibraphone_solo
_generate_acoustic_bass_solo_legacy = generate_acoustic_bass_solo




# -*- coding: utf-8 -*-

import random
import numpy as np

from core.generator.theme_profiles import build_theme_profile, get_producer_profile, split_theme
from core.generator.solos import _build_allowed_notes, _solo_duration_pool, _solo_theme_mods, _weighted_choice

_split_theme = split_theme
_get_producer_profile = get_producer_profile
_build_theme_profile = build_theme_profile

def generate_sax_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    """
    Local sax solo generator (short + loop-friendly).

    Shape (scaled to bars, 4..8 recommended):
      - Bez příběhu: konzistentní charakter po celou dobu (klidné nebo divoké)
      - Příběh: jemný vývoj (intro -> develop -> peak -> outro) bez brutálního zlomu

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

    char_s = str(character or "Klidné").strip().lower()
    is_wild = char_s.startswith("div")  # divoke/divoké
    use_story = bool(story) if story is not None else False
    dur_mode = str(solo_mods.get("dur_mode") or "normal")
    dens_mult = float(solo_mods.get("density_mult") or 1.0)
    run_mult = float(solo_mods.get("run_mult") or 1.0)
    center_add = int(solo_mods.get("center_steps") or 0)

    # Section settings (intro/develop/peak/outro).
    # IMPORTANT: keep the contrast mild so the second half doesn't sound like a different song.
    if is_wild:
        # "Divoké" overall.
        sections = [
            {"dens": 0.48, "center": 3, "grid": 0.5, "run_prob": 0.14, "vel": 88},
            {"dens": 0.54, "center": 4, "grid": 0.5, "run_prob": 0.18, "vel": 92},
            {"dens": 0.62, "center": 6, "grid": 0.25, "run_prob": 0.26, "vel": 98},
            {"dens": 0.50, "center": 3, "grid": 0.5, "run_prob": 0.16, "vel": 90},
        ]
        flat_section = {"dens": 0.56, "center": 5, "grid": 0.5, "run_prob": 0.22, "vel": 94}
    else:
        # "Klidné" overall.
        sections = [
            {"dens": 0.26, "center": 0, "grid": 0.5, "run_prob": 0.04, "vel": 72},
            {"dens": 0.30, "center": 1, "grid": 0.5, "run_prob": 0.06, "vel": 76},
            {"dens": 0.38, "center": 2, "grid": 0.5, "run_prob": 0.10, "vel": 82},
            {"dens": 0.28, "center": 0, "grid": 0.5, "run_prob": 0.05, "vel": 74},
        ]
        flat_section = {"dens": 0.30, "center": 1, "grid": 0.5, "run_prob": 0.06, "vel": 76}

    out = []
    beats_total = float(total_bars * 4)
    dur_pool_main = _solo_duration_pool(theme_profile, dur_mode, base=[0.25, 0.5, 1.0, 1.5])
    dur_pool_peak = _solo_duration_pool(theme_profile, "short" if dur_mode == "short" else "normal", base=[0.25, 0.25, 0.5, 0.5, 1.0])

    def _add_note(start_t: float, pitch: int, dur: float, vel: int):
        if start_t < 0 or start_t >= beats_total:
            return
        dur = float(max(0.25, dur))
        out.append([float(round(start_t, 3)), int(pitch), float(round(dur, 3)), int(max(1, min(127, vel)))])

    # Distribute bars across 4 sections only when "Příběh" is enabled.
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





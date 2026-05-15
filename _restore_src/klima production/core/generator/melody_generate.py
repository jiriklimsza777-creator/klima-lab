# -*- coding: utf-8 -*-

import random

import numpy as np


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
    import Generator_not as legacy

    style_s = str(style or "").strip().lower()
    if style_s.startswith("klas") or style_s in {"classic", "legacy", "old"}:
        return legacy.smart_generate_classic(num_bars, theme=theme, energy=energy)
    if style_s.startswith("sax"):
        return legacy.generate_sax_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=sax_character,
            story=sax_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("piano"):
        return legacy.generate_piano_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=piano_character,
            story=piano_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("rhodes"):
        return legacy.generate_piano_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=rhodes_character,
            story=rhodes_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("trumpet"):
        return legacy.generate_trumpet_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=trumpet_character,
            story=trumpet_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("flute"):
        return legacy.generate_flute_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=flute_character,
            story=flute_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("marimba"):
        return legacy.generate_marimba_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=marimba_character,
            story=marimba_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("vib") or style_s.startswith("vibra"):
        return legacy.generate_vibraphone_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=vibraphone_character,
            story=vibraphone_story,
            motif_source=solo_motif_source,
        )
    if style_s.startswith("akust") or style_s.startswith("acoustic bass") or style_s.startswith("acoustic_bass"):
        return legacy.generate_acoustic_bass_solo(
            theme=theme,
            bars=int(num_bars),
            energy=energy,
            character=acoustic_bass_character,
            story=acoustic_bass_story,
            motif_source=solo_motif_source,
        )

    producer, theme_name = legacy._split_theme(theme)
    producer_profile = legacy._get_producer_profile(producer)
    theme_profile = legacy._build_theme_profile(theme_name)

    root = random.choice([55, 57, 58, 60, 62]) + theme_profile["register_shift"]
    register_low, register_high = producer_profile["register"]
    register = (max(48, register_low + theme_profile["register_shift"]), min(84, register_high + theme_profile["register_shift"]))
    allowed = legacy._build_allowed_notes(root, theme_profile["scale"], register)
    if not allowed:
        allowed = legacy._build_allowed_notes(60, [0, 3, 5, 7, 10], (52, 72))

    force_boombap_loop = ("boombap" in style_s) or ("loop" in style_s)
    boombap_producers = {"DJ Premier", "Pete Rock", "J Dilla", "MF DOOM", "Apollo Brown", "9th Wonder", "Q-Tip", "Havoc", "RZA"}
    boombap_mode = (
        producer in boombap_producers
        or "boom" in theme_name.lower()
        or "bap" in theme_name.lower()
        or "street" in theme_name.lower()
    )
    boombap_mode = boombap_mode or force_boombap_loop

    motif_length = legacy._weighted_choice(producer_profile["motif"], 2.0)
    if boombap_mode and num_bars >= 2:
        motif_length = 8.0
    elif boombap_mode:
        motif_length = 4.0
    step = producer_profile["step"]
    density = min(0.95, producer_profile["density"] * theme_profile["density"] * (0.65 + energy / 12.0))
    swing_amount = producer_profile["swing"] * theme_profile["swing"]
    durations = legacy._merge_unique(producer_profile["durations"] + theme_profile["durations"])
    jump_limit = max(2, producer_profile["jump"] + theme_profile["jump"])

    motif = []
    last_pitch = None
    accent_boost = theme_profile["accent"]
    allowed_sorted = sorted(allowed)
    home_pitch = min(allowed_sorted, key=lambda p: abs(p - root)) if allowed_sorted else root
    home_idx = allowed_sorted.index(home_pitch) if allowed_sorted else 0
    cadence_candidates = []
    for off in (0, -2, 2, -4, 4):
        idx = max(0, min(len(allowed_sorted) - 1, home_idx + off)) if allowed_sorted else 0
        if allowed_sorted:
            cadence_candidates.append(int(allowed_sorted[idx]))
    cadence_candidates = list(dict.fromkeys(cadence_candidates)) or [int(home_pitch)]

    def _nearest_allowed_pitch(target: int) -> int:
        if not allowed_sorted:
            return int(target)
        return int(min(allowed_sorted, key=lambda p: abs(int(p) - int(target))))

    def _nudge_scale_steps(pitch: int, steps: int) -> int:
        if not allowed_sorted:
            return int(pitch)
        p = int(pitch)
        idx = min(range(len(allowed_sorted)), key=lambda i: abs(int(allowed_sorted[i]) - p))
        idx2 = max(0, min(len(allowed_sorted) - 1, idx + int(steps)))
        return int(allowed_sorted[idx2])

    times = [float(round(t, 3)) for t in np.arange(0, motif_length, step)]
    if not times:
        times = [0.0]

    bars_in_motif = max(1.0, motif_length / 4.0)
    if boombap_mode:
        desired_notes = int(round(bars_in_motif * (2.2 + density * 1.6)))
        desired_notes = max(2, min(int(bars_in_motif * 5), desired_notes))
    else:
        desired_notes = int(round(bars_in_motif * (3.0 + density * 2.8)))
        desired_notes = max(2, min(int(bars_in_motif * 8), desired_notes))

    weights = []
    for t in times:
        down = abs(t % 1.0) < 0.001
        offbeat = abs((t % 1.0) - 0.5) < 0.001
        w = 1.0
        if down:
            w *= 1.25
        if offbeat:
            w *= (1.45 if boombap_mode else 1.15)
        if not down and not offbeat:
            w *= (0.85 if boombap_mode else 1.0)
        weights.append(w)

    try:
        vv = 0.55 if boombap_variation is None else float(boombap_variation) / 100.0
    except Exception:
        vv = 0.55
    vv = max(0.0, min(1.0, vv))

    loop_shift = float(producer_profile.get("loop_shift", 0.18))
    loop_drop = float(producer_profile.get("loop_drop", 0.12))
    loop_contrast = float(producer_profile.get("loop_contrast", 0.18))
    loop_shift = max(0.0, min(0.55, loop_shift))
    loop_drop = max(0.0, min(0.55, loop_drop))
    loop_contrast = max(0.0, min(0.55, loop_contrast))

    vv_eff = min(1.0, vv + (0.14 if motif_length <= 4.0 else 0.0) + loop_contrast)

    if boombap_mode and motif_length >= 4.0:
        phrase_len = motif_length / 2.0
        times_call = [t for t in times if t < phrase_len - 1e-9]
        if not times_call:
            times_call = [0.0]

        desired_call = max(1, min(len(times_call), int(round(desired_notes * 0.55))))

        w_call = []
        for t in times_call:
            down = abs(t % 1.0) < 0.001
            offbeat = abs((t % 1.0) - 0.5) < 0.001
            w = 1.0
            if down:
                w *= 1.25
            if offbeat:
                w *= 1.45
            if not down and not offbeat:
                w *= 0.85
            w_call.append(w)

        chosen_call = []
        pool_t = list(times_call)
        pool_w = list(w_call)
        for _ in range(min(desired_call, len(pool_t))):
            pick = random.choices(pool_t, weights=pool_w, k=1)[0]
            idx = pool_t.index(pick)
            chosen_call.append(pick)
            pool_t.pop(idx)
            pool_w.pop(idx)
        chosen_call.sort()

        call_notes = []
        for t in chosen_call:
            strong_beat = abs(t % 1.0) < 0.001
            if last_pitch is None and strong_beat:
                pitch = random.choice(cadence_candidates)
            elif strong_beat and (abs(t % 2.0) < 0.001) and random.random() < 0.55:
                pitch = random.choice(cadence_candidates)
            else:
                pitch = legacy._choose_next_pitch(last_pitch, allowed, jump_limit)

            if strong_beat:
                duration = legacy._weighted_choice([1.0, 1.5, 2.0] + durations, 1.0)
                velocity = random.randint(74, 108) + 18 + accent_boost
            else:
                duration = legacy._weighted_choice([0.25, 0.5, 0.5, 1.0] + durations, 0.5)
                velocity = random.randint(58, 98) + accent_boost

            swing = swing_amount if (t % 0.5 != 0) else 0.0
            note = [float(round(t + swing, 3)), int(pitch), float(duration), int(max(1, min(127, velocity)))]
            call_notes.append(note)
            last_pitch = int(pitch)

        if not call_notes:
            call_notes = [[0.0, int(random.choice(allowed)), 0.5, 90]]

        response_notes = []
        shift_unit = float(step if float(step) <= 0.5 else 0.5)
        min_keep_prob = 0.05
        for start, pitch, dur, vel in call_notes:
            t2 = float(start + phrase_len)
            if t2 >= motif_length:
                continue

            roll = random.random()
            keep_prob = max(min_keep_prob, 0.65 - (0.60 * vv_eff))
            if roll < keep_prob:
                p2 = int(pitch)
            elif roll < 0.85:
                big_step_prob = 0.10 + (0.55 * vv_eff)
                if random.random() < big_step_prob:
                    p2 = _nudge_scale_steps(int(pitch), steps=-4 if random.random() < 0.65 else 4)
                else:
                    p2 = _nudge_scale_steps(int(pitch), steps=-2 if random.random() < 0.60 else 2)
            else:
                cc = [int(c) for c in cadence_candidates if int(c) != int(pitch)]
                p2 = _nearest_allowed_pitch(int(random.choice(cc or cadence_candidates)))

            strong_beat = abs(t2 % 1.0) < 0.001
            cadence_on_strong = 0.62 - (0.50 * vv_eff)
            if strong_beat and random.random() < cadence_on_strong:
                cc = [int(c) for c in cadence_candidates if int(c) != int(pitch)]
                p2 = _nearest_allowed_pitch(int(random.choice(cc or cadence_candidates)))

            if vv_eff >= 0.65 and int(p2) == int(pitch):
                p2 = _nudge_scale_steps(int(pitch), steps=-3 if random.random() < 0.65 else -2)

            vel2 = int(max(1, min(127, int(vel) - random.randint(4, 14))))
            dur2 = float(dur)
            if random.random() < 0.35:
                dur2 = float(legacy._weighted_choice([0.25, 0.5, 1.0] + durations, dur2))

            if vv_eff >= 0.28 and random.random() < (0.10 + 0.35 * vv_eff + loop_drop):
                continue

            if vv_eff >= 0.45 and random.random() < (0.18 + 0.40 * vv_eff + loop_shift):
                shift = random.choices([-shift_unit, 0.0, shift_unit], weights=[1.0, 1.4, 1.0], k=1)[0]
                t2 = float(t2 + shift)
                t2 = max(float(phrase_len), min(float(motif_length - step), t2))
                strong_beat = abs(t2 % 1.0) < 0.001

            response_notes.append([float(round(t2, 3)), int(p2), float(dur2), vel2])

        if vv_eff >= 0.65:
            tag_t = float(round(motif_length - max(shift_unit, 0.5), 3))
            if tag_t >= phrase_len and all(abs(float(n[0]) - tag_t) > 1e-6 for n in response_notes):
                tag_pitch = int(_nearest_allowed_pitch(int(random.choice(cadence_candidates))))
                response_notes.append([tag_t, tag_pitch, float(legacy._weighted_choice([0.25, 0.5], 0.25)), int(max(1, min(127, 96 + accent_boost)))])

        end_t = float(round(motif_length - step, 3))
        end_prob = 0.55 + (0.35 * (1.0 - vv))
        if end_t > 0 and random.random() < end_prob:
            response_notes.append([end_t, int(random.choice(cadence_candidates)), float(legacy._weighted_choice([0.5, 1.0, 1.5], 1.0)), int(max(1, min(127, 92 + accent_boost)))])

        motif = sorted(call_notes + response_notes, key=lambda x: float(x[0]))
    else:
        chosen_times = []
        pool_times = list(times)
        pool_weights = list(weights)
        for _ in range(min(desired_notes, len(pool_times))):
            pick = random.choices(pool_times, weights=pool_weights, k=1)[0]
            idx = pool_times.index(pick)
            chosen_times.append(pick)
            pool_times.pop(idx)
            pool_weights.pop(idx)
        chosen_times.sort()

        for t in chosen_times:
            strong_beat = abs(t % 1.0) < 0.001
            if last_pitch is None and strong_beat:
                pitch = random.choice(cadence_candidates)
            elif strong_beat and (abs(t % 2.0) < 0.001) and random.random() < (0.55 if boombap_mode else 0.35):
                pitch = random.choice(cadence_candidates)
            else:
                pitch = legacy._choose_next_pitch(last_pitch, allowed, jump_limit)

            if strong_beat:
                duration = legacy._weighted_choice([1.0, 1.5, 2.0] + durations, 1.0) if boombap_mode else legacy._weighted_choice(durations, 0.5)
                velocity = random.randint(74, 108) + (18 if boombap_mode else 10) + accent_boost
            else:
                duration = legacy._weighted_choice([0.25, 0.5, 0.5, 1.0] + durations, 0.5) if boombap_mode else legacy._weighted_choice(durations, 0.5)
                velocity = random.randint(58, 98) + accent_boost

            swing = swing_amount if (t % 0.5 != 0) else 0.0
            motif.append([float(round(t + swing, 3)), int(pitch), float(duration), int(max(1, min(127, velocity)))])
            last_pitch = pitch

    if not motif:
        motif.append([0.0, random.choice(allowed), 0.5, 90])

    data = []
    repeats = int(np.ceil((num_bars * 4) / motif_length))
    for bar in range(repeats):
        mutate_idx = None
        if motif and random.random() < (0.55 if boombap_mode else 0.35):
            mutate_idx = random.randrange(0, len(motif))
        for note_idx, note in enumerate(motif):
            start_time = note[0] + bar * motif_length
            if start_time < num_bars * 4:
                variation_roll = random.random()
                new_pitch = note[1]
                new_duration = note[2]
                can_mutate = mutate_idx is not None and note_idx == mutate_idx
                if can_mutate:
                    if variation_roll < (0.10 if boombap_mode else 0.18):
                        new_pitch = legacy._choose_next_pitch(note[1], allowed, max(2, jump_limit - 1))
                    if variation_roll > (0.90 if boombap_mode else 0.82):
                        new_duration = legacy._weighted_choice(durations, note[2])
                data.append([float(round(start_time, 3)), int(new_pitch), float(new_duration), int(note[3])])

    data.sort(key=lambda x: x[0])
    return data

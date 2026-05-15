# -*- coding: utf-8 -*-

import json
import random
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from core.generator.chords import build_chord_loop


def _extract_note_array(content):
    if not content:
        return None

    stripped = content.strip()
    if stripped.startswith("["):
        return stripped

    match = re.search(r"\[\s*\[.*\]\s*\]", stripped, re.DOTALL)
    return match.group() if match else None


def _clamp_int(v, lo, hi):
    return int(max(lo, min(hi, int(v))))


def _group_by_bar(notes, bars):
    groups = {i: [] for i in range(int(bars))}
    for n in notes:
        try:
            start = float(n[0])
        except Exception:
            continue
        bar = int(start // 4.0)
        if 0 <= bar < int(bars):
            groups[bar].append(n)
    return groups


def _prune_monophonic(notes):
    by_start = {}
    for n in notes:
        start = float(n[0])
        vel = int(n[3]) if len(n) > 3 else 80
        prev = by_start.get(start)
        if prev is None or vel > (int(prev[3]) if len(prev) > 3 else 80):
            by_start[start] = n
    return list(by_start.values())


def _limit_density(notes, bars, role, counter_style, creativity):
    role = (role or "Lead").lower()
    counter_style = (counter_style or "smooth").lower()
    creativity = _clamp_int(creativity, 0, 100)

    base = 5
    if role == "bass":
        base = 3
    elif role == "counter":
        base = 4 if counter_style != "busy" else 7
    elif role == "lead":
        base = 6

    max_per_bar = int(max(2, round(base + (creativity / 100.0) * 2)))
    groups = _group_by_bar(notes, bars)
    kept = []

    for _, items in groups.items():
        items_sorted = sorted(
            items,
            key=lambda x: (int(x[3]) if len(x) > 3 else 80, float(x[2]) if len(x) > 2 else 0.25),
            reverse=True,
        )
        kept.extend(items_sorted[:max_per_bar])

    if role in {"lead", "counter", "bass"}:
        kept = _prune_monophonic(kept)

    kept.sort(key=lambda x: (float(x[0]), int(x[1])))
    return kept


def _normalize_ai_chords(raw_notes, theme_name, bars, energy, creativity):
    if not raw_notes:
        return build_chord_loop(theme_name, bars, energy=energy)

    bars = int(bars)
    creativity = _clamp_int(creativity, 0, 100)
    groups = _group_by_bar(raw_notes, bars)
    cleaned = []
    for bar in range(bars):
        start = float(bar * 4.0)
        items = groups.get(bar, [])
        if not items:
            continue

        items_sorted = sorted(items, key=lambda x: (int(x[3]) if len(x) > 3 else 80), reverse=True)
        picked = []
        used_pitches = set()
        for n in items_sorted:
            pitch = int(n[1])
            if pitch in used_pitches:
                continue
            used_pitches.add(pitch)
            picked.append(pitch)
            if len(picked) >= (4 if creativity > 60 else 3):
                break

        if len(picked) < 3:
            continue

        picked.sort()
        base_vel = int(items_sorted[0][3]) if len(items_sorted[0]) > 3 else 85
        for idx, pitch in enumerate(picked):
            vel = _clamp_int(base_vel - idx * 7, 1, 127)
            cleaned.append([start, int(pitch), 4.0, int(vel)])

    if len(cleaned) < max(3, bars - 1) * 3:
        return build_chord_loop(theme_name, bars, energy=energy)

    cleaned.sort(key=lambda x: (x[0], x[1]))
    return cleaned


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
    if not api_key or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=api_key.strip())
        beats = bars * 4
        mode_label = "AKORDY (polyfonie)" if chords_mode else "MELODIE (monofonni/lead)"
        mode_rule = (
            "Kazdy harmonicky okamzik musi obsahovat vice soucasne znejicich tonu. Vracej skutecne akordy, ne jen jednonotovy lead."
            if chords_mode
            else "Generuj pouze jednu hlavni notu v jeden cas. Nepis bloky akordu ani vice soucasnych tonu."
        )

        creativity = max(0, min(100, int(creativity)))
        role = str(role or "Lead")
        counter_style = str(counter_style or "Smooth")
        groove_hint = (
            "HODNE TIGHT groove: drz vetsinu startu na 1/8 nebo 1/16 mrizce, minimum mikro-posunu a minimum chaosu."
            if creativity <= 25
            else (
                "BALANCE groove/kreativita: pouzivej swing a synkopy, ale zachovej citelny motiv."
                if creativity <= 70
                else "HODNE KREATIVNI: vic synkop, vic variaci motivu, obcas mikro-posun startu (stale hudebne)."
            )
        )

        role_rule = ""
        if chords_mode or role.lower() == "chords":
            role_rule = (
                "ROLE: CHORDS. Vytvor konkretni opakovatelnou SMYCKU.\n"
                "- Presne 1 akord na takt.\n"
                "- Starty akordu presne na 0, 4, 8, 12, ... (po 4 beatech).\n"
                "- Kazdy akord ma 3 az 4 soucasne tony.\n"
                "- Delka kazdeho akordu presne 4 beaty.\n"
                "- Zadne arpeggio, zadna melodicka navrch.\n"
                "- Smycka se musi po 4 taktech opakovat (s malou variaci max 1 ton)."
            )
        elif role.lower() == "bass":
            role_rule = "ROLE: BASS. Pis nizke tony (MIDI pitch typicky 36-55), jednoduche rytmy, mene not, spise koreny/kvinty."
        elif role.lower() == "counter":
            if counter_style.lower() == "busy":
                role_rule = "ROLE: COUNTER (Busy). Odpovidej leadu, ale bud aktivnejsi: kratsi fraze, vic not, stale nepln kazdy beat."
            else:
                role_rule = "ROLE: COUNTER (Smooth). Call & response: nech hodne pauz, zacej spise na offbeatech (napr. +0.5, +1.0), pouzivej delsi tony a mene not."
        else:
            role_rule = "ROLE: LEAD. Silny 1-2 taktovy motiv, opakuj s malymi variacemi, citelna melodie."

        system_instructions = (
            "Jsi MIDI architekt a hudebni teoretik. Generuj pouze JSON pole not.\n\n"
            "HUDEBNI PRAVIDLA:\n"
            "1. Pouzivej pentatoniku nebo bluesovou stupnici.\n"
            "2. Tvor synkopy a lehky swing.\n"
            "3. Postav 1-2 taktovy motiv a opakuj ho s malymi variacemi.\n"
            "4. Men velocity, at vysledek neni plochy.\n\n"
            f"KONTEXT: Tema: {theme_name}. Styl: {user_prompt or 'Freestyle'}. Energie: {energy}/10. Delka: {beats} beatu.\n"
            f"REZIM: {mode_label}.\n"
            f"SPECIALNI PRAVIDLO: {mode_rule}\n"
            f"{role_rule}\n"
            f"GROOVE: {groove_hint}\n"
            "VYSTUP: Pouze validni JSON ve formatu [[start, pitch, duration, velocity], ...]. Bez dalsiho textu."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_instructions}],
            temperature=0.8,
        )

        content = response.choices[0].message.content
        note_array = _extract_note_array(content)
        if not note_array:
            return None

        raw_data = json.loads(note_array)
        fixed = []
        for note in raw_data:
            if not isinstance(note, (list, tuple)) or len(note) < 3:
                continue

            start = round(max(0, float(note[0])), 3)
            pitch = int(note[1])
            duration = round(max(0.125, float(note[2])), 3)
            velocity = int(note[3]) if len(note) > 3 else random.randint(75, 105)
            velocity = max(1, min(127, velocity))

            if 12 <= pitch <= 127:
                if role.lower() == "bass" and pitch > 60:
                    continue
                fixed.append([start, pitch, duration, velocity])

        fixed.sort(key=lambda x: (x[0], x[1]))

        if chords_mode or role.lower() == "chords":
            return _normalize_ai_chords(fixed, theme_name, bars, energy=energy, creativity=creativity)

        fixed = _limit_density(fixed, bars, role, counter_style, creativity)
        return fixed or None
    except Exception as e:
        print(f"Chyba core.generator.ai_generate: {e}")
        return None

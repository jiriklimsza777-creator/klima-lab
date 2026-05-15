# -*- coding: utf-8 -*-

import random


def apply_humanize(notes, preset: str, seed: int = 0, bars: int | None = None):
    """
    Notes format: [start, pitch, dur, vel?] where start/dur are in beats.
    Returns a new list; deterministic based on seed.
    """
    if not notes or not preset or preset == "Off":
        return notes

    preset = str(preset)
    cfg = {
        "Tight": {"swing": 0.03, "jitter": 0.010, "vel": 3},
        "Groove": {"swing": 0.06, "jitter": 0.020, "vel": 6},
        "Loose": {"swing": 0.09, "jitter": 0.030, "vel": 10},
    }.get(preset, None)

    if not cfg:
        return notes

    rng = random.Random(int(seed) & 0xFFFFFFFF)
    swing = float(cfg["swing"])
    jitter = float(cfg["jitter"])
    vel_rand = int(cfg["vel"])

    out = []
    max_time = float(bars * 4) if bars else None
    grid = 0.5  # 1/8 swing

    for i, n in enumerate(notes):
        if len(n) < 3:
            continue
        start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90

        # Swing: delay off-eighth positions.
        pos = start / grid
        pos_round = round(pos)
        if abs(pos - pos_round) <= 0.03:
            if int(pos_round) % 2 == 1:
                start += swing

        # Jitter (deterministic).
        start += rng.uniform(-jitter, jitter)
        start = max(0.0, round(start, 4))

        if max_time is not None:
            start = min(max_time - 0.01, start)

        # Velocity variation.
        if vel_rand > 0:
            vel = int(max(1, min(127, vel + rng.randint(-vel_rand, vel_rand))))

        dur = max(0.05, float(dur))
        out.append([start, pitch, dur, vel])

    out.sort(key=lambda x: (x[0], x[1]))
    return out


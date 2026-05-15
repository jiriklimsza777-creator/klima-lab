# -*- coding: utf-8 -*-

"""
Audio caching helpers.

Goal: keep the UI identical, but avoid re-synthesising the same audio on every Streamlit rerun.
"""

from __future__ import annotations

import streamlit as st

import Zvuk_a_export as sound


def _norm_melody(melody):
    """
    Convert a melody list into a small, hashable tuple-of-tuples suitable for st.cache_data.
    Also clamps/rounds values a bit to reduce cache misses from tiny float differences.
    """
    if not melody:
        return tuple()

    out = []
    for n in melody:
        if not isinstance(n, (list, tuple)) or len(n) < 3:
            continue
        try:
            start = round(float(n[0]), 4)
            pitch = int(n[1])
            dur = round(float(n[2]), 4)
            vel = int(n[3]) if len(n) > 3 else 100
        except Exception:
            continue

        if dur <= 0:
            continue
        vel = max(1, min(127, vel))
        pitch = max(0, min(127, pitch))
        out.append((start, pitch, dur, vel))

    out.sort(key=lambda x: (x[0], x[1]))
    return tuple(out)


@st.cache_data(show_spinner=False, max_entries=128)
def _synth_cached(melody_tup, engine_type: str, instrument_id: int, octave_shift: int, bpm: int) -> bytes:
    melody = [list(n) for n in melody_tup]
    return sound.synthesise_full_audio(
        melody,
        engine_type=str(engine_type),
        instrument_id=int(instrument_id),
        octave_shift=int(octave_shift),
        bpm=int(bpm),
    )


def synthesise_full_audio_cached(melody, engine_type: str, instrument_id: int, octave_shift: int = 0, bpm: int = 120) -> bytes:
    return _synth_cached(_norm_melody(melody), str(engine_type), int(instrument_id), int(octave_shift), int(bpm))


@st.cache_data(show_spinner=False, max_entries=16)
def prep_import_beat_wav_cached(wav_bytes: bytes, target_sr: int, gain: float) -> bytes:
    """
    Import beat prep is CPU-heavy (decode/resample). Cache it across reruns.
    Note: expects WAV bytes (not MP3).
    """
    try:
        beat_wav = sound.resample_wav_bytes(wav_bytes, int(target_sr))
        return sound.apply_gain_wav_bytes(beat_wav, gain=float(gain))
    except Exception:
        return b""

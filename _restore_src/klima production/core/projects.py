# -*- coding: utf-8 -*-

import random

import streamlit as st

from app.config import ENGINE_LAB, LAB_WAVES, STUDIO_INSTRUMENTS


def default_instrument_for_engine():
    return "Acoustic Grand Piano" if st.session_state.engine_type != ENGINE_LAB else "Sinus"


def create_project(
    title,
    theme,
    melody,
    instrument_name=None,
    source="generated",
    layers=None,
    bars=None,
    seed=None,
    locked=False,
    humanize="Off",
    note_density=None,
    note_role=None,
    melody_style=None,
    boombap_variation=None,
    app_version=None,
):
    instrument_name = instrument_name or default_instrument_for_engine()
    return {
        "title": title,
        "theme": theme,
        "main_instrument": instrument_name,
        "melody": melody,
        "layers": layers or [],
        "source": source,
        "bars": int(bars) if bars is not None else None,
        "seed": int(seed) if seed is not None else random.randint(1, 1_000_000_000),
        "locked": bool(locked),
        "humanize": str(humanize or "Off"),
        "note_density": str(note_density) if note_density is not None else None,
        "note_role": str(note_role) if note_role is not None else None,
        "melody_style": str(melody_style) if melody_style is not None else None,
        "boombap_variation": int(boombap_variation) if boombap_variation is not None else None,
        "app_version": str(app_version) if app_version is not None else None,
    }


def normalize_project_payload(raw_payload, fallback_title, fallback_theme, fallback_instrument):
    if isinstance(raw_payload, dict):
        melody = raw_payload.get("melody") or raw_payload.get("base_melody") or []
        layers = raw_payload.get("layers", [])
        normalized_layers = []
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            normalized_layers.append(
                {
                    "instrument": layer.get("instrument", "Alto Sax"),
                    "melody": layer.get("melody", []),
                }
            )
        project = create_project(
            raw_payload.get("title", fallback_title),
            raw_payload.get("theme", fallback_theme),
            melody,
            raw_payload.get("main_instrument", fallback_instrument),
            source="archive",
            layers=normalized_layers,
            bars=raw_payload.get("bars"),
            seed=raw_payload.get("seed"),
            locked=raw_payload.get("locked", False),
            humanize=raw_payload.get("humanize", "Off"),
            note_density=raw_payload.get("note_density"),
            note_role=raw_payload.get("note_role"),
            melody_style=raw_payload.get("melody_style"),
            boombap_variation=raw_payload.get("boombap_variation"),
            app_version=raw_payload.get("app_version"),
        )
        # Backward-compat: if missing, keep current defaults (Lead/Normal)
        return project

    return create_project(fallback_title, fallback_theme, raw_payload, fallback_instrument, source="archive", layers=[])


def project_to_payload(project):
    return {
        "title": project["title"],
        "theme": project["theme"],
        "main_instrument": project["main_instrument"],
        "melody": project["melody"],
        "layers": project.get("layers", []),
        "bars": project.get("bars"),
        "seed": project.get("seed"),
        "locked": project.get("locked", False),
        "humanize": project.get("humanize", "Off"),
        "note_density": project.get("note_density"),
        "note_role": project.get("note_role"),
        "melody_style": project.get("melody_style"),
        "boombap_variation": project.get("boombap_variation"),
        "app_version": project.get("app_version"),
    }


def get_combined_notes(project):
    notes = list(project.get("melody", []))
    for layer in project.get("layers", []):
        notes.extend(layer.get("melody", []))
    return sorted(notes, key=lambda x: (x[0], x[1]))


def build_audio_parts(project, octave_shift):
    parts = []

    if st.session_state.engine_type == ENGINE_LAB:
        main_instr_id = LAB_WAVES.get(project["main_instrument"], 0)
    else:
        main_instr_id = STUDIO_INSTRUMENTS.get(project["main_instrument"], 0)

    parts.append(
        {
            "melody": project["melody"],
            "engine_type": st.session_state.engine_type,
            "instrument_id": main_instr_id,
            "octave_shift": octave_shift,
        }
    )

    for layer in project.get("layers", []):
        layer_instr = layer["instrument"]
        if st.session_state.engine_type == ENGINE_LAB:
            instr_id = LAB_WAVES.get(layer_instr, 0)
        else:
            instr_id = STUDIO_INSTRUMENTS.get(layer_instr, 0)
        parts.append(
            {
                "melody": layer["melody"],
                "engine_type": st.session_state.engine_type,
                "instrument_id": instr_id,
                "octave_shift": octave_shift,
            }
        )

    return parts


def _get_octave_key(index):
    return f"oct_project_{index}"


def ensure_project_octave(index):
    octave_key = _get_octave_key(index)
    if octave_key not in st.session_state:
        st.session_state[octave_key] = 0
    return octave_key

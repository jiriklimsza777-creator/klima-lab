# -*- coding: utf-8 -*-

import streamlit as st

from app_config import ENGINE_LAB, LAB_WAVES, STUDIO_INSTRUMENTS


def default_instrument_for_engine():
    return "Acoustic Grand Piano" if st.session_state.engine_type != ENGINE_LAB else "Sinus"


def create_project(title, theme, melody, instrument_name=None, source="generated", layers=None):
    instrument_name = instrument_name or default_instrument_for_engine()
    return {
        "title": title,
        "theme": theme,
        "main_instrument": instrument_name,
        "melody": melody,
        "layers": layers or [],
        "source": source,
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
        return create_project(
            raw_payload.get("title", fallback_title),
            raw_payload.get("theme", fallback_theme),
            melody,
            raw_payload.get("main_instrument", fallback_instrument),
            source="archive",
            layers=normalized_layers,
        )

    return create_project(fallback_title, fallback_theme, raw_payload, fallback_instrument, source="archive", layers=[])


def project_to_payload(project):
    return {
        "title": project["title"],
        "theme": project["theme"],
        "main_instrument": project["main_instrument"],
        "melody": project["melody"],
        "layers": project.get("layers", []),
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


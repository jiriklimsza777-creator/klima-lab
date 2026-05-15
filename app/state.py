# -*- coding: utf-8 -*-

import os

import streamlit as st

import Pamet_a_archiv as db
from app.config import ENGINE_STUDIO, PAGE_GENERATOR

def _resolve_openai_key_default() -> str:
    # Priority: environment variable -> Streamlit secrets -> empty.
    env_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    if env_key:
        return env_key
    try:
        sec = st.secrets
        sec_key = str(sec.get("OPENAI_API_KEY") or "").strip() if hasattr(sec, "get") else ""
        if sec_key:
            return sec_key
    except Exception:
        pass
    return ""

def init_state():
    # Security hardening: never keep API keys in local DB settings.
    try:
        db.save_setting("openai_api_key", "")
    except Exception:
        pass

    defaults = {
        "page": PAGE_GENERATOR,
        "selected_producer": "Žádný (vypnuto)",
        "selected_theme": "Žádné (vypnuto)",
        "import_audio_sig": "",
        "import_beat_wav_bytes": b"",
        "import_bpm_est": None,
        "import_use_auto_bpm": True,
        "import_bpm_manual": 90,
        "import_bars": 4,
        "import_main_instrument": "Acoustic Grand Piano",
        "boombap_extract_tight_midi": b"",
        "boombap_extract_loose_midi": b"",
        "boombap_extract_tight_notes": [],
        "boombap_extract_loose_notes": [],
        # AI-only controls (do not affect local generator unless AI is enabled)
        "ai_role": "Lead",
        "ai_counter_style": "Smooth",
        "ai_creativity": 50,
        "ai_prompt": "",
        "last_ai_prompt": "",
        # Applies to both AI + local generator (melody mode). Kept simple to avoid surprises.
        "note_density": "Normál",
        "note_role": "Lead",
        # Default startup experience: start in Melodic mode.
        "gen_mode": "Melodic",
        "solo_style_last": "Sax",
        "solo_prompt": "",
        "solo_inline_panel": "",
        "show_tutorial": False,
        "local_melody_style": "Klasicky",
        "boombap_variation": 55,
        "boombap_variation_level": "Středně",
        # Sax solo controls (only used when local_melody_style starts with "Sax Solo")
        "sax_solo_character": "Klidné",  # Klidné / Divoké
        "sax_solo_structure": "Bez příběhu",  # Bez příběhu / Příběh
        "piano_solo_character": "Klidné",  # Klidné / Divoké
        "piano_solo_structure": "Bez příběhu",  # Bez příběhu / Příběh
        # DAW-friendly quantize grid (keeps FL alignment). Off preserves original groove.
        "quantize_grid": "Off",
        # Defaults applied to newly generated projects (can be changed per-project later).
        "preset_humanize": "Off",
        "preset_instrument": "Acoustic Grand Piano",
        "active_preset": "Custom",
        "bpm": db.get_setting("default_bpm", 90),
        "num_variants": db.get_setting("default_num_variants", 3),
        "num_bars": db.get_setting("default_num_bars", 4),
        "font": db.get_setting("default_font", "Roboto"),
        "p_color": db.get_setting("default_p_color", "#00FFFF"),
        "bg_type": db.get_setting("default_bg_type", "Výchozí / Obrázek"),
        "card_style": db.get_setting("default_card_style", "Klasický"),
        "chart_style": db.get_setting("default_chart_style", "Klasický"),
        # Visual skins (presets that set bg/card/chart/font/color together).
        "skin_preset": "Custom",
        "skin_applied": "",
        "ai_active": False,
        "ai_chords": False,
        "generation_engine": "Lokální (Random)",
        # Random generator quality controls (internal v1)
        "random_topk_candidates": 5,
        "random_seed_base": 0,
        "dataset_output_mode": "Melodie + akordy",
        "chord_voicing_mode": "Tight",
        "dataset_theme_influence": 20,
        "openai_key": _resolve_openai_key_default(),
        "engine_type": ENGINE_STUDIO,
        "projects": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Streamlit forbids mutating a session_state key after a widget with the same key
    # has been instantiated. We therefore apply page switches via a "pending" key
    # early in the script, before the sidebar radio (key="page") is created.
    if "page_pending" in st.session_state:
        st.session_state.page = st.session_state.page_pending
        del st.session_state["page_pending"]

    # Apply pending UI control changes (used by preset chips / archive open)
    # before the corresponding widgets are instantiated in the sidebar.
    pending_map = {
        "bpm_pending": "bpm",
        "num_variants_pending": "num_variants",
        "num_bars_pending": "num_bars",
        "note_role_pending": "note_role",
        "note_density_pending": "note_density",
        "local_melody_style_pending": "local_melody_style",
        "boombap_variation_pending": "boombap_variation",
        "boombap_variation_level_pending": "boombap_variation_level",
        "preset_humanize_pending": "preset_humanize",
        "preset_instrument_pending": "preset_instrument",
        "active_preset_pending": "active_preset",
        "sax_solo_character_pending": "sax_solo_character",
        "sax_solo_structure_pending": "sax_solo_structure",
        "piano_solo_character_pending": "piano_solo_character",
        "piano_solo_structure_pending": "piano_solo_structure",
        # Visual "skin" preset support (applied before sidebar widgets are instantiated).
        "bg_type_pending": "bg_type",
        "font_pending": "font",
        "card_style_pending": "card_style",
        "chart_style_pending": "chart_style",
        "p_color_pending": "p_color",
    }
    for pk, target in pending_map.items():
        if pk in st.session_state:
            st.session_state[target] = st.session_state[pk]
            del st.session_state[pk]


def autosave_song_params():
    db.save_setting("default_num_variants", int(st.session_state.num_variants))
    db.save_setting("default_num_bars", int(st.session_state.num_bars))


def reset_project_widget_state(max_items: int):
    # Streamlit keeps widget values by their key. When we replace generated projects,
    # we want the UI (especially the "Název projektu" input) to reflect the new data.
    for i in range(int(max_items)):
        # Avoid touching octave shift here; it feels like "playback control" rather than
        # "project identity", and users may expect it to stay even after regeneration.
        for k in (f"name_{i}", f"sel_lab_{i}", f"sel_std_{i}", f"human_{i}"):
            if k in st.session_state:
                del st.session_state[k]




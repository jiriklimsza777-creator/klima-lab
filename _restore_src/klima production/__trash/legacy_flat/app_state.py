# -*- coding: utf-8 -*-

import streamlit as st

import Pamet_a_archiv as db
from app_config import ENGINE_STUDIO, PAGE_GENERATOR


def init_state():
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
        # AI-only controls (do not affect local generator unless AI is enabled)
        "ai_role": "Lead",
        "ai_counter_style": "Smooth",
        "ai_creativity": 50,
        "bpm": db.get_setting("default_bpm", 90),
        "num_variants": db.get_setting("default_num_variants", 3),
        "num_bars": db.get_setting("default_num_bars", 4),
        "font": db.get_setting("default_font", "Roboto"),
        "p_color": db.get_setting("default_p_color", "#00FFFF"),
        "bg_type": db.get_setting("default_bg_type", "Výchozí / Obrázek"),
        "card_style": db.get_setting("default_card_style", "Klasický"),
        "chart_style": db.get_setting("default_chart_style", "Klasický"),
        "ai_active": False,
        "ai_chords": False,
        "openai_key": db.get_setting("openai_api_key", ""),
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


def autosave_song_params():
    db.save_setting("default_num_variants", int(st.session_state.num_variants))
    db.save_setting("default_num_bars", int(st.session_state.num_bars))


def reset_project_widget_state(max_items: int):
    # Streamlit keeps widget values by their key. When we replace generated projects,
    # we want the UI (especially the "Název projektu" input) to reflect the new data.
    for i in range(int(max_items)):
        for k in (f"name_{i}", f"sel_lab_{i}", f"sel_std_{i}", f"oct_project_{i}"):
            if k in st.session_state:
                del st.session_state[k]


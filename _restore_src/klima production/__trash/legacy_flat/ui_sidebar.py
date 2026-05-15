# -*- coding: utf-8 -*-

import os

import streamlit as st
from PIL import Image

import Pamet_a_archiv as db
from app_config import (
    ENGINE_LAB,
    ENGINE_STUDIO,
    LOGO_PATH,
    MODE_CHORDS,
    MODE_MELODY,
    PAGE_ARCHIVE,
    PAGE_GENERATOR,
    PAGE_IMPORT,
)
from app_state import autosave_song_params


def save_custom_items(all_producers, all_themes, new_producer, new_theme):
    if new_producer and new_producer not in all_producers:
        db.save_producer(new_producer)
        st.toast(f"Přidán producent: {new_producer}")
    if new_theme and new_theme not in all_themes:
        db.save_theme(new_theme)
        st.toast(f"Přidáno téma: {new_theme}")


def save_visual_defaults():
    db.save_setting("default_font", st.session_state.font)
    db.save_setting("default_p_color", st.session_state.p_color)
    db.save_setting("default_bg_type", st.session_state.bg_type)
    db.save_setting("default_card_style", st.session_state.card_style)
    db.save_setting("default_chart_style", st.session_state.chart_style)
    st.toast("Vizuál uložen jako výchozí.")


def save_api_key(new_key):
    st.session_state.openai_key = new_key or ""
    db.save_setting("openai_api_key", st.session_state.openai_key)
    st.toast("API klíč uložen.")


def render_sidebar(all_producers, all_themes):
    uploaded_bg = None
    page = st.session_state.page
    selected_producer = st.session_state.selected_producer
    selected_theme = st.session_state.selected_theme

    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(Image.open(LOGO_PATH), use_container_width=True)

        studio_status = "ODEMČENO ✅" if st.session_state.openai_key else "UZAMČENO 🔒"
        studio_color = "#00FF00" if st.session_state.openai_key else "#FF0000"
        st.markdown(
            f"<div style='text-align:center; color:{studio_color}; font-weight:bold; margin-bottom:10px;'>STUDIO {studio_status}</div>",
            unsafe_allow_html=True,
        )

        page = st.radio("📌 STRÁNKY:", [PAGE_GENERATOR, PAGE_ARCHIVE, PAGE_IMPORT], key="page")

        st.session_state.engine_type = st.radio("🔊 ZVUKOVÝ ENGINE:", [ENGINE_LAB, ENGINE_STUDIO], index=1)
        st.session_state.ai_active = st.toggle("🤖 ChatGPT Režim", st.session_state.ai_active)
        gen_mode = st.radio("TYP OBSAHU:", [MODE_MELODY, MODE_CHORDS], horizontal=True)
        st.session_state.ai_chords = gen_mode == MODE_CHORDS

        if st.session_state.ai_active and st.session_state.openai_key:
            with st.expander("🤖 AI NASTAVENÍ", expanded=False):
                st.session_state.ai_creativity = st.slider(
                    "Groove ↔ Kreativita",
                    min_value=0,
                    max_value=100,
                    value=int(st.session_state.ai_creativity),
                    help="Ovlivňuje jen AI (ChatGPT) generování. Lokální generátor se nemění.",
                )
                if not st.session_state.ai_chords:
                    st.session_state.ai_role = st.selectbox(
                        "Role:",
                        ["Lead", "Counter", "Bass"],
                        index=["Lead", "Counter", "Bass"].index(st.session_state.ai_role)
                        if st.session_state.ai_role in ["Lead", "Counter", "Bass"]
                        else 0,
                    )
                    if st.session_state.ai_role == "Counter":
                        st.session_state.ai_counter_style = st.selectbox(
                            "Counter styl:",
                            ["Smooth", "Busy"],
                            index=["Smooth", "Busy"].index(st.session_state.ai_counter_style)
                            if st.session_state.ai_counter_style in ["Smooth", "Busy"]
                            else 0,
                        )
                else:
                    st.caption("Role je v akordovém režimu fixní: Chords.")

        with st.expander("📦 PRODUCENTI & TÉMATA", expanded=False):
            selected_producer = st.selectbox(
                "Producent:",
                all_producers,
                key="producer_sel",
                index=all_producers.index(st.session_state.selected_producer) if st.session_state.selected_producer in all_producers else 0,
            )
            st.session_state.selected_producer = selected_producer

            selected_theme = st.selectbox(
                "Téma:",
                all_themes,
                key="theme_sel",
                index=all_themes.index(st.session_state.selected_theme) if st.session_state.selected_theme in all_themes else 0,
            )
            st.session_state.selected_theme = selected_theme

            st.caption("Níže můžeš přidat vlastní položky do seznamu.")
            new_producer = st.text_input("Vlastní producent:")
            new_theme = st.text_input("Vlastní atmosféra:")
            if st.button("💾 ULOŽIT NOVÉ", use_container_width=True):
                save_custom_items(all_producers, all_themes, new_producer, new_theme)

        with st.expander("⚙️ PARAMETRY SKLADBY", expanded=False):
            st.caption("BPM většinou řešíš v DAW, ale nechávám tu možnost.")
            st.session_state.bpm = st.number_input("BPM (Rychlost):", min_value=40, max_value=220, value=int(st.session_state.bpm))
            st.number_input(
                "Počet melodií:",
                min_value=1,
                max_value=10,
                value=int(st.session_state.num_variants),
                step=1,
                on_change=autosave_song_params,
                key="num_variants",
            )
            st.number_input(
                "Počet taktů:",
                min_value=1,
                max_value=16,
                value=int(st.session_state.num_bars),
                step=1,
                on_change=autosave_song_params,
                key="num_bars",
            )

        with st.expander("🎨 VIZUÁL A STYL", expanded=False):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.session_state.bg_type = st.selectbox(
                    "Pozadí:",
                    [
                        "Výchozí / Obrázek",
                        "Animovaný Gradient",
                        "Pulzující Temnota",
                        "Lo-Fi Papír",
                        "Jazz Club",
                        "Blueprint Grid",
                        "CRT Scanlines",
                        "Tape Sunset",
                        "Studio Fog",
                        "Vaporwave Haze",
                    ],
                    index=0,
                )
                uploaded_bg = st.file_uploader("Vlastní obrázek:", type=["jpg", "png"])
            with col_v2:
                st.session_state.font = st.selectbox("Písmo:", ["Roboto", "Orbitron", "Permanent Marker"], index=0)
                st.session_state.card_style = st.selectbox(
                    "Styl karet:",
                    [
                        "Klasický",
                        "Skleněný (Glassmorphism)",
                        "Neonový (Glow)",
                        "Cyberpunk",
                        "Retro Lo-Fi",
                        "Metal (Brushed)",
                        "Vinyl Sleeve",
                        "Notebook (Ruled)",
                        "Tape Deck",
                        "Brutalist Blocks",
                        "Soft Shadow",
                        "Outline Mono",
                    ],
                    index=0,
                )
                st.session_state.chart_style = st.selectbox(
                    "Styl grafů:",
                    [
                        "Klasický",
                        "Neon",
                        "Minimalistický",
                        "Synthwave (80s)",
                        "Lo-Fi Grayscale",
                        "Hologram",
                        "Blueprint",
                        "Paper",
                        "Jazz Club",
                        "Arcade",
                        "High Contrast",
                        "Soft Pastel",
                    ],
                    index=0,
                )
                st.session_state.p_color = st.color_picker("Barva prvků:", st.session_state.p_color)

            if st.button("💾 ULOŽIT VZHLED JAKO VÝCHOZÍ", use_container_width=True):
                save_visual_defaults()

        with st.expander("🔐 SYSTÉM", expanded=False):
            new_key = st.text_input("OpenAI API Klíč:", value=st.session_state.openai_key, type="password")
            if st.button("💾 Potvrdit klíč"):
                save_api_key(new_key)

    return uploaded_bg, page, selected_producer, selected_theme


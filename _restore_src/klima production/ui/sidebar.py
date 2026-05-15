# -*- coding: utf-8 -*-

import os

import streamlit as st
from PIL import Image

import Pamet_a_archiv as db
from core.backup import build_app_zip_bytes
from app.config import (
    APP_DIR,
    APP_VERSION,
    ENGINE_LAB,
    ENGINE_STUDIO,
    LOGO_PATH,
    PAGE_ARCHIVE,
    PAGE_GENERATOR,
    PAGE_IMPORT,
)
from app.state import autosave_song_params

MODE_SOLOS = "Sola"
MODE_MELODIC = "Melodic"
MODE_CHORDS_UI = "Chords"
MODE_LOOP = "Loop"
ENGINE_RANDOM = "Lokální (Random)"
ENGINE_DATASET = "Dataset Style"
ENGINE_AI = "AI (ChatGPT)"

SKIN_PRESETS = {
    # Name: {bg_type, card_style, chart_style, font, p_color}
    "BoomBap Mafia": {
        "bg_type": "Výchozí / Obrázek",
        "card_style": "Klasický",
        "chart_style": "Klasický",
        "font": "Roboto",
        "p_color": "#00FFFF",
    },
    "FL Classic": {
        "bg_type": "Blueprint Grid",
        "card_style": "Outline Mono",
        "chart_style": "Blueprint",
        "font": "Roboto",
        "p_color": "#1e9cc6",
    },
    "Minimal": {
        "bg_type": "Pulzující Temnota",
        "card_style": "Outline Mono",
        "chart_style": "Minimalistický",
        "font": "Roboto",
        "p_color": "#d8dde6",
    },
}


def save_custom_items(all_producers, all_themes, new_producer, new_theme):
    if new_producer and new_producer not in all_producers:
        db.save_producer(new_producer)
        st.toast(f"Přidán producent: {new_producer}.")
    if new_theme and new_theme not in all_themes:
        db.save_theme(new_theme)
        st.toast(f"Přidáno téma: {new_theme}.")


def save_visual_defaults():
    db.save_setting("default_font", st.session_state.font)
    db.save_setting("default_p_color", st.session_state.p_color)
    db.save_setting("default_bg_type", st.session_state.bg_type)
    db.save_setting("default_card_style", st.session_state.card_style)
    db.save_setting("default_chart_style", st.session_state.chart_style)
    st.toast("Vizuál uložen jako výchozí.")


def render_sidebar(all_producers, all_themes):
    uploaded_bg = None
    page = st.session_state.page
    selected_producer = st.session_state.selected_producer
    selected_theme = st.session_state.selected_theme
    # One-shot request to open the Producer/Theme expander (e.g. from solo chips).
    open_prod_theme = bool(st.session_state.pop("open_prod_theme_expander", False))
    # Allow other parts of the UI to programmatically set the producer/theme selectboxes.
    # Must happen before the widgets with keys "producer_sel"/"theme_sel" are instantiated.
    if "producer_sel_pending" in st.session_state:
        st.session_state["producer_sel"] = st.session_state.pop("producer_sel_pending")
    if "theme_sel_pending" in st.session_state:
        st.session_state["theme_sel"] = st.session_state.pop("theme_sel_pending")

    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(Image.open(LOGO_PATH), use_container_width=True)

        studio_status = "ODEMČENO" if st.session_state.openai_key else "UZAMČENO"
        studio_color = "#00FF00" if st.session_state.openai_key else "#FF0000"
        st.markdown(
            f"<div style='text-align:center; color:{studio_color}; font-weight:bold; margin-bottom:10px;'>"
            f"STUDIO {studio_status} &nbsp;•&nbsp; {APP_VERSION}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Tooltip (question-mark) for the page switcher without bringing back the "STRÁNKY:" label row.
        st.markdown(
            "<div style='display:flex; justify-content:flex-end; margin:-0.35rem 0 -1.05rem 0;'>"
            "<span title='Generátor = generuje nové nápady (melodie/akordy/loopy/sóla). "
            "Archiv = uložené projekty, filtry, otevření zpět. "
            "Import = nahraješ beat (WAV/MP3) a generuješ k němu.' "
            "style='display:inline-block; width:1.2rem; height:1.2rem; line-height:1.2rem; text-align:center; "
            "border-radius:999px; border:1px solid rgba(255,255,255,.25); opacity:.85; font-weight:700; cursor:help;'>?</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Stránky",
            [PAGE_GENERATOR, PAGE_ARCHIVE, PAGE_IMPORT],
            key="page",
            label_visibility="collapsed",
        )

        eng_opts = [ENGINE_LAB, ENGINE_STUDIO]
        eng_idx = eng_opts.index(st.session_state.engine_type) if st.session_state.engine_type in eng_opts else 1
        st.radio("ZVUKOVÝ ENGINE:", eng_opts, index=eng_idx, key="engine_type")
        engine_options = [ENGINE_RANDOM, ENGINE_DATASET, ENGINE_AI]
        current_engine = str(st.session_state.get("generation_engine") or ENGINE_RANDOM)
        if current_engine not in engine_options:
            current_engine = ENGINE_RANDOM
            st.session_state["generation_engine"] = current_engine
        with st.popover(f"Generátor: {current_engine} ▾", use_container_width=True):
            picked_engine = st.radio(
                "Typ generátoru",
                engine_options,
                index=engine_options.index(current_engine),
                key="generation_engine",
                label_visibility="collapsed",
            )
        st.session_state.ai_active = str(st.session_state.get("generation_engine") or ENGINE_RANDOM) == ENGINE_AI

        mode_options = [MODE_MELODIC, MODE_SOLOS, MODE_CHORDS_UI, MODE_LOOP]
        local_style = str(st.session_state.get("local_melody_style") or "").strip().lower()
        is_solo = local_style.startswith(
            ("sax", "piano", "rhodes", "trumpet", "flute", "marimba", "vib", "vibra", "akust")
        )
        if st.session_state.ai_chords:
            mode_default = MODE_CHORDS_UI
        elif local_style == "boombap loop":
            mode_default = MODE_LOOP
        elif is_solo:
            mode_default = MODE_SOLOS
        else:
            mode_default = MODE_MELODIC

        # FL-like label row: title left, '?' tooltip on the right.
        c_lbl2, c_q2 = st.columns([1, 0.08], gap="small")
        with c_lbl2:
            st.markdown("**Co generovat**")
        with c_q2:
            st.markdown(
                "<div style='text-align:right;'>"
                "<span title='Melodic = jedna melodická linka. Chords = harmonická smyčka (akordy). "
                "Loop = boombap smyčka s \"otázka → odpověď\" (víc sample feel). "
                "Sola = krátká sólová linka (4–8 taktů); nástroj vybereš nahoře u chipů.' "
                "style='display:inline-block; width:1.2rem; height:1.2rem; line-height:1.2rem; text-align:center; border-radius:999px; "
                "border:1px solid rgba(255,255,255,.25); opacity:.85; font-weight:700; cursor:help;'>?</span>"
                "</div>",
                unsafe_allow_html=True,
            )

        if str(st.session_state.get("generation_engine") or ENGINE_RANDOM) == ENGINE_DATASET:
            dataset_outputs = ["Melodie", "Akordy", "Melodie + akordy", "Balík frází"]
            if str(st.session_state.get("dataset_output_mode") or "") not in dataset_outputs:
                st.session_state["dataset_output_mode"] = "Melodie + akordy"
            st.radio(
                "Dataset output",
                dataset_outputs,
                horizontal=True,
                key="dataset_output_mode",
                label_visibility="collapsed",
            )
            voicing_opts = ["Těsné", "Široké", "Jazz", "Temné"]
            voicing_map_to_internal = {"Těsné": "Tight", "Široké": "Wide", "Jazz": "Jazz", "Temné": "Dark"}
            voicing_map_from_internal = {v: k for k, v in voicing_map_to_internal.items()}
            current_voicing_internal = str(st.session_state.get("chord_voicing_mode") or "Tight")
            current_voicing_ui = voicing_map_from_internal.get(current_voicing_internal, "Těsné")
            with st.popover(f"Voicing akordů: {current_voicing_ui} ▾", use_container_width=True):
                picked_voicing_ui = st.radio(
                    "Voicing akordů",
                    voicing_opts,
                    index=voicing_opts.index(current_voicing_ui) if current_voicing_ui in voicing_opts else 0,
                    key="chord_voicing_mode_ui",
                    label_visibility="collapsed",
                )
            st.session_state["chord_voicing_mode"] = voicing_map_to_internal.get(str(picked_voicing_ui), "Tight")
            st.slider(
                "Vliv tématu",
                min_value=0,
                max_value=100,
                value=int(st.session_state.get("dataset_theme_influence") or 20),
                key="dataset_theme_influence",
                help="0 = čistý dataset. Vyšší hodnota jemně upraví hustotu/registr podle tématu.",
            )
            st.session_state.ai_chords = False
            st.session_state.local_melody_style = "Klasicky"
            gen_mode = str(st.session_state.get("gen_mode") or MODE_MELODIC)
        else:
            gen_mode = st.radio(
                "Co generovat:",
                mode_options,
                horizontal=True,
                key="gen_mode",
                index=mode_options.index(mode_default) if mode_default in mode_options else 0,
                label_visibility="collapsed",
            )
            st.session_state.ai_chords = gen_mode == MODE_CHORDS_UI
            if gen_mode == MODE_MELODIC:
                st.session_state.ai_chords = False
                # Use ASCII value here to avoid Windows/encoding weirdness in session_state comparisons.
                st.session_state.local_melody_style = "Klasicky"
            elif gen_mode == MODE_LOOP:
                st.session_state.ai_chords = False
                st.session_state.local_melody_style = "Boombap Loop"
            elif gen_mode == MODE_SOLOS:
                st.session_state.ai_chords = False
                # Keep the previously selected solo instrument if possible.
                cur = str(st.session_state.get("local_melody_style") or "")
                cur_l = cur.strip().lower()
                if not cur_l.startswith(("sax", "piano", "rhodes", "trumpet", "flute", "marimba", "vib", "vibra", "akust")):
                    st.session_state.local_melody_style = str(st.session_state.get("solo_style_last") or "Sax")
            elif gen_mode == MODE_CHORDS_UI:
                # Chords mode: generation is handled as chords (role fixed to Chords).
                st.session_state.ai_chords = True

        if st.session_state.ai_active and st.session_state.openai_key:
            with st.expander("AI NASTAVENÍ", expanded=False):
                st.slider(
                    "Groove <-> Kreativita",
                    min_value=0,
                    max_value=100,
                    value=int(st.session_state.ai_creativity),
                    key="ai_creativity",
                    help="Ovlivňuje jen AI (ChatGPT) generování. Lokální generátor se nemění.",
                )
                # DAW helper (shared setting). We show it here when AI is enabled so all "feel" controls are together.
                st.selectbox(
                    "DAW Quantize:",
                    ["Off", "1/8", "1/16"],
                    index=["Off", "1/8", "1/16"].index(st.session_state.quantize_grid)
                    if st.session_state.quantize_grid in ["Off", "1/8", "1/16"]
                    else 0,
                    key="quantize_grid",
                    help="Když ti to v FL nesedí do rytmu, zapni 1/16. Přicvakne starty/délky not na mřížku.",
                )
                # Shared control (applies to AI + local), but when AI is on we show it here
                # to keep all "AI feel" controls in one place.
                st.selectbox(
                    "Hustota not:",
                    ["Méně not", "Normál", "Více not"],
                    index=["Méně not", "Normál", "Více not"].index(st.session_state.note_density)
                    if st.session_state.note_density in ["Méně not", "Normál", "Více not"]
                    else 1,
                    key="note_density",
                    help="Platí pro melodie (AI i matematický generátor). Akordy tím neměníme.",
                )
                # Shared control (applies to AI + local), but when AI is on we show it here
                # to keep all "AI feel" controls in one place.
                st.selectbox(
                    "Role melodie:",
                    ["Lead", "Counter", "Bass"],
                    index=["Lead", "Counter", "Bass"].index(st.session_state.note_role)
                    if st.session_state.note_role in ["Lead", "Counter", "Bass"]
                    else 0,
                    key="note_role",
                    help="Lead = hlavní melodie, Counter = doprovodná vyšší linka, Bass = basová linka. Platí pro AI i matematický generátor (jen melodie).",
                )
                if not st.session_state.ai_chords:
                    # Counter style is AI-only nuance; the main Role is set in "Parametry skladby".
                    if st.session_state.note_role == "Counter":
                        st.selectbox(
                            "Counter styl:",
                            ["Smooth", "Busy"],
                            index=["Smooth", "Busy"].index(st.session_state.ai_counter_style)
                            if st.session_state.ai_counter_style in ["Smooth", "Busy"]
                            else 0,
                            key="ai_counter_style",
                        )
                else:
                    st.caption("V režimu akordů je role fixní: Chords.")
        else:
            # Small, non-intrusive control for Boombap Loop only (local generator).
            if gen_mode == MODE_LOOP:
                def _apply_boombap_level():
                    level = str(st.session_state.get("boombap_variation_level") or "Středně")
                    mapping = {"Málo": 25, "Středně": 55, "Popiči moc": 85}
                    st.session_state["boombap_variation_pending"] = int(mapping.get(level, 55))

                # Derive default level from current numeric value (keeps archive/back-compat).
                try:
                    v = int(st.session_state.get("boombap_variation") or 55)
                except Exception:
                    v = 55
                if v <= 35:
                    default_level = "Málo"
                elif v <= 70:
                    default_level = "Středně"
                else:
                    default_level = "Popiči moc"
                if "boombap_variation_level" not in st.session_state:
                    st.session_state["boombap_variation_level"] = default_level

                # FL-like label row: title left, '?' tooltip on the right.
                c_lbl, c_q = st.columns([1, 0.08], gap="small")
                with c_lbl:
                    st.markdown("**Variace (Boombap)**")
                with c_q:
                    st.markdown(
                        "<div style='text-align:right;'>"
                        "<span title='Jak moc se odpověď liší od otázky v Boombap Loop. Málo = skoro stejné, Středně = malé variace, Popiči moc = výraznější odpověď.' "
                        "style='display:inline-block; width:1.2rem; height:1.2rem; line-height:1.2rem; text-align:center; border-radius:999px; "
                        "border:1px solid rgba(255,255,255,.25); opacity:.85; font-weight:700; cursor:help;'>?</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

                st.radio(
                    "Variace (Boombap):",
                    ["Málo", "Středně", "Popiči moc"],
                    index=["Málo", "Středně", "Popiči moc"].index(str(st.session_state.get("boombap_variation_level") or default_level)),
                    key="boombap_variation_level",
                    horizontal=True,
                    on_change=_apply_boombap_level,
                    label_visibility="collapsed",
                )
            # NOTE: Solo modes use "auto dice" per generated proposal (no sidebar controls),
            # and "lock" enables generating variations around a locked proposal.

        with st.expander("PRODUCENTI & TÉMATA", expanded=open_prod_theme):
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
            new_theme = st.text_input("Vlastní téma:")
            if st.button("ULOŽIT NOVÉ", use_container_width=True):
                save_custom_items(all_producers, all_themes, new_producer, new_theme)

            # (No "close panel" button; users can collapse the expander normally.)

        with st.expander("PARAMETRY SKLADBY", expanded=False):
            st.caption("BPM většinou řešíš v DAW, ale nechávám tu možnost.")
            st.number_input(
                "BPM:",
                min_value=40,
                max_value=220,
                value=int(st.session_state.bpm),
                key="bpm",
                help=(
                    "Rychlost skladby v BPM.\n"
                    "Kdy: Když chceš upravit tempo přehrávání/exportu.\n"
                    "Dopad: Mění rychlost playeru i MIDI exportu."
                ),
            )
            if not (st.session_state.ai_active and st.session_state.openai_key):
                st.selectbox(
                    "DAW Quantize:",
                    ["Off", "1/8", "1/16"],
                    index=["Off", "1/8", "1/16"].index(st.session_state.quantize_grid)
                    if st.session_state.quantize_grid in ["Off", "1/8", "1/16"]
                    else 0,
                    key="quantize_grid",
                    help=(
                        "Zarovná noty na rytmickou mřížku.\n"
                        "Kdy: Když v DAW timing nesedí přesně.\n"
                        "Dopad: Off = přirozený groove, 1/8 = volnější, 1/16 = nejpřesnější."
                    ),
                )
            if not (st.session_state.ai_active and st.session_state.openai_key):
                st.selectbox(
                    "Hustota not:",
                    ["Méně not", "Normál", "Více not"],
                    index=["Méně not", "Normál", "Více not"].index(st.session_state.note_density)
                    if st.session_state.note_density in ["Méně not", "Normál", "Více not"]
                    else 1,
                    key="note_density",
                    help=(
                        "Určí, kolik not bude v melodii.\n"
                        "Kdy: Když chceš jednodušší nebo plnější linku.\n"
                        "Dopad: Méně not = víc prostoru, Více not = hustší fráze."
                    ),
                )
            if not (st.session_state.ai_active and st.session_state.openai_key):
                st.selectbox(
                    "Role melodie:",
                    ["Lead", "Counter", "Bass"],
                    index=["Lead", "Counter", "Bass"].index(st.session_state.note_role)
                    if st.session_state.note_role in ["Lead", "Counter", "Bass"]
                    else 0,
                    key="note_role",
                    help=(
                        "Určí roli melodie v tracku.\n"
                        "Kdy: Když skládáš vrstvy (hlavní/doplňková/basová).\n"
                        "Dopad: Lead = dominantní, Counter = doplněk, Bass = spodní groove."
                    ),
                )
            st.number_input(
                "Počet melodií:",
                min_value=1,
                max_value=10,
                value=int(st.session_state.num_variants),
                step=1,
                on_change=autosave_song_params,
                key="num_variants",
                help=(
                    "Nastaví počet návrhů v jedné dávce.\n"
                    "Kdy: Když chceš víc variant najednou.\n"
                    "Dopad: Vyšší číslo = více možností, ale delší čekání."
                ),
            )
            st.number_input(
                "Počet taktů:",
                min_value=1,
                max_value=16,
                value=int(st.session_state.num_bars),
                step=1,
                on_change=autosave_song_params,
                key="num_bars",
                help=(
                    "Nastaví délku melodie v taktech.\n"
                    "Kdy: Když chceš krátký loop nebo delší vývoj.\n"
                    "Dopad: 2–4 = loop vibe, 8+ = více vývoje."
                ),
            )

        with st.expander("VIZUÁL A STYL", expanded=False):
            skin_opts = ["Custom"] + list(SKIN_PRESETS.keys())
            if st.session_state.get("skin_preset") not in skin_opts:
                # If we changed available presets, avoid Streamlit value-not-in-options errors.
                st.session_state["skin_preset"] = "Custom"
                st.session_state["skin_applied"] = ""
            st.selectbox(
                "Skins:",
                skin_opts,
                key="skin_preset",
                help="Skin nastaví najednou pozadí, písmo, styl karet, styl grafů a barvu prvků.",
            )
            chosen_skin = str(st.session_state.get("skin_preset") or "Custom")
            if chosen_skin != "Custom" and chosen_skin in SKIN_PRESETS and chosen_skin != str(st.session_state.get("skin_applied") or ""):
                s = SKIN_PRESETS[chosen_skin]
                st.session_state["bg_type_pending"] = str(s.get("bg_type") or st.session_state.bg_type)
                st.session_state["font_pending"] = str(s.get("font") or st.session_state.font)
                st.session_state["card_style_pending"] = str(s.get("card_style") or st.session_state.card_style)
                st.session_state["chart_style_pending"] = str(s.get("chart_style") or st.session_state.chart_style)
                st.session_state["p_color_pending"] = str(s.get("p_color") or st.session_state.p_color)
                st.session_state["skin_applied"] = chosen_skin
                st.rerun()
            elif chosen_skin == "Custom" and st.session_state.get("skin_applied"):
                st.session_state["skin_applied"] = ""

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.selectbox(
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
                    key="bg_type",
                )
                uploaded_bg = st.file_uploader("Vlastní obrázek:", type=["jpg", "png"])
            with col_v2:
                st.selectbox("Písmo:", ["Roboto", "Orbitron", "Permanent Marker"], index=0, key="font")
                st.selectbox(
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
                    key="card_style",
                )
                st.selectbox(
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
                    key="chart_style",
                )
                st.color_picker("Barva prvků:", st.session_state.p_color, key="p_color")

            if st.button("ULOŽIT VZHLED JAKO VÝCHOZÍ", use_container_width=True):
                save_visual_defaults()

        with st.expander("SYSTÉM", expanded=False):
            has_env_key = bool(os.getenv("OPENAI_API_KEY"))
            key_source = "OPENAI_API_KEY (systém)" if has_env_key else "nenalezeno"
            st.caption(f"OpenAI klíč: {key_source}")
            st.caption("Bezpečný režim: klíč se neukládá do appky ani do souborů.")
            if st.button("Obnovit stav klíče", use_container_width=True):
                st.session_state.openai_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
                st.toast("Stav klíče obnoven ze systémového prostředí.")
                st.rerun()

            st.divider()
            if st.button("Pro blbce !!!", use_container_width=True):
                st.session_state["show_tutorial"] = True
                st.rerun()

            if st.button("Vytvořit ZIP zálohu celé aplikace", use_container_width=True):
                import datetime as _dt

                ts = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                st.session_state["backup_zip_name"] = f"klima-production_{ts}.zip"
                with st.spinner("Vytvářím ZIP zálohu…"):
                    st.session_state["backup_zip_bytes"] = build_app_zip_bytes(APP_DIR)

            zip_bytes = st.session_state.get("backup_zip_bytes")
            zip_name = st.session_state.get("backup_zip_name", "klima-production_backup.zip")
            if zip_bytes:
                st.download_button(
                    "Stáhnout ZIP zálohu",
                    data=zip_bytes,
                    file_name=zip_name,
                    mime="application/zip",
                    use_container_width=True,
                )
                st.caption("Tip: aby se tě prohlížeč vždy ptal kam ukládat, zapni v nastavení stahování „Vždy se ptát“.") 

    return uploaded_bg, page, selected_producer, selected_theme


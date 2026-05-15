# -*- coding: utf-8 -*-

import random

import streamlit as st

import Generator_not as logic
import Pamet_a_archiv as db
import Zvuk_a_export as sound
from app_config import (
    ENGINE_LAB,
    ENGINE_STUDIO,
    LAB_WAVES,
    PAGE_GENERATOR,
    STUDIO_INSTRUMENTS,
)
from app_state import reset_project_widget_state
from app_utils import get_theme_string
from projects import create_project, get_combined_notes, normalize_project_payload
from ui_cards import render_melody_card


def _maybe_update_import_bpm(uploaded):
    if uploaded is None:
        st.session_state.import_audio_sig = ""
        st.session_state.import_beat_wav_bytes = b""
        st.session_state.import_bpm_est = None
        return

    sig = f"{uploaded.name}:{uploaded.size}"
    if sig == st.session_state.import_audio_sig:
        return

    st.session_state.import_audio_sig = sig
    st.session_state.import_bpm_est = None
    st.session_state.import_beat_wav_bytes = b""

    name_lower = uploaded.name.lower()
    if name_lower.endswith(".wav"):
        wav_bytes = uploaded.getvalue()
        st.session_state.import_beat_wav_bytes = wav_bytes
        bpm = sound.estimate_bpm_from_wav_bytes(wav_bytes)
        st.session_state.import_bpm_est = bpm
        if bpm and st.session_state.import_use_auto_bpm:
            st.session_state.import_bpm_manual = int(round(bpm))


def _apply_groove_creativity(notes, creativity_0_100):
    if not notes:
        return notes

    creativity = max(0.0, min(1.0, float(creativity_0_100) / 100.0))
    tightness = 1.0 - creativity

    quant = 0.25 if tightness >= 0.5 else 0.125
    jitter = 0.0 if tightness >= 0.6 else (0.03 * (1.0 - tightness))
    drop_prob = 0.18 * tightness

    styled = []
    for n in notes:
        if len(n) < 3:
            continue
        if drop_prob > 0 and random.random() < drop_prob:
            continue
        start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90

        start = round(round(start / quant) * quant, 3)
        if jitter > 0:
            start = round(max(0.0, start + random.uniform(-jitter, jitter)), 3)
        dur = round(round(dur / quant) * quant, 3)
        dur = max(quant, dur)
        styled.append([start, pitch, dur, vel])

    styled.sort(key=lambda x: (x[0], x[1]))
    return styled


def render_import_page(selected_producer, selected_theme):
    st.title("🎛️ IMPORT BEATU")
    uploaded = st.file_uploader("Nahraj beat (WAV nebo MP3):", type=["wav", "mp3"])
    if uploaded is None:
        st.info("Nahraj beat a nastav BPM / náladu / nástroj.")
        return

    st.audio(uploaded.getvalue())
    _maybe_update_import_bpm(uploaded)

    bpm_est = st.session_state.import_bpm_est
    if bpm_est:
        st.markdown(f"**Auto BPM:** `{bpm_est:.1f}`")
    else:
        st.markdown("**Auto BPM:** `—`")

    st.session_state.import_use_auto_bpm = st.checkbox("Použít Auto BPM", value=st.session_state.import_use_auto_bpm)
    st.session_state.import_bpm_manual = st.number_input("BPM:", min_value=40, max_value=220, value=int(st.session_state.import_bpm_manual))

    bpm_used = bpm_est if (st.session_state.import_use_auto_bpm and bpm_est) else float(st.session_state.import_bpm_manual)
    bpm_used = float(max(40, min(220, bpm_used)))

    bars_suggest = None
    if uploaded.name.lower().endswith(".wav") and bpm_used:
        dur = sound.get_wav_duration_seconds(uploaded.getvalue())
        if dur:
            beats = (dur * bpm_used) / 60.0
            bars_suggest = int(max(1, min(16, round(beats / 4.0))))

    st.session_state.import_bars = st.number_input(
        "Délka (taktů):",
        min_value=1,
        max_value=16,
        value=int(bars_suggest or st.session_state.import_bars),
    )

    theme_string = get_theme_string(selected_producer, selected_theme)
    st.markdown(f"**Mood:** `{theme_string}`")

    if st.session_state.engine_type == ENGINE_STUDIO:
        from app_config import DISPLAY_STUDIO_INSTRUMENTS

        st.session_state.import_main_instrument = st.selectbox("Nástroj (hlavní):", DISPLAY_STUDIO_INSTRUMENTS, index=0)
    else:
        st.session_state.import_main_instrument = st.selectbox("Vlna (hlavní):", list(LAB_WAVES.keys()), index=0)

    if st.button("🚀 GENEROVAT MELODIE K BEATU", use_container_width=True):
        st.session_state.bpm = int(round(bpm_used))

        chords_mode = st.session_state.ai_chords
        energy = logic.get_producer_energy(selected_producer)
        projects = []

        for i in range(int(st.session_state.num_variants)):
            if st.session_state.ai_active and st.session_state.openai_key:
                result = logic.call_chatgpt_ai(
                    st.session_state.openai_key,
                    "",
                    int(st.session_state.import_bars),
                    chords_mode,
                    theme_string,
                    energy=energy,
                    role="Chords" if chords_mode else st.session_state.ai_role,
                    creativity=int(st.session_state.ai_creativity),
                    counter_style=str(st.session_state.ai_counter_style),
                )
            else:
                if chords_mode:
                    result = logic.chord_generate(int(st.session_state.import_bars), theme_string, energy)
                else:
                    result = logic.smart_generate(int(st.session_state.import_bars), theme_string, energy)

            # Post-process only for AI output; local generator remains unchanged.
            if st.session_state.ai_active and st.session_state.openai_key:
                result = _apply_groove_creativity(result or [], int(st.session_state.ai_creativity))
            proj = create_project(
                f"IMPORT_{theme_string}_{i + 1}",
                theme_string,
                result,
                instrument_name=st.session_state.import_main_instrument,
                source="import",
            )
            projects.append(proj)

        old_n = len(st.session_state.projects) if st.session_state.projects else 0
        reset_project_widget_state(max(old_n, len(projects)))
        st.session_state.projects = projects
        st.toast("Hotovo. Návrhy jsou dole.")

    if st.session_state.projects:
        st.subheader("Výsledky")
        for idx, project in enumerate(st.session_state.projects):
            render_melody_card(project, idx)


def generate_projects(selected_producer, final_theme_string, ai_prompt, chords_mode):
    auto_energy = logic.get_producer_energy(selected_producer)
    projects = []

    for index in range(int(st.session_state.num_variants)):
        if st.session_state.ai_active and st.session_state.openai_key:
            result = logic.call_chatgpt_ai(
                st.session_state.openai_key,
                ai_prompt,
                st.session_state.num_bars,
                chords_mode,
                final_theme_string,
                energy=auto_energy,
                role="Chords" if chords_mode else st.session_state.ai_role,
                creativity=int(st.session_state.ai_creativity),
                counter_style=str(st.session_state.ai_counter_style),
            )
        else:
            result = logic.chord_generate(st.session_state.num_bars, final_theme_string, auto_energy) if chords_mode else logic.smart_generate(st.session_state.num_bars, final_theme_string, auto_energy)

        if not result:
            result = logic.chord_generate(st.session_state.num_bars, final_theme_string, auto_energy) if chords_mode else logic.smart_generate(st.session_state.num_bars, final_theme_string, auto_energy)

        projects.append(create_project(f"{final_theme_string}_{index + 1}", final_theme_string, result))

    old_n = len(st.session_state.projects) if st.session_state.projects else 0
    reset_project_widget_state(max(old_n, len(projects)))
    st.session_state.projects = projects


def render_generation_form():
    trigger_generate = False
    ai_prompt = ""

    with st.form("gen_form", border=False):
        col_center = st.columns([1, 1.5, 1])[1]
        with col_center:
            if st.session_state.ai_active:
                ai_prompt = st.text_input("Vize", placeholder="Popiš svůj beat...", label_visibility="collapsed")
            trigger_generate = st.form_submit_button("🚀 GENEROVAT", use_container_width=True)

    return trigger_generate, ai_prompt


def open_project_from_archive(project):
    st.session_state.projects = [project]
    reset_project_widget_state(1)
    st.session_state.page_pending = PAGE_GENERATOR
    st.rerun()


def render_generator_page(selected_producer, final_theme_string):
    trigger_generate, ai_prompt = render_generation_form()

    if trigger_generate:
        with st.spinner("Skládám hit..."):
            generate_projects(selected_producer, final_theme_string, ai_prompt, st.session_state.ai_chords)

    for index, project in enumerate(st.session_state.projects):
        render_melody_card(project, index)


def render_archive_page():
    st.title("📚 ARCHIV TVÝCH BEATŮ")
    df = db.get_all_melodies()
    if df.empty:
        st.info("Tvůj archiv je zatím prázdný.")
        return

    for _, row in df.iterrows():
        payload = db.json.loads(row["noty_json"])
        project = normalize_project_payload(payload, row["jmeno"], row["atmosfera"], row["nastroj"])
        combined_notes = get_combined_notes(project)
        title = f"{'⭐' * row['rating']} | {row['datum']} - {project['title']}"

        with st.expander(title):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                audio_parts = []
                main_instr = project["main_instrument"]
                if main_instr in STUDIO_INSTRUMENTS:
                    audio_parts.append(sound.synthesise_full_audio(project["melody"], engine_type=ENGINE_STUDIO, instrument_id=STUDIO_INSTRUMENTS[main_instr], bpm=row["bpm"]))
                else:
                    audio_parts.append(sound.synthesise_full_audio(project["melody"], engine_type=ENGINE_STUDIO, instrument_id=0, bpm=row["bpm"]))

                for layer in project.get("layers", []):
                    instr_id = STUDIO_INSTRUMENTS.get(layer["instrument"], 0)
                    audio_parts.append(sound.synthesise_full_audio(layer["melody"], engine_type=ENGINE_STUDIO, instrument_id=instr_id, bpm=row["bpm"]))

                st.audio(sound.mix_wav_audios(audio_parts), format="audio/wav")

                if project.get("layers"):
                    layer_labels = [layer["instrument"] for layer in project["layers"]]
                    st.markdown("<div class='layers-line'>Vrstevnice: " + " • ".join(layer_labels) + "</div>", unsafe_allow_html=True)

            with col_right:
                st.download_button("🎹 MIDI", sound.export_to_midi(combined_notes, row["bpm"]), f"{project['title']}.mid", key=f"dl_{row['id']}", use_container_width=True)
                if st.button("🪄 Otevřít do editoru", key=f"open_{row['id']}", use_container_width=True):
                    open_project_from_archive(project)
                if st.button("🗑️ Smazat", key=f"del_{row['id']}", use_container_width=True):
                    db.delete_from_db(row["id"])
                    st.rerun()


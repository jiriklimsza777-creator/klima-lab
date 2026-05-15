# -*- coding: utf-8 -*-

import streamlit as st

import Pamet_a_archiv as db
import Vizual_a_grafika as ui
import Zvuk_a_export as sound
from app_config import DISPLAY_STUDIO_INSTRUMENTS, ENGINE_LAB, ENGINE_STUDIO, LAB_WAVES, STUDIO_INSTRUMENTS
from projects import build_audio_parts, ensure_project_octave, get_combined_notes, project_to_payload


def render_project_audio_player(project, index):
    octave_key = ensure_project_octave(index)
    audio_parts = build_audio_parts(project, st.session_state[octave_key])
    audio_blobs = [
        sound.synthesise_full_audio(
            part["melody"],
            engine_type=part["engine_type"],
            instrument_id=part["instrument_id"],
            octave_shift=part["octave_shift"],
            bpm=st.session_state.bpm,
        )
        for part in audio_parts
    ]

    # If this project came from IMPORT and the user uploaded a WAV beat, mix it in.
    beat_wav = b""
    if project.get("source") == "import" and st.session_state.import_beat_wav_bytes:
        target_sr = 44100 if st.session_state.engine_type == ENGINE_STUDIO else 22050
        beat_wav = sound.resample_wav_bytes(st.session_state.import_beat_wav_bytes, target_sr)
        beat_wav = sound.apply_gain_wav_bytes(beat_wav, gain=0.75)

    st.audio(sound.mix_wav_audios(([beat_wav] if beat_wav else []) + audio_blobs), format="audio/wav")


def save_project_to_archive(project):
    payload = project_to_payload(project)
    instrument_label = project["main_instrument"] if not project.get("layers") else f"{project['main_instrument']} + vrstvy"
    db.save_to_db(project["title"], project["theme"], instrument_label, payload, st.session_state.bpm, 5)
    st.toast("Uloženo do archivu! ✅")


def render_melody_card(project, index):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    top_left, top_right = st.columns([1.6, 1], gap="medium")

    with top_left:
        st.markdown(f"<div class='proposal-label'>NÁVRH Č. {index + 1}</div>", unsafe_allow_html=True)
        st.markdown('<div class="melody-plot">', unsafe_allow_html=True)
        st.pyplot(
            ui.create_piano_roll(get_combined_notes(project), st.session_state.chart_style, st.session_state.p_color),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with top_right:
        st.markdown('<div class="side-panel">', unsafe_allow_html=True)

        # 1) Audio player always on top of the right column (per user request).
        st.markdown('<div class="audio-deck">', unsafe_allow_html=True)
        render_project_audio_player(project, index)
        st.markdown("</div>", unsafe_allow_html=True)

        # 2) Instrument
        engine_choice = st.session_state.engine_type
        if engine_choice == ENGINE_LAB:
            wave_keys = list(LAB_WAVES.keys())
            current_wave = project.get("main_instrument", "Sinus")
            wave_index = wave_keys.index(current_wave) if current_wave in LAB_WAVES else 0
            project["main_instrument"] = st.selectbox("Vlna:", wave_keys, index=wave_index, key=f"sel_lab_{index}")
        else:
            current_instr = project.get("main_instrument", "Acoustic Grand Piano")
            instr_index = DISPLAY_STUDIO_INSTRUMENTS.index(current_instr) if current_instr in DISPLAY_STUDIO_INSTRUMENTS else 0
            project["main_instrument"] = st.selectbox("Nástroj:", DISPLAY_STUDIO_INSTRUMENTS, index=instr_index, key=f"sel_std_{index}")

        # 3) Project title
        project["title"] = st.text_input("Název projektu:", value=project["title"], key=f"name_{index}")

        # 4) Octave + BPM in one row
        octave_key = ensure_project_octave(index)
        c_oct, c_bpm = st.columns([1, 1], gap="small")
        with c_oct:
            o1, o2, o3 = st.columns([0.28, 0.44, 0.28], gap="small")
            if o1.button("-", key=f"oct_dn_{index}", use_container_width=True):
                st.session_state[octave_key] -= 1
                st.rerun()
            with o2:
                st.markdown(
                    f"<div class='octave-display'>OKTÁVA <span style='opacity:.85'>{int(st.session_state[octave_key]):+d}</span></div>",
                    unsafe_allow_html=True,
                )
            if o3.button("+", key=f"oct_up_{index}", use_container_width=True):
                st.session_state[octave_key] += 1
                st.rerun()

        with c_bpm:
            b1, b2, b3 = st.columns([0.28, 0.44, 0.28], gap="small")
            if b1.button("-", key=f"bpm_dn_{index}", use_container_width=True):
                st.session_state.bpm = max(40, st.session_state.bpm - 5)
                st.rerun()
            with b2:
                st.markdown(
                    f"<div class='octave-display'>BPM <span style='opacity:.85'>{int(st.session_state.bpm)}</span></div>",
                    unsafe_allow_html=True,
                )
            if b3.button("+", key=f"bpm_up_{index}", use_container_width=True):
                st.session_state.bpm = min(220, st.session_state.bpm + 5)
                st.rerun()

        # 5) MIDI + Save in one row
        c_midi, c_save = st.columns([1, 1], gap="small")
        with c_midi:
            st.download_button(
                "🎹 MIDI",
                sound.export_to_midi(get_combined_notes(project), st.session_state.bpm, instrument_id=0),
                f"{project['title']}.mid",
                key=f"midi_dl_{index}",
                use_container_width=True,
            )

        with c_save:
            if st.button("⭐ Uložit", key=f"save_db_{index}", use_container_width=True):
                save_project_to_archive(project)

        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.projects[index] = project
    st.markdown("</div>", unsafe_allow_html=True)


# -*- coding: utf-8 -*-

import streamlit as st

import Pamet_a_archiv as db
import Vizual_a_grafika as ui
import Zvuk_a_export as sound
from app.config import DISPLAY_STUDIO_INSTRUMENTS, ENGINE_LAB, ENGINE_STUDIO, LAB_WAVES, STUDIO_INSTRUMENTS
from core.humanize import apply_humanize
from core.tags import derive_tags, tags_to_str
from core.projects import build_audio_parts, ensure_project_octave, get_combined_notes, project_to_payload
from ui.audio_cache import prep_import_beat_wav_cached, synthesise_full_audio_cached


def _sync_project_instrument_from_state(project, index, engine_choice, session_state):
    instr_key = f"sel_lab_{index}" if engine_choice == ENGINE_LAB else f"sel_std_{index}"
    if instr_key in session_state:
        project["main_instrument"] = str(session_state.get(instr_key) or project.get("main_instrument"))
    else:
        project_default = project.get(
            "main_instrument",
            "Sinus" if engine_choice == ENGINE_LAB else "Acoustic Grand Piano",
        )
        session_state[instr_key] = str(project_default)
    return instr_key


def render_project_audio_player(project, index):
    octave_key = ensure_project_octave(index)
    audio_parts = build_audio_parts(project, st.session_state[octave_key])
    seed_base = int(project.get("seed") or 0)
    human = str(project.get("humanize") or "Off")
    bars = int(project.get("bars") or 0) or None

    audio_blobs = []
    for j, part in enumerate(audio_parts):
        mel = apply_humanize(part["melody"], human, seed=seed_base + (j * 10007), bars=bars)
        audio_blobs.append(
            synthesise_full_audio_cached(
                mel,
                engine_type=part["engine_type"],
                instrument_id=part["instrument_id"],
                octave_shift=part["octave_shift"],
                bpm=st.session_state.bpm,
            )
        )

    beat_wav = b""
    if project.get("source") == "import" and st.session_state.import_beat_wav_bytes:
        target_sr = 44100 if st.session_state.engine_type == ENGINE_STUDIO else 22050
        beat_wav = prep_import_beat_wav_cached(st.session_state.import_beat_wav_bytes, target_sr, 0.75)

    st.audio(sound.mix_wav_audios(([beat_wav] if beat_wav else []) + audio_blobs), format="audio/wav")




def save_project_to_archive(project, rating=5):
    project["note_density"] = str(st.session_state.get("note_density") or project.get("note_density") or "Normál")
    project["note_role"] = str(st.session_state.get("note_role") or project.get("note_role") or "Lead")
    payload = project_to_payload(project)
    instrument_label = project["main_instrument"] if not project.get("layers") else f"{project['main_instrument']} + vrstvy"
    auto_tags = derive_tags(project.get("theme", ""), project.get("main_instrument", ""))
    db.save_to_db(
        project["title"],
        project["theme"],
        instrument_label,
        payload,
        st.session_state.bpm,
        int(rating),
        tags=tags_to_str(auto_tags),
        source_type=(
            "dataset"
            if str(project.get("melody_style") or "").strip().lower() == "dataset style"
            else "generated"
        ),
    )
    st.toast("Uloženo do archivu.")


def render_melody_card(project, index):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    top_left, top_right = st.columns([1.6, 1], gap="medium")

    with top_left:
        st.markdown(f"<div class='proposal-label'>NÁVRH Č. {index + 1}</div>", unsafe_allow_html=True)
        q_score = project.get("quality_score")
        g_seed = project.get("generation_seed")
        cand_n = project.get("candidate_count")
        if q_score is not None or g_seed is not None:
            score_txt = f"{float(q_score):.1f}" if isinstance(q_score, (int, float)) else "—"
            seed_txt = str(int(g_seed)) if isinstance(g_seed, (int, float)) else "—"
            cand_txt = str(int(cand_n)) if isinstance(cand_n, (int, float)) else "—"
            st.markdown(
                "<div style='font-size:.78rem; opacity:.85; margin:.15rem 0 .35rem 0;'>"
                f"<span title='Interní hodnocení kvality melodie. Vyšší číslo = lepší kandidát.'>"
                f"Kvalita: <b>{score_txt}</b></span>"
                " &nbsp;•&nbsp; "
                f"<span title='Seed použitý pro vybraný návrh. Hodí se pro reprodukovatelnost.'>"
                f"Seed: <b>{seed_txt}</b></span>"
                " &nbsp;•&nbsp; "
                f"<span title='Kolik interních pokusů se porovnalo před výběrem.'>"
                f"Pokusy: <b>{cand_txt}</b></span>"
                "</div>",
                unsafe_allow_html=True,
            )
        st.markdown('<div class="melody-plot">', unsafe_allow_html=True)
        st.pyplot(
            ui.create_piano_roll(get_combined_notes(project), st.session_state.chart_style, st.session_state.p_color),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with top_right:
        st.markdown('<div class="side-panel">', unsafe_allow_html=True)

        engine_choice = st.session_state.engine_type
        instr_key = _sync_project_instrument_from_state(project, index, engine_choice, st.session_state)

        # Keep humanize value available for playback/export, but hide the card control.
        project["humanize"] = str(st.session_state.get("preset_humanize") or project.get("humanize") or "Off")

        # 1) Přehrávač
        st.markdown('<div class="audio-deck">', unsafe_allow_html=True)
        render_project_audio_player(project, index)
        st.markdown("</div>", unsafe_allow_html=True)

        locked = bool(project.get("locked"))

        # 2) Jméno projektu + Variace
        c_title, c_var_top = st.columns([1.6, 1], gap="small")
        with c_title:
            name_key = f"name_{index}"
            # Keep widget value in sync with regenerated project title.
            if str(st.session_state.get(name_key, "")) != str(project.get("title", "")):
                st.session_state[name_key] = str(project.get("title", ""))
            project["title"] = st.text_input(
                "Název projektu",
                value=project["title"],
                key=name_key,
                label_visibility="collapsed",
                placeholder="Název projektu…",
            )
        with c_var_top:
            if st.button("🧬 Variace", key=f"var_{index}", use_container_width=True, help="Udělá chytrou variaci aktuálního návrhu.\nKdy: Když chceš podobný nápad, ale ne úplně od nuly.\nDopad: Zachová groove, jemně změní noty/rytmus."):
                if not locked:
                    st.session_state["variation_one_index"] = int(index)
                st.rerun()

        # 3) Nástroje (popover + radio)
        engine_choice = st.session_state.engine_type
        if engine_choice == ENGINE_LAB:
            instrument_options = list(LAB_WAVES.keys())
            default_instrument = "Sinus"
        else:
            instrument_options = DISPLAY_STUDIO_INSTRUMENTS
            default_instrument = "Acoustic Grand Piano"

        current_instrument = str(st.session_state.get(instr_key) or project.get("main_instrument", default_instrument))
        if current_instrument not in instrument_options:
            current_instrument = instrument_options[0]

        popover_label = f"🎛️ Nástroje · {current_instrument}"
        with st.popover(popover_label, use_container_width=True):
            st.caption("Vyber hlavní nástroj pro tento návrh.")
            chosen_instrument = st.radio(
                "Vyber nástroj",
                instrument_options,
                index=instrument_options.index(current_instrument),
                key=instr_key,
                label_visibility="collapsed",
            )
        project["main_instrument"] = str(chosen_instrument)

        # Persist into the session list
        if st.session_state.projects and 0 <= int(index) < len(st.session_state.projects):
            st.session_state.projects[index] = project

        # 4) Oktáva + BPM
        octave_key = ensure_project_octave(index)
        c_oct, c_bpm = st.columns([1, 1], gap="small")
        with c_oct:
            o1, o2, o3 = st.columns([0.28, 0.44, 0.28], gap="small")
            if o1.button("-", key=f"oct_dn_{index}", use_container_width=True, help="Sníží oktávu o 1.\nKdy: Když je melodie moc vysoko.\nDopad: Tmavší/hlubší charakter."):
                st.session_state[octave_key] -= 1
                st.rerun()
            with o2:
                st.markdown(
                    f"<div class='octave-display'>OKTÁVA <span style='opacity:.85'>{int(st.session_state[octave_key]):+d}</span></div>",
                    unsafe_allow_html=True,
                )
            if o3.button("+", key=f"oct_up_{index}", use_container_width=True, help="Zvýší oktávu o 1.\nKdy: Když je melodie moc nízko.\nDopad: Jasnější/výraznější charakter."):
                st.session_state[octave_key] += 1
                st.rerun()

        with c_bpm:
            b1, b2, b3 = st.columns([0.28, 0.44, 0.28], gap="small")
            if b1.button("-", key=f"bpm_dn_{index}", use_container_width=True, help="Sníží BPM o 5.\nKdy: Když chceš klidnější groove.\nDopad: Pomalejší playback i MIDI export."):
                st.session_state["bpm_pending"] = max(40, int(st.session_state.bpm) - 5)
                st.rerun()
            with b2:
                st.markdown(
                    f"<div class='octave-display'>BPM <span style='opacity:.85'>{int(st.session_state.bpm)}</span></div>",
                    unsafe_allow_html=True,
                )
            if b3.button("+", key=f"bpm_up_{index}", use_container_width=True, help="Zvýší BPM o 5.\nKdy: Když chceš energičtější groove.\nDopad: Rychlejší playback i MIDI export."):
                st.session_state["bpm_pending"] = min(220, int(st.session_state.bpm) + 5)
                st.rerun()

        # 5) Odemčeno + Regenerovat
        c_lock, c_regen = st.columns([1, 1], gap="small")
        with c_lock:
            if st.button("🔒 Zamknuto" if locked else "🔓 Odemčeno", key=f"lock_{index}", use_container_width=True, help="Zamkne nebo odemkne tento návrh.\nKdy: Když si chceš nechat dobrý motiv.\nDopad: Zamknutý návrh se nepřepíše při regeneraci."):
                project["locked"] = not locked
                st.session_state.projects[index] = project
                st.rerun()
        with c_regen:
            regen_label = "🔁 Regenerovat" if not locked else "🔁 Regenerovat ostatní"
            if st.button(regen_label, key=f"regen_{index}", use_container_width=True, help="Přegeneruje návrh.\nKdy: Když chceš novou variantu.\nDopad: Odemčené návrhy se nahradí novými."):
                if locked:
                    st.session_state["regen_unlocked_skip"] = int(index)
                else:
                    st.session_state["regen_one_index"] = int(index)
                st.rerun()

        # 6) MIDI + Uložit
        c_midi, c_save = st.columns([1, 1], gap="small")
        with c_midi:
            seed_base = int(project.get("seed") or 0)
            human = str(project.get("humanize") or "Off")
            bars = int(project.get("bars") or 0) or None

            combined_h = []
            main_h = apply_humanize(project.get("melody", []), human, seed=seed_base + 0, bars=bars) or []
            combined_h.extend(main_h)
            for j, layer in enumerate(project.get("layers", []) or []):
                combined_h.extend(apply_humanize(layer.get("melody", []), human, seed=seed_base + ((j + 1) * 10007), bars=bars) or [])
            combined_h.sort(key=lambda x: (float(x[0]), int(x[1])))

            q = str(st.session_state.get("quantize_grid") or "Off")
            if q != "Off":
                grid = 0.5 if q == "1/8" else 0.25
                max_t = float(int(bars) * 4) if bars else None
                q_notes = []
                for n in combined_h:
                    if len(n) < 3:
                        continue
                    start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
                    vel = int(n[3]) if len(n) > 3 else 90
                    start_q = round(round(start / grid) * grid, 4)
                    dur_q = round(round(dur / grid) * grid, 4)
                    dur_q = max(grid, dur_q)
                    if max_t is not None:
                        if start_q >= max_t:
                            start_q = max(0.0, max_t - grid)
                        if start_q + dur_q > max_t:
                            dur_q = max(grid, max_t - start_q)
                    q_notes.append([start_q, pitch, dur_q, vel])
                q_notes.sort(key=lambda x: (float(x[0]), int(x[1])))
                combined_h = q_notes

            st.download_button(
                "🎹 MIDI",
                sound.export_to_midi(
                    combined_h if combined_h else get_combined_notes(project),
                    st.session_state.bpm,
                    instrument_id=(
                        int(STUDIO_INSTRUMENTS.get(project.get("main_instrument"), 0))
                        if st.session_state.engine_type != ENGINE_LAB
                        else 0
                    ),
                ),
                f"{project['title']}.mid",
                key=f"midi_dl_{index}",
                use_container_width=True,
                help="Stáhne MIDI soubor.\nKdy: Pro další práci ve FL/Abletonu.\nDopad: Export respektuje BPM, nástroj i humanize/quantize.",
            )

        with c_save:
            rating_key = f"save_rating_{index}"
            if rating_key not in st.session_state:
                st.session_state[rating_key] = 5
            current_rating = int(st.session_state.get(rating_key) or 5)
            current_rating = max(1, min(5, current_rating))
            stars_label = "⭐" * current_rating + "✩" * (5 - current_rating)
            with st.popover(f"{stars_label} ▾", use_container_width=True):
                rating_options = [5, 4, 3, 2, 1]
                st.caption("Klikni na hodnocení pro uložení do archivu.")
                for r in rating_options:
                    if st.button(
                        "⭐" * int(r) + "✩" * (5 - int(r)),
                        key=f"{rating_key}_pick_{r}",
                        use_container_width=True,
                    ):
                        st.session_state[rating_key] = int(r)
                        save_project_to_archive(project, rating=int(r))
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.projects[index] = project
    st.markdown("</div>", unsafe_allow_html=True)


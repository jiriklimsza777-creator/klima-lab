# -*- coding: utf-8 -*-

import random
from pathlib import Path
from datetime import datetime

import streamlit as st

import Generator_not as logic
import Pamet_a_archiv as db
import Zvuk_a_export as sound
from core.tags import COMMON_TAGS, str_to_tags, tags_to_str
from ui.audio_cache import synthesise_full_audio_cached
from app.config import (
    APP_VERSION,
    ENGINE_LAB,
    ENGINE_STUDIO,
    LAB_WAVES,
    PAGE_GENERATOR,
    STUDIO_INSTRUMENTS,
)
from app.state import reset_project_widget_state
from app.utils import get_theme_string
from core.projects import create_project, get_combined_notes, normalize_project_payload
from ui.cards import render_melody_card


PRESETS = [
    {
        "label": "BoomBap Jazz",
        "note_role": "Lead",
        "note_density": "Normál",
        "humanize": "Groove",
        "instrument": "Rhodes Piano",
    },
    {
        "label": "Dark Piano",
        "note_role": "Lead",
        "note_density": "Méně not",
        "humanize": "Tight",
        "instrument": "Acoustic Grand Piano",
    },
    {
        "label": "Premo Horn Stabs",
        "note_role": "Counter",
        "note_density": "Méně not",
        "humanize": "Groove",
        "instrument": "Alto Sax",
    },
    {
        "label": "LoFi Rainy",
        "note_role": "Lead",
        "note_density": "Méně not",
        "humanize": "Loose",
        "instrument": "Rhodes Piano",
    },
    {
        "label": "Bassline Pocket",
        "note_role": "Bass",
        "note_density": "Normál",
        "humanize": "Tight",
        "instrument": "Electric Bass",
    },
    {
        "label": "Dreamy Pads",
        "note_role": "Counter",
        "note_density": "Méně not",
        "humanize": "Loose",
        "instrument": "Pad (warm)",
    },
]

SOLO_CHIPS = [
    {"label": "🎷 Sax", "style": "Sax", "note_role": "Lead", "note_density": "Normál", "humanize": "Groove", "instrument": "Alto Sax"},
    {"label": "🎹 Piano", "style": "Piano", "note_role": "Lead", "note_density": "Normál", "humanize": "Tight", "instrument": "Acoustic Grand Piano"},
    {"label": "🎹 Rhodes", "style": "Rhodes", "note_role": "Lead", "note_density": "Normál", "humanize": "Groove", "instrument": "Rhodes Piano"},
    {"label": "🎺 Trumpet", "style": "Trumpet", "note_role": "Lead", "note_density": "Normál", "humanize": "Groove", "instrument": "Trumpet"},
    {"label": "🪈 Flute", "style": "Flute", "note_role": "Lead", "note_density": "Normál", "humanize": "Loose", "instrument": "Flute"},
    {"label": "🪘 Marimba", "style": "Marimba", "note_role": "Lead", "note_density": "Normál", "humanize": "Tight", "instrument": "Marimba"},
    {"label": "🔔 Vibraphone", "style": "Vibraphone", "note_role": "Lead", "note_density": "Normál", "humanize": "Groove", "instrument": "Vibraphone"},
    {"label": "🎸 Akustik. bass", "style": "Akustik Bass", "note_role": "Bass", "note_density": "Méně not", "humanize": "Tight", "instrument": "Acoustic Bass"},
]


_DENSITY_UI_ORDER = ["Málo", "Středně", "Hodně"]
_DENSITY_UI_TO_INTERNAL = {"Málo": "Méně not", "Středně": "Normál", "Hodně": "Více not"}
_DENSITY_INTERNAL_TO_UI = {v: k for k, v in _DENSITY_UI_TO_INTERNAL.items()}


def _cycle_index(cur, items, delta: int):
    if not items:
        return None
    try:
        i = items.index(cur)
    except Exception:
        i = 0
    return items[(i + int(delta)) % len(items)]


def _render_topbar_controls():
    """
    One-line top bar:
      Producenti | Počet | BPM | Takty | Hustota | Role | Témata

    All +/- actions use *_pending keys so we never mutate widget-backed session_state
    after the sidebar widgets are instantiated.
    """
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    cols = st.columns([1.25, 1, 1, 1, 1, 1, 1.25], gap="small")

    # Producers / Themes are controlled via pending values for the sidebar selectboxes.
    try:
        all_producers, all_themes = db.get_producers_and_themes()
    except Exception:
        all_producers, all_themes = ([], [])

    cur_prod = str(st.session_state.get("selected_producer") or "")
    cur_theme = str(st.session_state.get("selected_theme") or "")

    def _producer_picker():
        if not all_producers:
            st.button("Producenti", disabled=True, use_container_width=True, key="top_producer_disabled")
            return
        if hasattr(st, "popover"):
            with st.popover("Producenti", use_container_width=True):
                idx = all_producers.index(cur_prod) if cur_prod in all_producers else 0
                picked = st.radio(
                    "Vyber producenta",
                    all_producers,
                    index=idx,
                    horizontal=False,
                    key="top_producer_pick",
                    label_visibility="collapsed",
                )
                if picked and str(picked) != cur_prod:
                    st.session_state["producer_sel_pending"] = str(picked)
                    st.rerun()
        else:
            idx = all_producers.index(cur_prod) if cur_prod in all_producers else 0
            picked = st.selectbox("Producenti", all_producers, index=idx, key="top_producer_pick", label_visibility="collapsed")
            if picked and str(picked) != cur_prod:
                st.session_state["producer_sel_pending"] = str(picked)
                st.rerun()

    def _theme_picker():
        if not all_themes:
            st.button("Témata", disabled=True, use_container_width=True, key="top_theme_disabled")
            return
        if hasattr(st, "popover"):
            with st.popover("Témata", use_container_width=True):
                idx = all_themes.index(cur_theme) if cur_theme in all_themes else 0
                picked = st.radio(
                    "Vyber téma",
                    all_themes,
                    index=idx,
                    horizontal=False,
                    key="top_theme_pick",
                    label_visibility="collapsed",
                )
                if picked and str(picked) != cur_theme:
                    st.session_state["theme_sel_pending"] = str(picked)
                    st.rerun()
        else:
            idx = all_themes.index(cur_theme) if cur_theme in all_themes else 0
            picked = st.selectbox("Témata", all_themes, index=idx, key="top_theme_pick", label_visibility="collapsed")
            if picked and str(picked) != cur_theme:
                st.session_state["theme_sel_pending"] = str(picked)
                st.rerun()

    with cols[0]:
        _producer_picker()

    # Solo instrument picker (replaces BPM in topbar).
    cur_solo_style = str(st.session_state.get("solo_style_last") or "Sax")
    solo_styles = [str(ch.get("style") or "") for ch in SOLO_CHIPS if str(ch.get("style") or "").strip()]
    solo_label_map = {str(ch.get("style") or ""): str(ch.get("label") or ch.get("style") or "") for ch in SOLO_CHIPS}
    if cur_solo_style not in solo_styles and solo_styles:
        cur_solo_style = solo_styles[0]
    with cols[1]:
        if hasattr(st, "popover"):
            with st.popover("Nástroje ▾", use_container_width=True):
                picked = st.radio(
                    "Vyber nástroj",
                    solo_styles,
                    index=solo_styles.index(cur_solo_style) if cur_solo_style in solo_styles else 0,
                    format_func=lambda s: solo_label_map.get(str(s), str(s)),
                    horizontal=False,
                    key="top_solo_pick",
                    label_visibility="collapsed",
                )
                if picked and str(picked) != cur_solo_style:
                    st.session_state["local_melody_style_pending"] = str(picked)
                    st.session_state["solo_style_last"] = str(picked)
                    st.rerun()
        else:
            picked = st.selectbox(
                "Nástroje",
                solo_styles,
                index=solo_styles.index(cur_solo_style) if cur_solo_style in solo_styles else 0,
                format_func=lambda s: solo_label_map.get(str(s), str(s)),
                key="top_solo_pick",
                label_visibility="collapsed",
            )
            if picked and str(picked) != cur_solo_style:
                st.session_state["local_melody_style_pending"] = str(picked)
                st.session_state["solo_style_last"] = str(picked)
                st.rerun()

    # Počet melodií (popover like Hustota/Role)
    variants = int(st.session_state.get("num_variants") or 1)
    variants = max(1, min(12, variants))
    with cols[2]:
        if hasattr(st, "popover"):
            with st.popover(f"Počet: {variants} ▾", use_container_width=True):
                picked = st.radio(
                    "Vyber počet",
                    list(range(1, 13)),
                    index=int(variants) - 1,
                    horizontal=False,
                    key="top_variants_pick",
                    label_visibility="collapsed",
                )
                if picked and int(picked) != int(variants):
                    st.session_state["num_variants_pending"] = int(picked)
                    st.rerun()
        else:
            picked = st.selectbox(
                "Počet",
                list(range(1, 13)),
                index=int(variants) - 1,
                key="top_variants_pick",
                label_visibility="collapsed",
            )
            if picked and int(picked) != int(variants):
                st.session_state["num_variants_pending"] = int(picked)
                st.rerun()

    # Počet taktů (popover)
    bars = int(st.session_state.get("num_bars") or 4)
    bars = max(1, min(16, bars))
    is_solo_mode = str(st.session_state.get("gen_mode") or "") == "Sola"
    bars_opts = list(range(2, 17, 2)) if is_solo_mode else list(range(1, 17))
    with cols[3]:
        if hasattr(st, "popover"):
            with st.popover(f"Takty: {bars} ▾", use_container_width=True):
                picked = st.radio(
                    "Vyber počet taktů",
                    bars_opts,
                    index=bars_opts.index(int(bars)) if int(bars) in bars_opts else 0,
                    horizontal=False,
                    key="top_bars_pick",
                    label_visibility="collapsed",
                )
                if picked and int(picked) != int(bars):
                    st.session_state["num_bars_pending"] = int(picked)
                    st.rerun()
        else:
            picked = st.selectbox(
                "Takty",
                bars_opts,
                index=bars_opts.index(int(bars)) if int(bars) in bars_opts else 0,
                key="top_bars_pick",
                label_visibility="collapsed",
            )
            if picked and int(picked) != int(bars):
                st.session_state["num_bars_pending"] = int(picked)
                st.rerun()

    # Hustota (Málo/Středně/Hodně) as a slide-out picker (like Producenti/Témata).
    dens_internal = str(st.session_state.get("note_density") or "Normál")
    dens_ui = _DENSITY_INTERNAL_TO_UI.get(dens_internal, "Středně")
    dens_ui = dens_ui if dens_ui in _DENSITY_UI_ORDER else "Středně"
    with cols[4]:
        if hasattr(st, "popover"):
            with st.popover("Hustota ▾", use_container_width=True):
                picked = st.radio(
                    "Vyber hustotu",
                    _DENSITY_UI_ORDER,
                    index=_DENSITY_UI_ORDER.index(dens_ui) if dens_ui in _DENSITY_UI_ORDER else 1,
                    horizontal=False,
                    key="top_density_pick",
                    label_visibility="collapsed",
                )
                if picked and str(picked) != dens_ui:
                    st.session_state["note_density_pending"] = _DENSITY_UI_TO_INTERNAL.get(str(picked), "Normál")
                    st.rerun()
        else:
            picked = st.selectbox(
                "Hustota",
                _DENSITY_UI_ORDER,
                index=_DENSITY_UI_ORDER.index(dens_ui) if dens_ui in _DENSITY_UI_ORDER else 1,
                key="top_density_pick",
                label_visibility="collapsed",
            )
            if picked and str(picked) != dens_ui:
                st.session_state["note_density_pending"] = _DENSITY_UI_TO_INTERNAL.get(str(picked), "Normál")
                st.rerun()

    # Role (Lead/Counter/Bass) as a slide-out picker (like Producenti/Témata).
    role_order = ["Lead", "Counter", "Bass"]
    cur_role = str(st.session_state.get("note_role") or "Lead")
    cur_role = cur_role if cur_role in role_order else "Lead"
    with cols[5]:
        if hasattr(st, "popover"):
            with st.popover(f"Role: {cur_role} ▾", use_container_width=True):
                picked = st.radio(
                    "Vyber roli",
                    role_order,
                    index=role_order.index(cur_role) if cur_role in role_order else 0,
                    horizontal=False,
                    key="top_role_pick",
                    label_visibility="collapsed",
                )
                if picked and str(picked) != cur_role:
                    st.session_state["note_role_pending"] = str(picked)
                    st.rerun()
        else:
            picked = st.selectbox(
                "Role",
                role_order,
                index=role_order.index(cur_role) if cur_role in role_order else 0,
                key="top_role_pick",
                label_visibility="collapsed",
            )
            if picked and str(picked) != cur_role:
                st.session_state["note_role_pending"] = str(picked)
                st.rerun()

    with cols[6]:
        _theme_picker()


def _render_preset_chips():
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1, 1, 1, 1, 1], gap="small")
    clicked = None
    for i, preset in enumerate(PRESETS):
        with cols[i]:
            if st.button(preset["label"], key=f"preset_{i}", use_container_width=True):
                clicked = preset
    if clicked:
        # Can't mutate widget-backed keys after instantiation; use pending keys and rerun.
        st.session_state["note_role_pending"] = clicked["note_role"]
        st.session_state["note_density_pending"] = clicked["note_density"]
        st.session_state["preset_humanize_pending"] = clicked["humanize"]
        st.session_state["preset_instrument_pending"] = clicked["instrument"]
        st.session_state["active_preset_pending"] = clicked["label"]
        # Also apply to current projects (audio feel changes immediately).
        st.session_state["apply_preset_projects_pending"] = {
            "label": clicked["label"],
            "note_role": clicked["note_role"],
            "note_density": clicked["note_density"],
            "humanize": clicked["humanize"],
            "instrument": clicked["instrument"],
        }
        st.toast(f"Preset: {clicked['label']}")
        st.rerun()


def _render_solo_chips():
    """
    Solo instrument selector chips shown above GENEROVAT when gen_mode == "Sola".
    Layout: 5 chips on the first row, 3 chips centered on the second row.
    Producer/theme are handled by the shared topbar for all modes.
    """
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    top = SOLO_CHIPS[:5]
    bottom = SOLO_CHIPS[5:8]

    clicked = None
    cols = st.columns([1, 1, 1, 1, 1], gap="small")
    for i, chip in enumerate(top):
        with cols[i]:
            if st.button(chip["label"], key=f"solo_chip_top_{i}", use_container_width=True):
                clicked = chip

    if bottom:
        cols2 = st.columns([1.65, 1, 1, 1, 1.65], gap="small")
        start_col = 1  # center 3 chips into columns 1..3
        for j, chip in enumerate(bottom):
            with cols2[start_col + j]:
                if st.button(chip["label"], key=f"solo_chip_bot_{j}", use_container_width=True):
                    clicked = chip

    if clicked:
        # Apply via pending keys (widget-safe) and rerun.
        st.session_state["local_melody_style_pending"] = str(clicked["style"])
        st.session_state["note_role_pending"] = str(clicked["note_role"])
        st.session_state["note_density_pending"] = str(clicked["note_density"])
        st.session_state["preset_humanize_pending"] = str(clicked["humanize"])
        st.session_state["preset_instrument_pending"] = str(clicked["instrument"])
        st.session_state["active_preset_pending"] = "Custom"
        # Remember last chosen solo instrument so the sidebar "Sola" keeps it.
        st.session_state["solo_style_last"] = str(clicked["style"])
        st.toast(f"Sólo: {clicked['label']}")
        st.rerun()


def _infer_active_preset_label() -> str:
    """
    Compute what preset matches the *current* controls so the status line reflects reality.
    If nothing matches, return "Custom".
    """
    role = str(st.session_state.get("note_role") or "")
    density = str(st.session_state.get("note_density") or "")
    human = str(st.session_state.get("preset_humanize") or "")
    instr = str(st.session_state.get("preset_instrument") or "")
    for p in PRESETS:
        if (
            str(p.get("note_role")) == role
            and str(p.get("note_density")) == density
            and str(p.get("humanize")) == human
            and str(p.get("instrument")) == instr
        ):
            return str(p.get("label") or "Custom")
    return "Custom"


def _infer_active_solo_label() -> str:
    """Name of the currently selected solo chip (for the status line above GENEROVAT)."""
    style = str(st.session_state.get("solo_style_last") or "")
    for p in SOLO_CHIPS:
        if str(p.get("style") or "") == style:
            label = str(p.get("label") or style or "Sax")
            # SOLO_CHIPS labels are "emoji + name". Show just the name in the status line.
            if label and not label[0].isalnum() and " " in label:
                return label.split(" ", 1)[1].strip()
            return label
    return style or "Sax"


def _render_tutorial_body():
    """
    Shared tutorial content. Kept in one place so it's easy to maintain as features grow.
    """
    import streamlit as st
    from PIL import Image

    from app.config import LOGO_PATH

    tab_overview, tab_generator, tab_sola, tab_import, tab_archive, tab_export, tab_brand = st.tabs(
        ["Přehled", "Generator", "Sola", "Import", "Archiv", "Export", "Klima"]
    )

    with tab_overview:
        st.markdown(
            """
### Tutorial Pro Blbce (rychle a bez bolesti)
1. V sidebaru vyber `Generátor`:  
   - `Lokální (Random)` = náhoda a nápady  
   - `Dataset Style` = jede podle tvých MIDI datasetů  
   - `AI (ChatGPT)` = AI generování přes API klíč
2. Pod tím nastav `Co generovat` (nebo v Dataset režimu `Melodie / Akordy / Melodie + akordy / Balík frází`).
3. Klikni `GENEROVAT`.
4. U návrhu si můžeš dát `Variace`, změnit `Nástroj`, `BPM`, `Oktávu`, pak stáhnout `MIDI` nebo uložit do archivu.

### Důležité
- `Zamknuto` = ten návrh se nepřepíše při další regeneraci.
- `Variace` = podobný nápad, ne úplně od nuly.
- Appka si drží stav sama, takže je normální, že se UI při kliknutí překreslí.
            """
        )

    with tab_generator:
        st.markdown(
            """
### Generátor (co kde dělá)
- `Melodic`: jedna hlavní melodie.
- `Loop`: boombap otázka-odpověď.
- `Chords`: akordový loop.

### Dataset Style režim
- Bere MIDI z `datasets/midi`.
- Funguje i bez producenta a tématu.
- `Voicing akordů`: `Tight / Wide / Jazz / Dark`.

### Karta návrhu
- `🧬 Variace`: jemně upraví aktuální nápad.
- `🎛️ Nástroje`: změní zvuk přehrání/exportu.
- `🔒 Zamknout`: ochrání návrh před přepsáním.
            """
        )

    with tab_sola:
        st.markdown(
            """
### Sola
- Krátké, hudební, většinou 4-8 taktů.
- Nástroj pro sola vybíráš nahoře přes chips/picker.
- Vize (text) může změnit vibe:  
  - `klidné, bez příběhu`  
  - `divoké, příběh`
            """
        )

    with tab_import:
        st.markdown(
            """
### Import
- Nahraj `WAV` nebo `MP3`.
- U WAV se odhadne BPM.
- Vygeneruje se melodie k beatu a při přehrání se beat přimíchá.
            """
        )

    with tab_archive:
        st.markdown(
            """
### Archiv 2.0
- Hledání + filtry: producent, téma, solo, zdroj.
- Nově vidíš `source_type` štítek: `generated / imported / dataset`.
- Filtr `Jen dataset návrhy` ti ukáže jen dataset věci.
- Hodnocení je přes hvězdičkový popover a můžeš ho měnit kdykoli.
            """
        )

    with tab_export:
        st.markdown(
            """
### Export
- `MIDI` tlačítko stáhne `.mid`.
- Export respektuje BPM, nástroj, quantize i humanize.
            """
        )

    with tab_brand:
        try:
            c1, c2, c3 = st.columns([1, 1.2, 1], gap="small")
            with c2:
                st.image(Image.open(LOGO_PATH), width=420)
        except Exception:
            st.info("Logo se nepodařilo načíst.")
        st.markdown("## Klima production Pičo 2026")


def render_tutorial_modal():
    """
    Show a DAW-like tutorial window that can be closed.
    Implemented as an in-page modal overlay with a close "X" so we can reliably persist the closed state across reruns.
    """
    if not st.session_state.get("show_tutorial"):
        return

    # NOTE: Disabled st.dialog because its built-in close "X" doesn't update session_state,
    # which causes the tutorial to re-open on the next Streamlit rerun.
    if False and hasattr(st, "dialog"):
        @st.dialog("Tutorial", width="large")
        def _dlg():
            c1, c2 = st.columns([1, 0.15], gap="small")
            with c1:
                st.caption("Klima Production Tutorial")
            with c2:
                if st.button("✕", key="tutorial_close_x", use_container_width=True):
                    st.session_state["show_tutorial"] = False
                    st.rerun()
            _render_tutorial_body()

        _dlg()
        return

    # Fallback (no true modal): show a centered panel.
    st.markdown(
        """
<style>
  .tutorial-panel { border:1px solid rgba(255,255,255,.18); border-radius:14px; padding:14px 14px 10px;
    background:rgba(10,12,16,.92); box-shadow:0 18px 50px rgba(0,0,0,.55); }
</style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="tutorial-panel">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 0.15], gap="small")
        with c1:
            st.caption("Klima Production Tutorial")
        with c2:
            if st.button("✕", key="tutorial_close_x_fallback", use_container_width=True):
                st.session_state["show_tutorial"] = False
                st.rerun()
        _render_tutorial_body()
        st.markdown("</div>", unsafe_allow_html=True)

def _is_sax_solo_mode() -> bool:
    # Accept both the new label ("Sax") and older archived value ("Sax Solo").
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("sax")

def _is_piano_solo_mode() -> bool:
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("piano")

def _is_rhodes_solo_mode() -> bool:
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("rhodes")

def _is_trumpet_solo_mode() -> bool:
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("trumpet")

def _is_flute_solo_mode() -> bool:
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("flute")

def _is_marimba_solo_mode() -> bool:
    return str(st.session_state.get("local_melody_style") or "").strip().lower().startswith("marimba")

def _is_vibraphone_solo_mode() -> bool:
    s = str(st.session_state.get("local_melody_style") or "").strip().lower()
    return s.startswith("vib") or s.startswith("vibra")

def _is_akustik_bass_mode() -> bool:
    s = str(st.session_state.get("local_melody_style") or "").strip().lower()
    return s.startswith("akust")

def _is_any_solo_mode() -> bool:
    return (
        _is_sax_solo_mode()
        or _is_piano_solo_mode()
        or _is_rhodes_solo_mode()
        or _is_trumpet_solo_mode()
        or _is_flute_solo_mode()
        or _is_marimba_solo_mode()
        or _is_vibraphone_solo_mode()
        or _is_akustik_bass_mode()
    )

def _roll_solo_variants(total: int, seed: int | None = None):
    """
    Returns a list of (character, story) tuples for this generation batch.
    Ensures we don't accidentally generate all proposals with the same combo (unless total==1).
    """
    total = int(max(1, total))
    rng = random.Random(int(seed) if seed is not None else None)
    combos = [("Klidné", False), ("Klidné", True), ("Divoké", False), ("Divoké", True)]
    rng.shuffle(combos)
    out = []
    if total == 1:
        return [combos[0]]
    # Guarantee at least two different combos.
    out.append(combos[0])
    out.append(combos[1])
    while len(out) < total:
        out.append(rng.choice(combos))
    rng.shuffle(out)
    return out


def _solo_vibe_from_text(text: str):
    """
    Very small parser for local (math) solo generator.
    It doesn't "understand" text like ChatGPT, but we can map keywords to knobs:
      - character: Klidné / Divoké
      - story: True / False
    """
    t = str(text or "").strip().lower()
    if not t:
        return None, None

    # Character
    char = None
    if any(w in t for w in ["divok", "wild", "agres", "hard", "rychl", "energi", "crazy"]):
            char = "Divoké"
    if any(w in t for w in ["klid", "chill", "pomal", "jemn", "soft", "smooth", "calm"]):
            char = "Klidné"

    # Story
    story = None
    if any(w in t for w in ["bez příbě", "bez pribeh", "no story", "bez story"]):
        story = False
    elif any(w in t for w in ["příbě", "pribeh", "story", "vývoj", "vyvoj", "stavba"]):
        story = True

    return char, story


def _bars_for_current_mode(default_bars: int) -> int:
    # Sax Solo is intentionally short + loop-friendly.
    if _is_any_solo_mode():
        return int(max(4, min(8, int(default_bars))))
    return int(default_bars)


def _build_generated_title(producer: str, theme: str, index: int) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    prod = str(producer or "").strip() or "Bez producenta"
    th = str(theme or "").strip() or "Bez tématu"
    return f"{prod} | {th} | {ts} | {int(index) + 1}"


def _dataset_midi_paths():
    cached = st.session_state.get("_dataset_midi_paths_cache")
    if isinstance(cached, list) and cached:
        return cached
    root = Path(__file__).resolve().parents[1] / "datasets" / "midi"
    paths = sorted([str(p) for p in root.rglob("*.mid")]) if root.exists() else []
    st.session_state["_dataset_midi_paths_cache"] = paths
    return paths


def _pick_dataset_path_nonrepeat(paths, window=24):
    pool = [str(p) for p in (paths or []) if str(p).strip()]
    if not pool:
        return None
    window = max(1, int(window))
    recent_key = "_dataset_recent_paths"
    recent = st.session_state.get(recent_key)
    if not isinstance(recent, list):
        recent = []
    recent_norm = [str(p) for p in recent if str(p)]
    blocked = set(recent_norm[-window:])
    candidates = [p for p in pool if p not in blocked]
    picked = random.choice(candidates or pool)
    recent_norm.append(str(picked))
    # Keep a bit more history than window for stable behavior after reruns.
    st.session_state[recent_key] = recent_norm[-max(window * 2, 48) :]
    return picked


def _loop_to_bars(notes, bars: int):
    if not notes:
        return []
    target_len = float(max(1, int(bars)) * 4)
    notes = [[float(n[0]), int(n[1]), float(n[2]), int(n[3]) if len(n) > 3 else 90] for n in notes if len(n) >= 3]
    if not notes:
        return []
    min_start = min(n[0] for n in notes)
    for n in notes:
        n[0] -= min_start
    src_len = max((n[0] + max(0.05, n[2])) for n in notes)
    src_len = max(1.0, float(src_len))
    out = []
    offset = 0.0
    while offset < target_len - 0.01:
        for n in notes:
            s = n[0] + offset
            if s >= target_len:
                continue
            d = min(max(0.05, n[2]), target_len - s)
            out.append([round(s, 4), n[1], round(d, 4), n[3]])
        offset += src_len
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def _split_dataset_lead_chords(notes):
    if not notes:
        return [], []
    pts = sorted([int(n[1]) for n in notes if len(n) >= 3])
    median_pitch = pts[len(pts) // 2] if pts else 60
    lead_raw = [n for n in notes if int(n[1]) >= median_pitch]
    chords_raw = [n for n in notes if int(n[1]) < median_pitch]
    if not lead_raw:
        lead_raw = list(notes)
    if not chords_raw:
        chords_raw = [n for n in notes if int(n[1]) <= median_pitch]
    # lead: monophonic-ish, keep highest note per 1/4 beat bucket
    lead_map = {}
    for n in lead_raw:
        t = round(float(n[0]) / 0.25) * 0.25
        cur = lead_map.get(t)
        if cur is None or int(n[1]) > int(cur[1]):
            lead_map[t] = n
    lead = sorted([[round(float(k), 4), int(v[1]), float(v[2]), int(v[3]) if len(v) > 3 else 90] for k, v in lead_map.items()], key=lambda x: (x[0], x[1]))
    chords = sorted([[float(n[0]), int(n[1]), float(n[2]), int(n[3]) if len(n) > 3 else 90] for n in chords_raw], key=lambda x: (x[0], x[1]))
    return lead, chords


def _apply_chord_voicing(notes, mode: str):
    if not notes:
        return notes
    mode = str(mode or "Tight")
    out = []
    for n in notes:
        if len(n) < 3:
            continue
        start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90
        p2 = pitch
        d2 = dur
        v2 = vel
        if mode == "Wide":
            p2 = p2 + (12 if p2 >= 60 else -12)
        elif mode == "Jazz":
            p2 = p2 + (2 if (int(start * 2) % 2 == 0) else 0)
            d2 = max(0.25, dur * 1.1)
        elif mode == "Dark":
            p2 = p2 - 7
            d2 = max(0.25, dur * 1.2)
            v2 = max(40, vel - 8)
        # Tight default: keep around mid register
        p2 = max(36, min(84, p2))
        out.append([round(start, 4), int(p2), round(max(0.05, d2), 4), int(max(1, min(127, v2)))])
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def _apply_dataset_theme_bias(notes, theme_text: str, influence_0_100: int):
    if not notes:
        return notes
    infl = max(0.0, min(1.0, float(influence_0_100) / 100.0))
    if infl <= 0:
        return notes
    t = str(theme_text or "").strip().lower()
    if not t:
        return notes

    calm_words = ("chill", "calm", "soft", "lofi", "lo-fi", "sad", "dark", "night", "rain", "dream")
    energy_words = ("hard", "aggr", "up", "ener", "wild", "party", "hype", "fast", "bright")
    is_calm = any(w in t for w in calm_words)
    is_energy = any(w in t for w in energy_words)
    if not is_calm and not is_energy:
        return notes

    out = []
    drop_prob = 0.0
    pitch_shift = 0
    dur_mul = 1.0
    if is_calm and not is_energy:
        drop_prob = 0.18 * infl
        pitch_shift = int(round(-3 * infl))
        dur_mul = 1.0 + (0.18 * infl)
    elif is_energy and not is_calm:
        drop_prob = 0.08 * infl
        pitch_shift = int(round(2 * infl))
        dur_mul = 1.0 - (0.12 * infl)

    for n in notes:
        if len(n) < 3:
            continue
        if drop_prob > 0 and random.random() < drop_prob:
            continue
        start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90
        p2 = max(24, min(100, pitch + pitch_shift))
        d2 = max(0.05, dur * dur_mul)
        out.append([round(start, 4), int(p2), round(d2, 4), int(max(1, min(127, vel)))])
    out.sort(key=lambda x: (x[0], x[1]))
    return out or notes


def _smart_variation(notes, bars: int):
    if not notes:
        return notes
    bars = int(max(1, bars))
    max_t = float(bars * 4)
    src = [[float(n[0]), int(n[1]), float(n[2]), int(n[3]) if len(n) > 3 else 90] for n in notes if len(n) >= 3]
    if not src:
        return notes
    out = []
    for n in src:
        start, pitch, dur, vel = n
        # pitch tweaks on a subset
        if random.random() < 0.18:
            pitch += random.choice([-2, -1, 1, 2])
        # duration tweaks
        if random.random() < 0.22:
            dur *= random.choice([0.75, 0.9, 1.1, 1.25])
        # small timing moves
        if random.random() < 0.12:
            start += random.choice([-0.25, 0.25])
        start = max(0.0, min(start, max_t - 0.05))
        dur = max(0.05, min(dur, max_t - start))
        out.append([round(start, 4), int(max(24, min(100, pitch))), round(dur, 4), int(max(1, min(127, vel)))])
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def _generate_from_dataset(bars: int):
    paths = _dataset_midi_paths()
    if not paths:
        return {"melody": [], "layers": []}
    path = _pick_dataset_path_nonrepeat(paths, window=24)
    if not path:
        return {"melody": [], "layers": []}
    try:
        midi_bytes = Path(path).read_bytes()
    except Exception:
        return {"melody": [], "layers": []}
    notes, _bpm, _instr = sound.import_midi_bytes(midi_bytes)
    notes = _loop_to_bars(notes or [], bars)
    notes = _apply_dataset_theme_bias(
        notes,
        str(st.session_state.get("current_theme_string") or ""),
        int(st.session_state.get("dataset_theme_influence") or 20),
    )
    lead, chords = _split_dataset_lead_chords(notes)
    mode = str(st.session_state.get("dataset_output_mode") or "Melodie + akordy")
    voicing = str(st.session_state.get("chord_voicing_mode") or "Tight")
    if mode == "Melodie":
        return {"melody": lead, "layers": []}
    if mode == "Akordy":
        return {"melody": _apply_chord_voicing(chords, voicing), "layers": []}
    if mode == "Balík frází":
        short = [n for n in lead if float(n[0]) < min(8.0, float(max(1, int(bars)) * 4))]
        return {"melody": short or lead, "layers": []}
    # Melodie + akordy
    return {
        "melody": lead,
        "layers": [{"instrument": "Rhodes Piano", "melody": _apply_chord_voicing(chords, voicing)}] if chords else [],
    }

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
        # Initial bars suggestion for a new upload (keeps Import UX simple).
        try:
            bpm_used = float(bpm or st.session_state.import_bpm_manual or 0)
            if bpm_used > 0:
                dur = sound.get_wav_duration_seconds(wav_bytes)
                if dur:
                    beats = (float(dur) * bpm_used) / 60.0
                    bars_suggest = int(max(1, min(16, round(beats / 4.0))))
                    st.session_state.import_bars = bars_suggest
        except Exception:
            pass


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


def _apply_ai_density(notes, density: str, bars: int):
    if not notes or not density or density == "Normál":
        return notes

    # Limit notes per bar (melody mode) to avoid "patlanina".
    limits = {"Méně not": 8, "Více not": 22}
    per_bar = limits.get(str(density), None)
    if not per_bar:
        return notes

    out = []
    notes_sorted = sorted([n for n in notes if len(n) >= 3], key=lambda x: (float(x[0]), int(x[1])))
    by_bar = {}
    for n in notes_sorted:
        bar = int(float(n[0]) // 4.0)
        if bar < 0 or bar >= int(bars):
            continue
        by_bar.setdefault(bar, []).append(n)

    for bar in range(int(bars)):
        chunk = by_bar.get(bar, [])
        out.extend(chunk[:per_bar])

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


def _apply_local_density(notes, density: str, bars: int):
    """
    For the mathematical generator:
      - "Méně not": thin per bar (keeps earliest notes).
      - "Více not": add gentle articulation by splitting long notes (no new pitches).
    """
    if not notes or not density or density == "Normál":
        return notes

    density = str(density)
    bars = int(bars)
    notes_sorted = sorted([n for n in notes if len(n) >= 3], key=lambda x: (float(x[0]), int(x[1])))

    if density == "Méně not":
        per_bar = 10
        out = []
        by_bar = {}
        for n in notes_sorted:
            bar = int(float(n[0]) // 4.0)
            if 0 <= bar < bars:
                by_bar.setdefault(bar, []).append(n)
        for b in range(bars):
            out.extend(by_bar.get(b, [])[:per_bar])
        out.sort(key=lambda x: (float(x[0]), int(x[1])))
        return out

    if density == "Více not":
        # Split longer notes into repeated hits (articulation), capped per bar.
        per_bar_cap = 26
        out = []
        by_bar = {}
        for n in notes_sorted:
            bar = int(float(n[0]) // 4.0)
            if 0 <= bar < bars:
                by_bar.setdefault(bar, []).append(n)

        for b in range(bars):
            chunk = by_bar.get(b, [])
            # If it's already dense, don't add more.
            if len(chunk) >= per_bar_cap:
                out.extend(chunk[:per_bar_cap])
                continue

            for n in chunk:
                if len(out) >= (b + 1) * per_bar_cap:
                    break
                start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
                vel = int(n[3]) if len(n) > 3 else 90
                # Only split notes that are clearly "long".
                if dur >= 1.0 and len(chunk) < per_bar_cap:
                    # Split into 0.5-beat hits, but keep within the note's duration.
                    step = 0.5
                    count = int(max(2, min(6, round(dur / step))))
                    seg = max(0.1, dur / count)
                    for k in range(count):
                        s2 = round(start + (k * seg), 4)
                        if s2 >= start + dur - 0.01:
                            break
                        out.append([s2, pitch, seg, vel])
                else:
                    out.append([start, pitch, dur, vel])

        out.sort(key=lambda x: (float(x[0]), int(x[1])))
        return out

    return notes


def _apply_melodic_density_limit(notes, density: str, bars: int):
    """
    Melodic-specific density limiter.

    User feedback: default Melodic was too dense ("preprcane").
    So we remap the effective density so that:
      - "Více not" ~= previous "Méně not" (still controlled, not a wall of notes)
      - "Normál" is slightly thinner
      - "Méně not" is clearly sparse
    """
    if not notes:
        return notes

    density = str(density or "Normál")
    bars = int(bars)
    notes_sorted = sorted([n for n in notes if len(n) >= 3], key=lambda x: (float(x[0]), int(x[1])))

    # Target notes per bar in Melodic (tight on purpose).
    if density == "Méně not":
        per_bar = 6
    elif density == "Více not":
        per_bar = 10
    else:
        per_bar = 8

    out = []
    by_bar = {}
    for n in notes_sorted:
        bar = int(float(n[0]) // 4.0)
        if 0 <= bar < bars:
            by_bar.setdefault(bar, []).append(n)
    for b in range(bars):
        out.extend(by_bar.get(b, [])[:per_bar])
    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


def _apply_melodic_duration_balance(notes, density: str, bars: int):
    """
    For Melodic (local generator only): keep note lengths consistent.
    - Tie allowed durations to Hustota not (density)
    - Avoid extreme short+long mixes inside one melody

    We slightly prefer *longer* durations (user request), but never exceed the next
    note start, so we don't introduce overlaps.
    """
    if not notes:
        return notes

    density = str(density or "Normál")
    bars = int(bars)
    max_t = float(bars * 4)

    # Density -> duration palette (beats). Keep it tight to prevent patlanina.
    # "One step longer" feel: even in dense mode we allow 0.75, and in sparse mode
    # we allow longer sustains.
    if density == "Méně not":
        pool = [0.5, 1.0, 1.5, 2.0]
        dur_cap = 2.0
    elif density == "Více not":
        pool = [0.25, 0.5, 0.75]
        dur_cap = 1.0
    else:
        pool = [0.5, 0.75, 1.0, 1.5]
        dur_cap = 1.5

    pool = sorted([float(p) for p in pool if p > 0])
    if not pool:
        return notes

    def _ceil_to_pool(d: float) -> float:
        """Prefer the next longer duration in the palette; fallback to longest."""
        d = float(d)
        for p in pool:
            if p >= d - 1e-9:
                return float(p)
        return float(pool[-1])

    # Sort by time and compute safe max duration (until next note start).
    notes_sorted = sorted([n for n in notes if len(n) >= 3], key=lambda x: (float(x[0]), int(x[1])))
    starts = [float(n[0]) for n in notes_sorted]

    out = []
    for i, n in enumerate(notes_sorted):
        start = float(n[0])
        pitch = int(n[1])
        dur = float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90

        next_start = float(starts[i + 1]) if i + 1 < len(starts) else max_t
        gap = max(0.05, next_start - start)
        # Prefer one-step longer, but never exceed the next note (no overlap) and cap.
        target = min(float(_ceil_to_pool(dur)), float(dur_cap))
        dur2 = min(target, gap)
        dur2 = max(0.05, min(dur2, max_t - start))
        out.append([float(round(start, 4)), pitch, float(round(dur2, 4)), vel])

    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


def _apply_role_postprocess(notes, role: str, bars: int):
    """
    Role shaping for both AI + local (melody mode only).
    We keep this conservative: no new pitches for Bass, only register/thinning.
    """
    if not notes:
        return notes

    role = str(role or "Lead")
    if role == "Lead":
        return notes

    bars = int(bars)
    notes_sorted = sorted([n for n in notes if len(n) >= 3], key=lambda x: (float(x[0]), int(x[1])))

    if role == "Bass":
        out = []
        # Make it low + more monophonic.
        for n in notes_sorted:
            start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
            vel = int(n[3]) if len(n) > 3 else 95
            # transpose down 12 semitones, then clamp to bass-ish range
            p2 = pitch - 12
            p2 = max(36, min(60, p2))
            out.append([start, p2, dur, vel])

        # Keep only the lowest note per start time "bucket" (monophonic-ish).
        by_time = {}
        for n in out:
            t = round(float(n[0]) / 0.25) * 0.25
            by_time.setdefault(t, []).append(n)
        mono = []
        for t in sorted(by_time.keys()):
            lowest = sorted(by_time[t], key=lambda x: x[1])[0]
            mono.append(lowest)
        mono.sort(key=lambda x: (float(x[0]), int(x[1])))
        return mono

    if role == "Counter":
        # Higher + sparser.
        lifted = []
        for n in notes_sorted:
            start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
            vel = int(n[3]) if len(n) > 3 else 85
            p2 = pitch + 12
            p2 = max(60, min(96, p2))
            vel = int(max(1, min(127, vel - 8)))
            lifted.append([start, p2, dur, vel])

        # Thin per bar so it doesn't fight the lead.
        per_bar = 7
        out = []
        by_bar = {}
        for n in lifted:
            bar = int(float(n[0]) // 4.0)
            if 0 <= bar < bars:
                by_bar.setdefault(bar, []).append(n)
        for b in range(bars):
            out.extend(by_bar.get(b, [])[:per_bar])
        out.sort(key=lambda x: (float(x[0]), int(x[1])))
        return out

    return notes


def _apply_quantize(notes, quantize_grid: str, bars: int):
    """
    DAW-friendly quantize: snap note starts + durations to a grid.
    This helps FL/DAW alignment when swing/micro-jitter is present.
    """
    if not notes:
        return notes

    q = str(quantize_grid or "Off")
    if q == "Off":
        return notes

    grid = 0.5 if q == "1/8" else 0.25  # beats
    max_t = float(int(bars) * 4)
    out = []
    for n in notes:
        if len(n) < 3:
            continue
        start, pitch, dur = float(n[0]), int(n[1]), float(n[2])
        vel = int(n[3]) if len(n) > 3 else 90
        start_q = round(round(start / grid) * grid, 4)
        dur_q = round(round(dur / grid) * grid, 4)
        dur_q = max(grid, dur_q)
        if start_q >= max_t:
            start_q = max(0.0, max_t - grid)
        if start_q + dur_q > max_t:
            dur_q = max(grid, max_t - start_q)
        out.append([start_q, pitch, dur_q, vel])
    out.sort(key=lambda x: (float(x[0]), int(x[1])))
    return out


def _make_monophonic_legato(notes, bars: int):
    """
    For sax solo we want a single note at a time and (optionally) no silence between notes.
    We keep at most one note per start time (stronger velocity wins), then stretch each note
    to the start of the next one (legato), clamped to the bar range.
    """
    if not notes:
        return notes
    max_t = float(int(bars) * 4)
    # Keep only one note per start time.
    by_t = {}
    for n in notes:
        if not isinstance(n, (list, tuple)) or len(n) < 3:
            continue
        try:
            t = float(n[0])
            p = int(n[1])
            d = float(n[2])
            v = int(n[3]) if len(n) > 3 else 90
        except Exception:
            continue
        if d <= 0:
            continue
        if t < 0 or t >= max_t:
            continue
        cur = by_t.get(t)
        if cur is None or v > int(cur[3]):
            by_t[t] = [t, p, d, v]
    mono = [by_t[t] for t in sorted(by_t.keys())]
    if not mono:
        return []

    # Stretch durations to the next start time (no gaps).
    for i in range(len(mono) - 1):
        t = float(mono[i][0])
        t_next = float(mono[i + 1][0])
        dur = max(0.01, t_next - t)  # tiny epsilon minimum
        if t + dur > max_t:
            dur = max(0.01, max_t - t)
        mono[i][2] = float(round(dur, 4))

    # Last note: keep within range.
    last = mono[-1]
    t_last = float(last[0])
    d_last = float(last[2])
    if t_last + d_last > max_t:
        last[2] = float(round(max(0.01, max_t - t_last), 4))
        mono[-1] = last

    return mono


def _is_disabled_pick(value: str) -> bool:
    v = str(value or "").strip().lower()
    return (not v) or ("vypnuto" in v) or (v == "freestyle")


def _split_theme_string(theme_string: str):
    s = str(theme_string or "").strip()
    if "|" in s:
        left, right = [p.strip() for p in s.split("|", 1)]
        return left, right
    return "", s


def _resolve_generation_controls(selected_producer, theme_string):
    producer_raw = str(selected_producer or "")
    _, theme_from_string = _split_theme_string(theme_string)
    theme_raw = str(st.session_state.get("selected_theme") or theme_from_string or "")
    density = str(st.session_state.get("note_density") or "Normál")

    producer_active = not _is_disabled_pick(producer_raw)
    theme_active = not _is_disabled_pick(theme_raw)
    solo_active = _is_any_solo_mode()

    effective_theme = theme_raw if theme_active else "Freestyle"
    effective_producer = producer_raw if producer_active else ""
    effective_theme_string = f"{effective_producer} | {effective_theme}" if effective_producer else effective_theme

    density_energy_map = {"Méně not": 4, "Normál": 6, "Více not": 8}
    density_energy = int(density_energy_map.get(density, 6))
    producer_energy = int(logic.get_producer_energy(effective_producer)) if producer_active else density_energy
    if solo_active:
        energy = int(round((0.65 * density_energy) + (0.35 * producer_energy)))
    elif producer_active:
        energy = int(round((0.30 * density_energy) + (0.70 * producer_energy)))
    else:
        energy = int(density_energy)
    energy = max(1, min(10, energy))

    boombap_var = st.session_state.get("boombap_variation")
    if boombap_var is not None:
        try:
            boombap_var = int(boombap_var)
        except Exception:
            boombap_var = None
    if boombap_var is not None:
        if solo_active:
            boombap_var = min(30, boombap_var)
        elif (not producer_active) and theme_active:
            boombap_var = min(35, boombap_var)
        elif not producer_active and not theme_active:
            boombap_var = min(25, boombap_var)

    return effective_producer, effective_theme_string, energy, boombap_var


def _generate_notes(
    selected_producer,
    theme_string,
    bars,
    ai_prompt,
    chords_mode,
    *,
    sax_character=None,
    sax_story=None,
    piano_character=None,
    piano_story=None,
    trumpet_character=None,
    trumpet_story=None,
    flute_character=None,
    flute_story=None,
    rhodes_character=None,
    rhodes_story=None,
    marimba_character=None,
    marimba_story=None,
    vibraphone_character=None,
    vibraphone_story=None,
    acoustic_bass_character=None,
    acoustic_bass_story=None,
    solo_motif_source=None,
):
    selected_producer, theme_string, energy, boombap_var = _resolve_generation_controls(selected_producer, theme_string)
    bars = int(bars)
    # Solo modes are local-only (even if AI mode is enabled).
    if _is_any_solo_mode():
        bars = _bars_for_current_mode(bars)

    if (not _is_any_solo_mode()) and st.session_state.ai_active and st.session_state.openai_key:
        result = logic.call_chatgpt_ai(
            st.session_state.openai_key,
            ai_prompt or "",
            bars,
            chords_mode,
            theme_string,
            energy=energy,
        role="Chords" if chords_mode else str(st.session_state.note_role),
            creativity=int(st.session_state.ai_creativity),
            counter_style=str(st.session_state.ai_counter_style),
        )
        # Post-process only for AI output; local generator remains unchanged.
        if not chords_mode:
            result = _apply_ai_density(result or [], str(st.session_state.note_density), bars)
            result = _apply_groove_creativity(result or [], int(st.session_state.ai_creativity))
            result = _apply_role_postprocess(result or [], str(st.session_state.note_role), bars)
            result = _apply_quantize(result or [], str(st.session_state.quantize_grid), bars)
        return result

    # Local generator
    if chords_mode:
        return _apply_chord_voicing(
            logic.chord_generate(bars, theme_string, energy),
            str(st.session_state.get("chord_voicing_mode") or "Tight"),
        )

    local = logic.smart_generate(
        bars,
        theme_string,
        energy,
        style=st.session_state.get("local_melody_style"),
        boombap_variation=boombap_var,
        sax_character=sax_character,
        sax_story=sax_story,
        piano_character=piano_character,
        piano_story=piano_story,
        trumpet_character=trumpet_character,
        trumpet_story=trumpet_story,
        flute_character=flute_character,
        flute_story=flute_story,
        rhodes_character=rhodes_character,
        rhodes_story=rhodes_story,
        marimba_character=marimba_character,
        marimba_story=marimba_story,
        vibraphone_character=vibraphone_character,
        vibraphone_story=vibraphone_story,
        acoustic_bass_character=acoustic_bass_character,
        acoustic_bass_story=acoustic_bass_story,
        solo_motif_source=solo_motif_source,
    )
    # Density behavior differs per mode:
    # - Melodic: keep it controlled (user wants "Více not" ~= previous sparse benchmark)
    # - Others: keep existing behavior (including "Více not" articulation splits)
    if str(st.session_state.get("gen_mode") or "") == "Melodic":
        local = _apply_melodic_density_limit(local or [], str(st.session_state.note_density), bars)
    else:
        local = _apply_local_density(local or [], str(st.session_state.note_density), bars)
    # In Melodic mode, keep durations consistent (ties to Hustota not).
    if str(st.session_state.get("gen_mode") or "") == "Melodic":
        local = _apply_melodic_duration_balance(local or [], str(st.session_state.note_density), bars)
    local = _apply_role_postprocess(local or [], str(st.session_state.note_role), bars)
    local = _apply_quantize(local or [], str(st.session_state.quantize_grid), bars)
    if _is_any_solo_mode():
        local = _make_monophonic_legato(local or [], bars)
    return local


def render_import_page(selected_producer, selected_theme):
    render_tutorial_modal()
    st.title("IMPORT BEATU")
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

    st.checkbox("Použít Auto BPM", key="import_use_auto_bpm")
    st.number_input("BPM:", min_value=40, max_value=220, value=int(st.session_state.import_bpm_manual), key="import_bpm_manual")

    bpm_used = bpm_est if (st.session_state.import_use_auto_bpm and bpm_est) else float(st.session_state.import_bpm_manual)
    bpm_used = float(max(40, min(220, bpm_used)))
    st.number_input("Délka (taktů):", min_value=1, max_value=16, value=int(st.session_state.import_bars), key="import_bars")

    theme_string = get_theme_string(selected_producer, selected_theme)
    st.markdown(f"**Mood:** `{theme_string}`")

    if st.session_state.engine_type == ENGINE_STUDIO:
        from app.config import DISPLAY_STUDIO_INSTRUMENTS

        opts = list(DISPLAY_STUDIO_INSTRUMENTS)
        cur = str(st.session_state.import_main_instrument or opts[0])
        idx = opts.index(cur) if cur in opts else 0
        st.selectbox("Nástroj (hlavní):", opts, index=idx, key="import_main_instrument")
    else:
        opts = list(LAB_WAVES.keys())
        cur = str(st.session_state.import_main_instrument or opts[0])
        idx = opts.index(cur) if cur in opts else 0
        st.selectbox("Vlna (hlavní):", opts, index=idx, key="import_main_instrument")

    if st.button("🚀 GENEROVAT MELODIE K BEATU", use_container_width=True):
        # Sidebar BPM is a widget key; update via pending to avoid Streamlit API exceptions.
        st.session_state["bpm_pending"] = int(round(bpm_used))

        chords_mode = st.session_state.ai_chords
        prev = list(st.session_state.projects or [])
        projects = []
        total = int(st.session_state.num_variants)
        msg_ph = st.empty()
        bar_ph = st.empty()

        for i in range(total):
            msg_ph.markdown(f"**Sekám sample…** `{i + 1}/{total}`")
            bar_ph.progress(int((i / max(1, total)) * 100))
            if i < len(prev) and prev[i].get("locked"):
                projects.append(prev[i])
                continue
            result = _generate_notes(selected_producer, theme_string, int(st.session_state.import_bars), "", chords_mode)
            proj = create_project(
                f"IMPORT_{theme_string}_{i + 1}",
                theme_string,
                result,
                instrument_name=st.session_state.import_main_instrument,
                source="import",
                bars=int(st.session_state.import_bars),
                locked=False,
                humanize=str(st.session_state.preset_humanize or "Off"),
                note_density=str(st.session_state.note_density),
                note_role=str(st.session_state.note_role),
                melody_style=None
                if (st.session_state.ai_active and st.session_state.openai_key) or chords_mode
                else str(st.session_state.get("local_melody_style")),
                boombap_variation=int(st.session_state.get("boombap_variation") or 0)
                if (not ((st.session_state.ai_active and st.session_state.openai_key) or chords_mode))
                else None,
                app_version=APP_VERSION,
            )
            projects.append(proj)

        bar_ph.progress(100)
        msg_ph.markdown("**Sekám sample…** `hotovo`")

        old_n = len(st.session_state.projects) if st.session_state.projects else 0
        reset_project_widget_state(max(old_n, len(projects)))
        st.session_state.projects = projects
        st.toast("Hotovo. Návrhy jsou dole.")
        bar_ph.empty()
        msg_ph.empty()

    if st.session_state.projects:
        st.subheader("Výsledky")
        for idx, project in enumerate(st.session_state.projects):
            render_melody_card(project, idx)


def generate_projects(selected_producer, final_theme_string, ai_prompt, chords_mode, progress_ui=None):
    prev = list(st.session_state.projects or [])
    projects = []

    total = int(st.session_state.num_variants)
    bar_ph = None
    msg_ph = None
    if progress_ui:
        bar_ph, msg_ph = progress_ui

    bars_for_mode = _bars_for_current_mode(int(st.session_state.num_bars))

    # Solo modes: auto "dice" for each proposal + optional variations around a locked base.
    solo_rolls = None
    locked_base = None
    if _is_any_solo_mode():
        forced_char, forced_story = _solo_vibe_from_text(str(st.session_state.get("solo_prompt") or ""))
        # Find the first locked proposal as the anchor.
        for p in prev:
            if isinstance(p, dict) and p.get("locked"):
                locked_base = p
                break
        # If there is a locked base, keep the same vibe for all new variants.
        # Otherwise roll diverse combos for this batch.
        if locked_base and isinstance(locked_base, dict):
            base_char = str(locked_base.get("solo_character") or "Klidné")
            base_story = bool(locked_base.get("solo_story")) if locked_base.get("solo_story") is not None else False
            if forced_char is not None:
                base_char = str(forced_char)
            if forced_story is not None:
                base_story = bool(forced_story)
            solo_rolls = [(base_char, base_story) for _ in range(total)]
        else:
            # Seed with theme + total to get stable but varied rolls between reruns.
            seed = abs(hash(f"{final_theme_string}:{total}:{bars_for_mode}")) % (2**31)
            solo_rolls = _roll_solo_variants(total, seed=seed)
            # Apply forced vibe on top of dice, if requested.
            if forced_char is not None or forced_story is not None:
                patched = []
                for c, s in solo_rolls:
                    patched.append((str(forced_char) if forced_char is not None else c, bool(forced_story) if forced_story is not None else s))
                solo_rolls = patched

    dataset_mode = str(st.session_state.get("generation_engine") or "") == "Dataset Style"
    for index in range(total):
        if msg_ph is not None:
            msg_ph.markdown(f"**Sekám sample…** `{index + 1}/{total}`")
        if bar_ph is not None:
            bar_ph.progress(int((index / max(1, total)) * 100))

        if index < len(prev) and prev[index].get("locked"):
            projects.append(prev[index])
            continue

        layers_for_project = []
        if dataset_mode:
            ds = _generate_from_dataset(int(bars_for_mode))
            result = ds.get("melody", []) if isinstance(ds, dict) else []
            layers_for_project = list(ds.get("layers", []) or []) if isinstance(ds, dict) else []
        elif _is_any_solo_mode():
            char, story = solo_rolls[index] if solo_rolls else ("Klidné", False)
            motif_source = None
            if locked_base and isinstance(locked_base, dict):
                motif_source = locked_base.get("melody") or []
            result = _generate_notes(
                selected_producer,
                final_theme_string,
                bars_for_mode,
                ai_prompt="",
                chords_mode=False,
                sax_character=char if _is_sax_solo_mode() else None,
                sax_story=story if _is_sax_solo_mode() else None,
                piano_character=char if _is_piano_solo_mode() else None,
                piano_story=story if _is_piano_solo_mode() else None,
                rhodes_character=char if _is_rhodes_solo_mode() else None,
                rhodes_story=story if _is_rhodes_solo_mode() else None,
                trumpet_character=char if _is_trumpet_solo_mode() else None,
                trumpet_story=story if _is_trumpet_solo_mode() else None,
                flute_character=char if _is_flute_solo_mode() else None,
                flute_story=story if _is_flute_solo_mode() else None,
                marimba_character=char if _is_marimba_solo_mode() else None,
                marimba_story=story if _is_marimba_solo_mode() else None,
                vibraphone_character=char if _is_vibraphone_solo_mode() else None,
                vibraphone_story=story if _is_vibraphone_solo_mode() else None,
                acoustic_bass_character=char if _is_akustik_bass_mode() else None,
                acoustic_bass_story=story if _is_akustik_bass_mode() else None,
                solo_motif_source=motif_source,
            )
        else:
            result = _generate_notes(selected_producer, final_theme_string, bars_for_mode, ai_prompt, chords_mode)
        if (not result) and (not dataset_mode):
            if _is_any_solo_mode():
                result = _generate_notes(
                    selected_producer,
                    final_theme_string,
                    bars_for_mode,
                    ai_prompt="",
                    chords_mode=False,
                    sax_character=char if _is_sax_solo_mode() else None,
                    sax_story=story if _is_sax_solo_mode() else None,
                    piano_character=char if _is_piano_solo_mode() else None,
                    piano_story=story if _is_piano_solo_mode() else None,
                    rhodes_character=char if _is_rhodes_solo_mode() else None,
                    rhodes_story=story if _is_rhodes_solo_mode() else None,
                    trumpet_character=char if _is_trumpet_solo_mode() else None,
                    trumpet_story=story if _is_trumpet_solo_mode() else None,
                    flute_character=char if _is_flute_solo_mode() else None,
                    flute_story=story if _is_flute_solo_mode() else None,
                    marimba_character=char if _is_marimba_solo_mode() else None,
                    marimba_story=story if _is_marimba_solo_mode() else None,
                    vibraphone_character=char if _is_vibraphone_solo_mode() else None,
                    vibraphone_story=story if _is_vibraphone_solo_mode() else None,
                    acoustic_bass_character=char if _is_akustik_bass_mode() else None,
                    acoustic_bass_story=story if _is_akustik_bass_mode() else None,
                    solo_motif_source=motif_source,
                )
            else:
                result = _generate_notes(selected_producer, final_theme_string, bars_for_mode, ai_prompt, chords_mode)

        instr = None
        if st.session_state.engine_type == ENGINE_STUDIO:
            if _is_sax_solo_mode():
                instr = "Alto Sax"
            if _is_piano_solo_mode():
                instr = "Acoustic Grand Piano"
            if _is_rhodes_solo_mode():
                instr = "Rhodes Piano"
            if _is_trumpet_solo_mode():
                instr = "Trumpet"
            if _is_flute_solo_mode():
                instr = "Flute"
            if _is_marimba_solo_mode():
                instr = "Marimba"
            if _is_vibraphone_solo_mode():
                instr = "Vibraphone"
            if _is_akustik_bass_mode():
                instr = "Acoustic Bass"
            # Apply preset instrument only for non-solo modes; solos have a fixed instrument.
            if not _is_any_solo_mode():
                try:
                    from app.config import DISPLAY_STUDIO_INSTRUMENTS

                    if st.session_state.preset_instrument in DISPLAY_STUDIO_INSTRUMENTS:
                        instr = st.session_state.preset_instrument
                except Exception:
                    instr = None

        projects.append(
            create_project(
                _build_generated_title(selected_producer, final_theme_string, index),
                final_theme_string,
                result,
                instrument_name=instr,
                bars=int(bars_for_mode),
                layers=layers_for_project,
                locked=False,
                humanize=str(st.session_state.preset_humanize or "Off"),
                note_density=str(st.session_state.note_density),
                note_role=str(st.session_state.note_role),
                melody_style=(
                    "Dataset Style"
                    if dataset_mode
                    else (
                        None
                        if (st.session_state.ai_active and st.session_state.openai_key) or chords_mode
                        else str(st.session_state.get("local_melody_style"))
                    )
                ),
                boombap_variation=int(st.session_state.get("boombap_variation") or 0)
                if (not ((st.session_state.ai_active and st.session_state.openai_key) or chords_mode))
                else None,
                app_version=APP_VERSION,
            )
        )
        # Store rolled solo vibe so "lock" can spawn variations around it.
        if _is_any_solo_mode() and projects:
            try:
                projects[-1]["solo_character"] = str(char)
                projects[-1]["solo_story"] = bool(story)
            except Exception:
                pass

    if bar_ph is not None:
        bar_ph.progress(100)
    if msg_ph is not None:
        msg_ph.markdown("**Sekám sample…** `hotovo`")

    old_n = len(st.session_state.projects) if st.session_state.projects else 0
    reset_project_widget_state(max(old_n, len(projects)))
    st.session_state.projects = projects

    if bar_ph is not None:
        bar_ph.empty()
    if msg_ph is not None:
        msg_ph.empty()


def render_generation_form(final_theme_string: str):
    trigger_generate = False
    ai_prompt = ""

    gen_mode_now = str(st.session_state.get("gen_mode") or "")
    # Unified topbar for all generation modes.
    _render_topbar_controls()
    with st.form("gen_form", border=False):
        # Make the center area wide so the one-line status text can fit without wrapping.
        col_center = st.columns([0.25, 3.5, 0.25])[1]
        with col_center:
            gen_mode = str(st.session_state.get("gen_mode") or "")
            solo_label = _infer_active_solo_label()
            mood = str(final_theme_string or st.session_state.get("current_theme_string") or "")
            variants = int(st.session_state.get("num_variants") or 1)
            bars = _bars_for_current_mode(int(st.session_state.get("num_bars") or 4))
            dens_internal = str(st.session_state.get("note_density") or "Normál")
            dens_ui = _DENSITY_INTERNAL_TO_UI.get(dens_internal, dens_internal)
            left_span = f"<span>Solo: <code>{solo_label}</code></span><span class='sep'>•</span>" if gen_mode == "Sola" else ""
            # Centered status line above the main Generate button (keeps the same "caption" feel).
            st.markdown(
                "<div class='gen-statusline'>"
                f"{left_span}"
                f"<span>Mood: <code>{mood}</code></span>"
                f"<span class='sep'>•</span><span>Počet: <code>{variants}</code></span>"
                f"<span class='sep'>•</span><span>Taktů: <code>{bars}</code></span>"
                f"<span class='sep'>•</span><span>BPM: <code>{int(st.session_state.bpm)}</code></span>"
                f"<span class='sep'>•</span><span>Role: <code>{st.session_state.note_role}</code></span>"
                f"<span class='sep'>•</span><span>Hustota: <code>{dens_ui}</code></span>"
                f"<span class='sep'>•</span><span>Quantize: <code>{st.session_state.quantize_grid}</code></span>"
                f"<span class='sep'>•</span><span>Humanize: <code>{st.session_state.preset_humanize}</code></span>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.session_state.ai_active and gen_mode != "Sola":
                st.text_input("Vize", placeholder="Popiš svůj beat...", label_visibility="collapsed", key="ai_prompt")
                ai_prompt = str(st.session_state.ai_prompt or "")
                st.session_state.last_ai_prompt = ai_prompt
            trigger_generate = st.form_submit_button("🚀 GENEROVAT", use_container_width=True)

    return trigger_generate, ai_prompt


def open_project_from_archive(project):
    st.session_state.projects = [project]
    reset_project_widget_state(1)
    # Restore the "creative controls" used when the project was made.
    if project.get("note_density"):
        st.session_state["note_density_pending"] = project.get("note_density")
    if project.get("note_role"):
        st.session_state["note_role_pending"] = project.get("note_role")
    if project.get("humanize"):
        st.session_state["preset_humanize_pending"] = project.get("humanize")
    if project.get("melody_style"):
        st.session_state["local_melody_style_pending"] = project.get("melody_style")
    if project.get("boombap_variation") is not None:
        vv = int(project.get("boombap_variation"))
        st.session_state["boombap_variation_pending"] = vv
        if vv <= 35:
            st.session_state["boombap_variation_level_pending"] = "Málo"
        elif vv <= 70:
            st.session_state["boombap_variation_level_pending"] = "Středně"
        else:
            st.session_state["boombap_variation_level_pending"] = "Popiči moc"
    st.session_state.page_pending = PAGE_GENERATOR
    st.rerun()


def render_generator_page(selected_producer, final_theme_string):
    render_tutorial_modal()
    # Apply preset to currently visible projects so the user feels the click immediately.
    pending = st.session_state.pop("apply_preset_projects_pending", None)
    if pending and st.session_state.projects:
        try:
            from app.config import DISPLAY_STUDIO_INSTRUMENTS

            for i, p in enumerate(list(st.session_state.projects)):
                if not isinstance(p, dict):
                    continue
                if p.get("locked"):
                    continue
                p["humanize"] = str(pending.get("humanize") or p.get("humanize") or "Off")
                p["note_density"] = str(pending.get("note_density") or p.get("note_density") or st.session_state.note_density)
                p["note_role"] = str(pending.get("note_role") or p.get("note_role") or st.session_state.note_role)
                if st.session_state.engine_type == ENGINE_STUDIO and pending.get("instrument") in DISPLAY_STUDIO_INSTRUMENTS:
                    p["main_instrument"] = pending.get("instrument")
                st.session_state.projects[i] = p
        except Exception:
            pass

    trigger_generate, ai_prompt = render_generation_form(final_theme_string)

    if trigger_generate:
        msg_ph = st.empty()
        bar_ph = st.empty()
        generate_projects(
            selected_producer,
            final_theme_string,
            ai_prompt,
            st.session_state.ai_chords,
            progress_ui=(bar_ph, msg_ph),
        )

    regen_idx = st.session_state.pop("regen_one_index", None)
    variation_idx = st.session_state.pop("variation_one_index", None)
    regen_unlocked_skip = st.session_state.pop("regen_unlocked_skip", None)
    if regen_idx is not None and st.session_state.projects:
        idx = int(regen_idx)
        dataset_mode = str(st.session_state.get("generation_engine") or "") == "Dataset Style"
        if 0 <= idx < len(st.session_state.projects):
            project = st.session_state.projects[idx]
            if not project.get("locked"):
                bars = int(project.get("bars") or st.session_state.num_bars)
                # Use current selection (stored by main) if available.
                theme_str = str(st.session_state.get("current_theme_string") or project.get("theme") or final_theme_string)
                prod = str(st.session_state.get("current_selected_producer") or selected_producer)
                prompt = str(st.session_state.get("last_ai_prompt") or "")
                if dataset_mode:
                    ds = _generate_from_dataset(int(bars))
                    project["melody"] = ds.get("melody", []) or project.get("melody", [])
                    project["layers"] = list(ds.get("layers", []) or [])
                else:
                    project["melody"] = _generate_notes(prod, theme_str, bars, prompt, st.session_state.ai_chords) or project["melody"]
                project["theme"] = theme_str
                project["title"] = _build_generated_title(prod, theme_str, idx)
                st.session_state.projects[idx] = project
                st.toast(f"Regenerováno: návrh č. {idx + 1}")
                st.rerun()

    if variation_idx is not None and st.session_state.projects:
        idx = int(variation_idx)
        if 0 <= idx < len(st.session_state.projects):
            project = st.session_state.projects[idx]
            if not project.get("locked"):
                bars = int(project.get("bars") or st.session_state.num_bars)
                project["melody"] = _smart_variation(project.get("melody", []) or [], bars) or project.get("melody", [])
                if project.get("layers"):
                    new_layers = []
                    for ly in list(project.get("layers") or []):
                        lm = _smart_variation(ly.get("melody", []) or [], bars)
                        ly2 = dict(ly)
                        ly2["melody"] = lm or ly.get("melody", [])
                        new_layers.append(ly2)
                    project["layers"] = new_layers
                st.session_state.projects[idx] = project
                st.toast(f"Variace: návrh č. {idx + 1}")
                st.rerun()

    if regen_unlocked_skip is not None and st.session_state.projects:
        dataset_mode = str(st.session_state.get("generation_engine") or "") == "Dataset Style"
        # Regenerate all unlocked proposals (used when user clicks Regen on a locked proposal).
        try:
            skip = int(regen_unlocked_skip)
        except Exception:
            skip = -1

        theme_str = str(st.session_state.get("current_theme_string") or final_theme_string)
        prod = str(st.session_state.get("current_selected_producer") or selected_producer)
        prompt = str(st.session_state.get("last_ai_prompt") or "")

        changed = 0
        for i in range(len(st.session_state.projects)):
            if i == skip:
                continue
            p = st.session_state.projects[i]
            if not isinstance(p, dict) or p.get("locked"):
                continue
            bars = int(p.get("bars") or st.session_state.num_bars)
            if dataset_mode:
                ds = _generate_from_dataset(int(bars))
                p["melody"] = ds.get("melody", []) or p.get("melody")
                p["layers"] = list(ds.get("layers", []) or [])
            else:
                p["melody"] = _generate_notes(prod, theme_str, bars, prompt, st.session_state.ai_chords) or p.get("melody")
            p["theme"] = theme_str
            p["title"] = _build_generated_title(prod, theme_str, i)
            st.session_state.projects[i] = p
            changed += 1

        if changed:
            st.toast(f"Regenerováno: {changed}× (nezamčené návrhy)")
        else:
            st.toast("Nic k regeneraci (všechno je zamčené).")
        st.rerun()

    for index, project in enumerate(st.session_state.projects):
        render_melody_card(project, index)


def render_archive_page():
    render_tutorial_modal()

    # Row 1: full-width header
    h1, h2 = st.columns([1.5, 1], gap="small")
    with h1:
        st.title("📚 Archiv 2.0")
    with h2:
        if hasattr(st, "popover"):
            with st.popover("Import MIDI ▾", use_container_width=True):
                uploaded_midi = st.file_uploader("Nahraj MIDI", type=["mid", "midi"], key="arch2_import_midi")
                if uploaded_midi is not None:
                    melody, bpm_guess, instr_guess = sound.import_midi_bytes(uploaded_midi.getvalue())
                    if not melody:
                        st.warning("MIDI se nepodařilo načíst.")
                    else:
                        default_title = uploaded_midi.name.rsplit(".", 1)[0]
                        imp_title = st.text_input("Název", value=default_title, key="arch2_import_title")
                        imp_theme = st.text_input("Téma", value="Imported Reference", key="arch2_import_theme")
                        imp_rating_key = "arch2_import_rating"
                        if imp_rating_key not in st.session_state:
                            st.session_state[imp_rating_key] = 5
                        current_import_rating = int(st.session_state.get(imp_rating_key) or 5)
                        current_import_rating = max(1, min(5, current_import_rating))
                        import_stars_label = "⭐" * current_import_rating
                        with st.popover(f"{import_stars_label} ▾", use_container_width=True):
                            imp_rating = st.radio(
                                "Hodnocení",
                                [1, 2, 3, 4, 5],
                                index=current_import_rating - 1,
                                key=f"{imp_rating_key}_pick",
                                label_visibility="collapsed",
                                format_func=lambda x: "⭐" * int(x),
                            )
                            st.session_state[imp_rating_key] = int(imp_rating)
                        if st.button("Uložit do knihovny", key="arch2_import_save", use_container_width=True):
                            payload = create_project(
                                str(imp_title or default_title),
                                str(imp_theme or "Imported Reference"),
                                melody,
                                instrument_name=str(instr_guess or "Acoustic Grand Piano"),
                                source="imported",
                                bars=max(1, int(round((max([n[0] + n[2] for n in melody]) if melody else 4) / 4.0))),
                                locked=False,
                                humanize="Off",
                                note_density=str(st.session_state.get("note_density") or "Normál"),
                                note_role=str(st.session_state.get("note_role") or "Lead"),
                                melody_style=str(st.session_state.get("local_melody_style") or "Boombap Loop"),
                                boombap_variation=int(st.session_state.get("boombap_variation") or 0),
                                app_version=APP_VERSION,
                            )
                            db.save_to_db(
                                str(imp_title or default_title),
                                str(imp_theme or "Imported Reference"),
                                str(instr_guess or "Acoustic Grand Piano"),
                                payload,
                                int(bpm_guess or 90),
                                int(st.session_state.get(imp_rating_key) or 0),
                                tags="",
                                source_type="imported",
                            )
                            st.toast("MIDI import uložen do Archivu 2.0.")
                            st.rerun()
        else:
            st.caption("Import MIDI není dostupný v tomto režimu UI.")

    df = db.get_all_melodies()
    if df.empty:
        st.info("Archiv 2.0 je zatím prázdný.")
        return

    if "source_type" not in df.columns:
        df["source_type"] = "generated"
    if "rating" not in df.columns:
        df["rating"] = 0

    def _split_atmo(atmo: str):
        atmo = str(atmo or "")
        if "|" in atmo:
            p, t = atmo.split("|", 1)
            return p.strip(), t.strip()
        return "", atmo.strip()

    def _is_solo_row(payload):
        try:
            style = str(payload.get("melody_style") or "").strip().lower()
            return style.startswith(("sax", "piano", "rhodes", "trumpet", "flute", "marimba", "vib", "akust"))
        except Exception:
            return False

    df["producer"] = df["atmosfera"].apply(lambda x: _split_atmo(x)[0])
    df["theme"] = df["atmosfera"].apply(lambda x: _split_atmo(x)[1])
    df["solo"] = df["noty_json"].apply(lambda s: "Solo" if _is_solo_row(db.json.loads(s)) else "Ne")
    def _norm_source(row):
        src = str(row.get("source_type") or "generated").strip().lower()
        if src == "imported":
            return "imported"
        if src == "dataset":
            return "dataset"
        try:
            payload = db.json.loads(row.get("noty_json") or "{}")
            if str(payload.get("melody_style") or "").strip().lower() == "dataset style":
                return "dataset"
        except Exception:
            pass
        return "generated"
    df["source_type_norm"] = df.apply(_norm_source, axis=1)
    source_label_map = {"generated": "generated", "imported": "imported", "dataset": "dataset"}

    # Row 2: full-width search + popover filters in one row
    r = st.columns([2.2, 1.2, 1, 1, 1, 1, 1], gap="small")
    q = ""
    sort_sel = "Nejnovější"
    producer_sel = "(Všichni)"
    theme_sel = "(Všechna)"
    solo_sel = "(Vše)"
    source_sel = "(Vše)"
    dataset_only_sel = "Ne"

    with r[0]:
        q = st.text_input("Hledat", placeholder="Název projektu...", label_visibility="collapsed", key="arch2_q")
    with r[1]:
        with st.popover("Řadit ▾", use_container_width=True):
            sort_sel = st.radio(
                "Řazení",
                ["Nejnovější", "Nejstarší", "Hodnocení nejlepší", "Hodnocení nejhorší"],
                key="arch2_sort",
                label_visibility="collapsed",
            )
    with r[2]:
        producer_opts = ["(Všichni)"] + sorted([p for p in df["producer"].unique().tolist() if p])
        with st.popover("Producent ▾", use_container_width=True):
            producer_sel = st.radio("Producent", producer_opts, key="arch2_producer", label_visibility="collapsed")
    with r[3]:
        theme_opts = ["(Všechna)"] + sorted([t for t in df["theme"].unique().tolist() if t])
        with st.popover("Téma ▾", use_container_width=True):
            theme_sel = st.radio("Téma", theme_opts, key="arch2_theme", label_visibility="collapsed")
    with r[4]:
        with st.popover("Solo ▾", use_container_width=True):
            solo_sel = st.radio("Solo filtr", ["(Vše)", "Solo", "Ne"], key="arch2_solo", label_visibility="collapsed")
    with r[5]:
        with st.popover("Zdroj ▾", use_container_width=True):
            source_sel = st.radio("Zdroj filtr", ["(Vše)", "Vygenerované", "Importované", "Dataset"], key="arch2_source", label_visibility="collapsed")
    with r[6]:
        with st.popover("Dataset ▾", use_container_width=True):
            dataset_only_sel = st.radio("Jen dataset návrhy", ["Ne", "Ano"], key="arch2_dataset_only", label_visibility="collapsed")

    f = df.copy()
    if producer_sel != "(Všichni)":
        f = f[f["producer"] == producer_sel]
    if theme_sel != "(Všechna)":
        f = f[f["theme"] == theme_sel]
    if solo_sel != "(Vše)":
        f = f[f["solo"] == solo_sel]
    if source_sel == "Vygenerované":
        f = f[f["source_type_norm"] == "generated"]
    elif source_sel == "Importované":
        f = f[f["source_type_norm"] == "imported"]
    elif source_sel == "Dataset":
        f = f[f["source_type_norm"] == "dataset"]
    if dataset_only_sel == "Ano":
        f = f[f["source_type_norm"] == "dataset"]
    if q:
        qn = q.strip().lower()
        f = f[f["jmeno"].astype(str).str.lower().str.contains(qn, na=False)]

    if sort_sel == "Nejstarší":
        f = f.sort_values(by=["datum"], ascending=True)
    elif sort_sel == "Hodnocení nejlepší":
        f = f.sort_values(by=["rating", "datum"], ascending=[False, False])
    elif sort_sel == "Hodnocení nejhorší":
        f = f.sort_values(by=["rating", "datum"], ascending=[True, False])
    else:
        f = f.sort_values(by=["datum"], ascending=False)

    st.caption(f"Nalezeno: {len(f)} / {len(df)}")

    # Projects area: a bit wider than half, aligned left
    proj_col, _ = st.columns([1.25, 0.75], gap="small")
    with proj_col:
        detail_id = int(st.session_state.get("arch2_detail_id") or 0)
        for _, row in f.iterrows():
            rid = int(row["id"])
            payload = db.json.loads(row["noty_json"])
            project = normalize_project_payload(payload, row["jmeno"], row["atmosfera"], row["nastroj"])

            stars_now = int(row.get("rating") or 0)
            stars_now = max(1, min(5, stars_now))
            c = st.columns([0.7, 3.1, 1.1, 1.0, 2.2], gap="small")
            with c[0]:
                icon = "▾" if detail_id == rid else "▸"
                if st.button(icon, key=f"arch2_toggle_{rid}", use_container_width=True):
                    st.session_state["arch2_detail_id"] = 0 if detail_id == rid else rid
                    st.rerun()
            with c[1]:
                st.markdown(f"**{project['title']}**")
            with c[2]:
                st.caption(str(row.get("datum") or ""))
            with c[3]:
                st.caption(str(source_label_map.get(str(row.get("source_type_norm") or "generated"), "generated")))
            with c[4]:
                stars_label = "⭐" * stars_now
                with st.popover(f"{stars_label} ▾", use_container_width=True):
                    picked_rating = st.radio(
                        "",
                        [1, 2, 3, 4, 5],
                        index=max(0, min(4, stars_now - 1)),
                        key=f"arch2_row_rating_{rid}",
                        label_visibility="collapsed",
                        format_func=lambda x: "⭐" * int(x),
                    )
                    if int(picked_rating) != stars_now:
                        db.update_rating(rid, int(picked_rating))
                        st.toast("Hodnocení uloženo.")
                        st.rerun()

            if detail_id == rid:
                # Player full width of project column
                play_instr_opts = list(STUDIO_INSTRUMENTS.keys())
                current_main = str(project.get("main_instrument") or "Acoustic Grand Piano")
                if current_main not in play_instr_opts:
                    current_main = "Acoustic Grand Piano"
                instr_state_key = f"arch2_play_instr_{rid}"
                if instr_state_key not in st.session_state:
                    st.session_state[instr_state_key] = current_main
                play_instr = str(st.session_state.get(instr_state_key) or current_main)
                if play_instr not in play_instr_opts:
                    play_instr = "Acoustic Grand Piano"

                audio_parts = []
                main_id = int(STUDIO_INSTRUMENTS.get(play_instr, 0))
                audio_parts.append(
                    synthesise_full_audio_cached(
                        project.get("melody", []),
                        engine_type=ENGINE_STUDIO,
                        instrument_id=main_id,
                        octave_shift=0,
                        bpm=int(row.get("bpm") or 90),
                    )
                )
                for layer in project.get("layers", []):
                    lid = STUDIO_INSTRUMENTS.get(layer.get("instrument"), 0)
                    audio_parts.append(
                        synthesise_full_audio_cached(
                            layer.get("melody", []),
                            engine_type=ENGINE_STUDIO,
                            instrument_id=lid,
                            octave_shift=0,
                            bpm=int(row.get("bpm") or 90),
                        )
                    )
                st.audio(sound.mix_wav_audios(audio_parts), format="audio/wav")

                acts = st.columns([1.2, 1, 1, 0.9], gap="small")
                with acts[0]:
                    with st.popover(f"{play_instr} ▾", use_container_width=True):
                        picked_instr = st.radio(
                            "Nástroj",
                            play_instr_opts,
                            index=play_instr_opts.index(play_instr) if play_instr in play_instr_opts else 0,
                            key=instr_state_key,
                            label_visibility="collapsed",
                        )
                with acts[1]:
                    combined_notes = get_combined_notes(project)
                    st.download_button(
                        "🎹 MIDI",
                        sound.export_to_midi(combined_notes, int(row.get("bpm") or 90)),
                        f"{project['title']}.mid",
                        key=f"arch2_dl_{rid}",
                        use_container_width=True,
                    )
                with acts[2]:
                    open_project = dict(project)
                    open_project["main_instrument"] = play_instr
                    if st.button("Otevřít v editoru", key=f"arch2_open_{rid}", use_container_width=True):
                        open_project_from_archive(open_project)
                with acts[3]:
                    if st.button("Smazat", key=f"arch2_del_{rid}", use_container_width=True):
                        db.delete_from_db(rid)
                        st.session_state["arch2_detail_id"] = 0
                        st.toast("Projekt smazán.")
                        st.rerun()
                st.markdown("---")

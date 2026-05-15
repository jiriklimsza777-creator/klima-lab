# -*- coding: utf-8 -*-
"""Compatibility bridge module.

This module keeps the historical `Generator_not` API stable while delegating
runtime generation logic to `core.generator.*` modules.
"""

import random

from core.generator.ai_generate import call_chatgpt_ai as _call_chatgpt_ai_impl
from core.generator.chords import chord_generate as _chord_generate_impl
from core.generator.melody_generate import smart_generate as _smart_generate_impl
from core.generator.melody_local import smart_generate_classic as _smart_generate_classic_impl
from core.generator.solos import (
    generate_acoustic_bass_solo as _generate_acoustic_bass_solo_impl,
    generate_flute_solo as _generate_flute_solo_impl,
    generate_marimba_solo as _generate_marimba_solo_impl,
    generate_piano_solo as _generate_piano_solo_impl,
    generate_sax_solo as _generate_sax_solo_impl,
    generate_trumpet_solo as _generate_trumpet_solo_impl,
    generate_vibraphone_solo as _generate_vibraphone_solo_impl,
)
from core.generator.theme_profiles import (
    DEFAULT_PROFILE,
    build_theme_profile as _build_theme_profile,
    get_producer_profile as _get_producer_profile,
    split_theme as _split_theme,
)
from core.generator.utils import (
    build_allowed_notes as _build_allowed_notes,
    choose_next_pitch as _choose_next_pitch,
    choose_next_pitch_classic as _choose_next_pitch_classic,
    merge_unique as _merge_unique,
    solo_duration_pool as _solo_duration_pool,
    solo_theme_mods as _solo_theme_mods,
    weighted_choice as _weighted_choice,
)


def get_producer_energy(producer):
    mapping = {
        "Daringer": 3,
        "Apollo Brown": 4,
        "J Dilla": 5,
        "Madlib": 5,
        "Knxwledge": 5,
        "Nujabes": 5,
        "Pete Rock": 6,
        "9th Wonder": 6,
        "Q-Tip": 6,
        "Havoc": 6,
        "RZA": 6,
        "MF DOOM": 7,
        "Dr Dre": 7,
        "Kanye West": 7,
        "DJ Premier": 7,
        "The Alchemist": 6,
        "Just Blaze": 8,
        "Timbaland": 8,
        "Metro Boomin": 9,
    }
    return mapping.get(producer, random.randint(4, 7))


def smart_generate_classic(num_bars, theme="Freestyle", energy=5):
    return _smart_generate_classic_impl(num_bars, theme=theme, energy=energy)


def generate_sax_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_sax_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_piano_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_piano_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_trumpet_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_trumpet_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_flute_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_flute_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_marimba_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_marimba_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_vibraphone_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_vibraphone_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def generate_acoustic_bass_solo(theme="Freestyle", bars=8, energy=5, character=None, story=None, motif_source=None):
    return _generate_acoustic_bass_solo_impl(theme=theme, bars=bars, energy=energy, character=character, story=story, motif_source=motif_source)


def smart_generate(
    num_bars,
    theme="Freestyle",
    energy=5,
    style=None,
    boombap_variation=None,
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
    return _smart_generate_impl(
        num_bars,
        theme=theme,
        energy=energy,
        style=style,
        boombap_variation=boombap_variation,
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


def chord_generate(num_bars, theme="Freestyle", energy=5):
    return _chord_generate_impl(num_bars, theme=theme, energy=energy)


def call_chatgpt_ai(
    api_key,
    user_prompt,
    bars,
    chords_mode,
    theme_name,
    secret_rule="",
    energy=5,
    role="Lead",
    creativity=50,
    counter_style="Smooth",
):
    return _call_chatgpt_ai_impl(
        api_key,
        user_prompt,
        bars,
        chords_mode,
        theme_name,
        secret_rule=secret_rule,
        energy=energy,
        role=role,
        creativity=creativity,
        counter_style=counter_style,
    )


# Compatibility aliases for bridge modules/tests that still call legacy symbols.
_smart_generate_legacy = smart_generate
_generate_sax_solo_legacy = generate_sax_solo
_generate_piano_solo_legacy = generate_piano_solo
_generate_trumpet_solo_legacy = generate_trumpet_solo
_generate_flute_solo_legacy = generate_flute_solo
_generate_marimba_solo_legacy = generate_marimba_solo
_generate_vibraphone_solo_legacy = generate_vibraphone_solo
_generate_acoustic_bass_solo_legacy = generate_acoustic_bass_solo

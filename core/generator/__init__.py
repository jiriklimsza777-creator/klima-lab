# -*- coding: utf-8 -*-

from core.generator.ai_generate import call_chatgpt_ai
from core.generator.chords import build_chord_loop, chord_generate
from core.generator.melody_generate import smart_generate
from core.generator.melody_local import smart_generate_classic
from core.generator.solos import (
    generate_acoustic_bass_solo,
    generate_flute_solo,
    generate_marimba_solo,
    generate_piano_solo,
    generate_sax_solo,
    generate_trumpet_solo,
    generate_vibraphone_solo,
)
from core.generator.theme_profiles import (
    DEFAULT_PROFILE,
    PRODUCER_PROFILES,
    build_theme_profile,
    get_producer_profile,
    split_theme,
)
from core.generator.utils import (
    build_allowed_notes,
    choose_next_pitch,
    choose_next_pitch_classic,
    merge_unique,
    solo_duration_pool,
    solo_theme_mods,
    weighted_choice,
)

__all__ = [
    "DEFAULT_PROFILE",
    "PRODUCER_PROFILES",
    "build_allowed_notes",
    "build_chord_loop",
    "build_theme_profile",
    "call_chatgpt_ai",
    "chord_generate",
    "choose_next_pitch",
    "choose_next_pitch_classic",
    "generate_acoustic_bass_solo",
    "generate_flute_solo",
    "generate_marimba_solo",
    "generate_piano_solo",
    "generate_sax_solo",
    "generate_trumpet_solo",
    "generate_vibraphone_solo",
    "get_producer_profile",
    "merge_unique",
    "smart_generate",
    "smart_generate_classic",
    "solo_duration_pool",
    "solo_theme_mods",
    "split_theme",
    "weighted_choice",
]

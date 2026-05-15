# -*- coding: utf-8 -*-
"""
Shared constants and simple configuration for the Streamlit app.

Kept in a separate module so UI/pages can import without creating circular imports.
"""

import os

PAGE_GENERATOR = "🔥 GENERÁTOR"
PAGE_ARCHIVE = "📚 ARCHIV 2.0"
PAGE_IMPORT = "🎛️ IMPORT"

ENGINE_LAB = "Laboratoř"
ENGINE_STUDIO = "Studio"

# Visible app version (also stored into archive payloads for debugging/back-compat).
APP_VERSION = "v1.2.5"

MODE_MELODY = "🎵 Melodie"
MODE_CHORDS = "🎹 Akordy"

# Studio instruments (General MIDI program numbers)
STUDIO_INSTRUMENTS = {
    "Acoustic Grand Piano": 0,
    "Bright Piano": 1,
    "Rhodes Piano": 4,
    "Chorused Piano": 5,
    "Harpsichord": 6,
    "Drawbar Organ": 16,
    "Church Organ": 19,
    "Accordion": 21,
    "Music Box": 11,
    "Vibraphone": 12,
    "Marimba": 13,
    "Nylon Guitar": 24,
    "Steel String Guitar": 25,
    "Acoustic Bass": 32,
    "Electric Bass": 33,
    "String Ensemble": 48,
    "Trumpet": 56,
    "Alto Sax": 65,
    "Flute": 73,
    "Lead (square)": 80,
    "Pad (warm)": 89,
}

DISPLAY_STUDIO_INSTRUMENTS = [
    "Acoustic Grand Piano",
    "Rhodes Piano",
    "Acoustic Bass",
    "Electric Bass",
    "String Ensemble",
    "Alto Sax",
    "Flute",
    "Vibraphone",
    "Nylon Guitar",
    "Drawbar Organ",
    "Marimba",
    "Pad (warm)",
    "Trumpet",
    "Steel String Guitar",
    "Lead (square)",
]

# Kept for compatibility with older archive payloads (some projects may contain layers).
LAYER_INSTRUMENTS = [
    "Alto Sax",
    "Flute",
    "String Ensemble",
    "Pad (warm)",
    "Trumpet",
    "Nylon Guitar",
    "Steel String Guitar",
    "Acoustic Bass",
    "Electric Bass",
    "Drawbar Organ",
    "Lead (square)",
]

LAB_WAVES = {"Sinus": 0, "Čtverec": 1, "Pila": 2, "Trojúhelník": 3}

# This module lives under app/, so project root is the parent directory.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(APP_DIR, "assets", "image_1.png")
LOGO_CENTER_PATH = os.path.join(APP_DIR, "assets", "image_3.png")
BG_DEFAULT_PATH = os.path.join(APP_DIR, "assets", "image_2.jpg")

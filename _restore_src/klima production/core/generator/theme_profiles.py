# -*- coding: utf-8 -*-

PRODUCER_PROFILES = {
    "Daringer": {"density": 0.55, "swing": 0.01, "step": 0.5, "durations": [0.5, 0.5, 1.0], "jump": 4, "register": (50, 66), "motif": [4.0], "offbeat_bias": -0.03, "cadence_prob": 0.33, "variation": 0.14},
    "Apollo Brown": {"density": 0.65, "swing": 0.02, "step": 0.5, "durations": [0.5, 1.0], "jump": 5, "register": (52, 68), "motif": [4.0]},
    "J Dilla": {"density": 0.72, "swing": 0.09, "step": 0.25, "durations": [0.25, 0.5, 0.75], "jump": 5, "register": (54, 70), "motif": [2.0, 4.0], "offbeat_bias": 0.09, "cadence_prob": 0.18, "variation": 0.30, "loop_shift": 0.30, "loop_drop": 0.18, "loop_contrast": 0.22, "chord_step": 1.0, "chord_complexity": 0.62, "chord_arp_prob": 0.32},
    "Madlib": {"density": 0.78, "swing": 0.06, "step": 0.25, "durations": [0.25, 0.5, 0.75], "jump": 8, "register": (53, 72), "motif": [2.0, 4.0], "offbeat_bias": 0.06, "cadence_prob": 0.16, "variation": 0.34, "loop_shift": 0.36, "loop_drop": 0.22, "loop_contrast": 0.34, "chord_step": 1.0, "chord_complexity": 0.78, "chord_arp_prob": 0.40},
    "Knxwledge": {"density": 0.7, "swing": 0.08, "step": 0.25, "durations": [0.25, 0.5, 0.75], "jump": 4, "register": (56, 72), "motif": [2.0]},
    "Nujabes": {"density": 0.62, "swing": 0.03, "step": 0.5, "durations": [0.5, 1.0, 1.5], "jump": 5, "register": (58, 74), "motif": [4.0], "offbeat_bias": 0.02, "cadence_prob": 0.26, "variation": 0.18, "chord_step": 2.0, "chord_complexity": 0.55, "chord_arp_prob": 0.25},
    "Pete Rock": {"density": 0.68, "swing": 0.04, "step": 0.5, "durations": [0.5, 1.0], "jump": 5, "register": (54, 69), "motif": [2.0, 4.0], "loop_shift": 0.14, "loop_drop": 0.10, "loop_contrast": 0.18},
    "9th Wonder": {"density": 0.66, "swing": 0.04, "step": 0.5, "durations": [0.5, 1.0], "jump": 4, "register": (52, 68), "motif": [4.0]},
    "Q-Tip": {"density": 0.7, "swing": 0.05, "step": 0.25, "durations": [0.25, 0.5, 1.0], "jump": 5, "register": (55, 71), "motif": [2.0]},
    "Havoc": {"density": 0.6, "swing": 0.02, "step": 0.5, "durations": [0.5, 1.0], "jump": 4, "register": (48, 64), "motif": [4.0], "loop_shift": 0.10, "loop_drop": 0.14, "loop_contrast": 0.18},
    "RZA": {"density": 0.64, "swing": 0.03, "step": 0.5, "durations": [0.5, 1.0, 1.5], "jump": 7, "register": (47, 65), "motif": [4.0], "loop_shift": 0.16, "loop_drop": 0.18, "loop_contrast": 0.26},
    "MF DOOM": {"density": 0.74, "swing": 0.06, "step": 0.25, "durations": [0.25, 0.5, 1.0], "jump": 7, "register": (52, 69), "motif": [2.0], "loop_shift": 0.22, "loop_drop": 0.16, "loop_contrast": 0.28},
    "Dr Dre": {"density": 0.63, "swing": 0.01, "step": 0.5, "durations": [0.5, 1.0, 2.0], "jump": 4, "register": (50, 67), "motif": [4.0], "offbeat_bias": -0.06, "cadence_prob": 0.38, "variation": 0.10, "chord_step": 2.0, "chord_complexity": 0.20, "chord_arp_prob": 0.12},
    "Kanye West": {"density": 0.76, "swing": 0.02, "step": 0.25, "durations": [0.25, 0.5, 1.0], "jump": 8, "register": (55, 74), "motif": [2.0, 4.0]},
    "DJ Premier": {"density": 0.67, "swing": 0.03, "step": 0.5, "durations": [0.5, 0.5, 1.0], "jump": 4, "register": (53, 67), "motif": [2.0], "offbeat_bias": -0.02, "cadence_prob": 0.36, "variation": 0.12, "loop_shift": 0.10, "loop_drop": 0.20, "loop_contrast": 0.20, "chord_step": 2.0, "chord_complexity": 0.30, "chord_arp_prob": 0.18},
    "The Alchemist": {"density": 0.61, "swing": 0.02, "step": 0.5, "durations": [0.5, 1.0, 1.5], "jump": 4, "register": (49, 66), "motif": [4.0], "offbeat_bias": -0.01, "cadence_prob": 0.34, "variation": 0.13, "loop_shift": 0.12, "loop_drop": 0.16, "loop_contrast": 0.22, "chord_step": 2.0, "chord_complexity": 0.40, "chord_arp_prob": 0.20},
    "Just Blaze": {"density": 0.82, "swing": 0.02, "step": 0.25, "durations": [0.25, 0.5, 1.0], "jump": 7, "register": (57, 76), "motif": [2.0]},
    "Timbaland": {"density": 0.8, "swing": 0.04, "step": 0.25, "durations": [0.25, 0.5], "jump": 9, "register": (54, 73), "motif": [2.0]},
    "Metro Boomin": {"density": 0.88, "swing": 0.01, "step": 0.25, "durations": [0.25, 0.5, 0.5], "jump": 5, "register": (50, 68), "motif": [2.0]},
}

DEFAULT_PROFILE = {
    "density": 0.68,
    "swing": 0.04,
    "step": 0.25,
    "durations": [0.25, 0.5, 1.0],
    "jump": 5,
    "register": (52, 70),
    "motif": [2.0, 4.0],
    "offbeat_bias": 0.0,
    "cadence_prob": 0.24,
    "variation": 0.22,
    "chord_step": 2.0,
    "chord_complexity": 0.35,
    "chord_arp_prob": 0.20,
}


def split_theme(theme):
    parts = [part.strip() for part in str(theme).split("|")]
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", str(theme)


def get_producer_profile(producer):
    profile = dict(DEFAULT_PROFILE)
    profile.update(PRODUCER_PROFILES.get(producer, {}))
    return profile


def build_theme_profile(theme_name):
    profile = {
        "scale": [0, 3, 5, 7, 10],
        "density": 1.0,
        "swing": 1.0,
        "durations": [0.25, 0.5, 1.0],
        "jump": 0,
        "register_shift": 0,
        "accent": 0,
        "chords": [[0, 3, 7], [0, 5, 7], [0, 3, 7, 10]],
        "progression": [0, 5, 7, 10],
    }

    rules = {
        "Dark": {"scale": [0, 1, 5, 7, 8], "density": 0.85, "durations": [0.5, 1.0, 1.5], "jump": -1, "register_shift": -4, "chords": [[0, 3, 7], [0, 3, 6], [0, 5, 10]], "progression": [0, 1, 7, 8]},
        "Aggressive": {"scale": [0, 1, 5, 7, 8], "density": 1.15, "durations": [0.25, 0.5], "jump": 2, "accent": 8, "chords": [[0, 3, 6], [0, 1, 7], [0, 5, 10]], "progression": [0, 1, 5, 8]},
        "Jazzy": {"scale": [0, 3, 5, 7, 9, 10], "density": 0.95, "swing": 1.3, "durations": [0.5, 0.75, 1.0], "jump": 1, "register_shift": 2, "chords": [[0, 3, 7, 10], [0, 5, 7, 10], [0, 3, 7, 9]], "progression": [0, 2, 5, 9]},
        "Soulful": {"scale": [0, 3, 5, 7, 9, 10], "density": 0.9, "swing": 1.15, "durations": [0.5, 1.0, 1.5], "register_shift": 3, "chords": [[0, 3, 7, 10], [0, 5, 9], [0, 3, 7, 9]], "progression": [0, 3, 5, 10]},
        "Lo-Fi Chill": {"density": 0.75, "swing": 1.2, "durations": [0.5, 1.0, 1.5], "jump": -1, "register_shift": 1, "chords": [[0, 3, 7, 10], [0, 5, 7], [0, 3, 7, 9]]},
        "Rainy Night": {"scale": [0, 1, 3, 5, 7, 10], "density": 0.78, "durations": [0.5, 1.0, 1.5, 2.0], "register_shift": 2, "chords": [[0, 3, 7], [0, 3, 10], [0, 5, 10]]},
        "Sad Piano": {"density": 0.72, "durations": [0.5, 1.0, 2.0], "register_shift": 4, "chords": [[0, 3, 7], [0, 3, 10], [0, 7, 10]]},
        "Street": {"density": 0.9, "durations": [0.25, 0.5, 1.0], "jump": 1, "register_shift": -2},
        "Hard Boom Bap": {"density": 0.82, "swing": 1.1, "durations": [0.5, 0.5, 1.0], "jump": -1, "register_shift": -1, "chords": [[0, 3, 7], [0, 5, 10], [0, 3, 6]]},
        "Experimental": {"density": 1.08, "swing": 1.25, "durations": [0.25, 0.5, 0.75, 1.25], "jump": 3, "chords": [[0, 1, 7], [0, 3, 6, 10], [0, 5, 8]], "progression": [0, 1, 6, 10]},
        "Dreamy": {"density": 0.8, "durations": [0.5, 1.0, 1.5, 2.0], "register_shift": 5, "chords": [[0, 4, 7], [0, 5, 9], [0, 4, 7, 11]], "progression": [0, 4, 7, 9]},
        "Melancholic": {"density": 0.76, "durations": [0.5, 1.0, 1.5], "register_shift": 2, "chords": [[0, 3, 7], [0, 3, 10], [0, 7, 10]]},
    }

    theme_norm = str(theme_name or "").strip().lower()
    for label, update in rules.items():
        if theme_norm == label.strip().lower():
            profile.update(update)
            return profile
    for label, update in rules.items():
        if label.strip().lower() in theme_norm:
            profile.update(update)
            break
    return profile

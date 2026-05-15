# -*- coding: utf-8 -*-


def get_theme_string(producer: str, theme: str) -> str:
    p = str(producer or "").strip()
    t = str(theme or "").strip()
    producer_on = bool(p) and ("vypnuto" not in p.lower())
    theme_on = bool(t) and ("vypnuto" not in t.lower())
    if producer_on and theme_on:
        return f"{p} | {t}"
    if producer_on:
        return p
    if theme_on:
        return t
    return "Freestyle"

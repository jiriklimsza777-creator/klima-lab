# -*- coding: utf-8 -*-


def get_theme_string(producer: str, theme: str) -> str:
    if producer and "vypnuto" not in producer.lower():
        return f"{producer} | {theme}"
    return "Freestyle"


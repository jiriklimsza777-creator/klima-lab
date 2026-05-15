# -*- coding: utf-8 -*-


COMMON_TAGS = [
    "boombap",
    "jazz",
    "dark",
    "lofi",
    "soul",
    "rainy",
    "melancholy",
    "aggressive",
    "dreamy",
    "experimental",
    "piano",
    "sax",
    "bass",
]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def derive_tags(theme_string: str, instrument: str | None = None) -> list[str]:
    """
    Very simple auto-tagging from theme/producers/instrument.
    Keeps tags small and human-readable.
    """
    text = _norm(theme_string)
    inst = _norm(instrument or "")
    tags: set[str] = set()

    if "boom" in text or "premier" in text or "dilla" in text or "rza" in text or "pete rock" in text:
        tags.add("boombap")
    if "jazz" in text or "jazzy" in text:
        tags.add("jazz")
    if "dark" in text:
        tags.add("dark")
    if "lo-fi" in text or "lofi" in text or "chill" in text:
        tags.add("lofi")
    if "soul" in text:
        tags.add("soul")
    if "rain" in text:
        tags.add("rainy")
    if "melanch" in text or "sad" in text:
        tags.add("melancholy")
    if "aggress" in text or "hard" in text or "street" in text:
        tags.add("aggressive")
    if "dream" in text:
        tags.add("dreamy")
    if "exper" in text:
        tags.add("experimental")

    if "piano" in inst:
        tags.add("piano")
    if "sax" in inst:
        tags.add("sax")
    if "bass" in inst:
        tags.add("bass")

    # Keep stable ordering.
    return [t for t in COMMON_TAGS if t in tags]


def tags_to_str(tags: list[str] | str | None) -> str:
    if tags is None:
        return ""
    if isinstance(tags, str):
        return tags
    cleaned = []
    for t in tags:
        t2 = _norm(t)
        if t2:
            cleaned.append(t2)
    # unique while keeping order
    seen = set()
    out = []
    for t in cleaned:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return ",".join(out)


def str_to_tags(s: str | None) -> list[str]:
    if not s:
        return []
    parts = [p.strip().lower() for p in str(s).split(",")]
    return [p for p in parts if p]


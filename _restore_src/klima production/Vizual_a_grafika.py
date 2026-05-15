# -*- coding: utf-8 -*-
import base64
import os

import matplotlib.pyplot as plt


def _mime_from_path(file_path: str) -> str:
    ext = str(os.path.splitext(str(file_path))[1] or "").lower()
    if ext in [".png"]:
        return "image/png"
    if ext in [".webp"]:
        return "image/webp"
    return "image/jpeg"


def get_base64_image(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as file_obj:
                mime = _mime_from_path(file_path)
                return f"data:{mime};base64,{base64.b64encode(file_obj.read()).decode()}"
    except OSError:
        return ""
    return ""


def get_base64_uploaded(image_input):
    try:
        data = base64.b64encode(image_input.read()).decode()
        image_input.seek(0)
        mime = str(getattr(image_input, "type", "") or "").strip().lower()
        if not mime.startswith("image/"):
            name = str(getattr(image_input, "name", "") or "")
            mime = _mime_from_path(name)
        return f"data:{mime};base64,{data}"
    except Exception:
        return ""


def get_main_css(bg_type, p_color, card_style, font_name, bg_img_base64=""):
    if bg_type == "Animovaný Gradient":
        bg_css = (
            f"background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, {p_color}); "
            "background-size: 400% 400%; animation: gradientBG 15s ease infinite;"
        )
    elif bg_type == "Pulzující Temnota":
        bg_css = "background: radial-gradient(circle, #1a1a1a 0%, #000000 100%); animation: pulseBG 5s infinite alternate;"
    elif bg_type == "Lo-Fi Papír":
        bg_css = (
            "background-image:"
            " linear-gradient(rgba(0,0,0,0.78), rgba(0,0,0,0.86)),"
            " repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 6px),"
            " radial-gradient(circle at 20% 10%, rgba(255,220,180,0.08), transparent 55%),"
            " radial-gradient(circle at 80% 90%, rgba(180,220,255,0.06), transparent 60%);"
            "background-size: cover, auto, cover, cover;"
            "background-attachment: fixed;"
        )
    elif bg_type == "Jazz Club":
        bg_css = (
            "background-image:"
            " radial-gradient(circle at 35% 20%, rgba(255,215,140,0.10), transparent 40%),"
            " radial-gradient(circle at 70% 55%, rgba(190,70,30,0.10), transparent 55%),"
            " linear-gradient(180deg, rgba(0,0,0,0.92), rgba(10,6,4,0.96));"
            "background-size: cover; background-attachment: fixed;"
        )
    elif bg_type == "Blueprint Grid":
        bg_css = (
            "background-color: #061a2e;"
            "background-image:"
            " linear-gradient(rgba(0,0,0,0.72), rgba(0,0,0,0.82)),"
            " repeating-linear-gradient(0deg, rgba(95,215,255,0.08) 0px, rgba(95,215,255,0.08) 1px, transparent 1px, transparent 28px),"
            " repeating-linear-gradient(90deg, rgba(95,215,255,0.08) 0px, rgba(95,215,255,0.08) 1px, transparent 1px, transparent 28px),"
            " repeating-linear-gradient(0deg, rgba(95,215,255,0.05) 0px, rgba(95,215,255,0.05) 1px, transparent 1px, transparent 7px),"
            " repeating-linear-gradient(90deg, rgba(95,215,255,0.05) 0px, rgba(95,215,255,0.05) 1px, transparent 1px, transparent 7px);"
            "background-size: cover, auto, auto, auto, auto;"
            "background-attachment: fixed;"
        )
    elif bg_type == "CRT Scanlines":
        bg_css = (
            "background-image:"
            " linear-gradient(rgba(0,0,0,0.78), rgba(0,0,0,0.88)),"
            " repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0px, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 3px),"
            " radial-gradient(circle at 50% 30%, rgba(0,255,200,0.07), transparent 55%);"
            "background-size: cover, auto, cover; background-attachment: fixed;"
        )
    elif bg_type == "Tape Sunset":
        bg_css = (
            "background: radial-gradient(circle at 25% 15%, rgba(255,170,120,0.20), transparent 45%),"
            " radial-gradient(circle at 70% 80%, rgba(120,180,255,0.18), transparent 55%),"
            " linear-gradient(135deg, #130b1d 0%, #1b0a14 35%, #0a121a 100%);"
            "background-attachment: fixed;"
        )
    elif bg_type == "Studio Fog":
        bg_css = (
            "background-image:"
            " radial-gradient(circle at 30% 25%, rgba(255,255,255,0.06), transparent 55%),"
            " radial-gradient(circle at 70% 65%, rgba(255,255,255,0.05), transparent 60%),"
            " linear-gradient(180deg, rgba(0,0,0,0.92), rgba(0,0,0,0.96));"
            "background-size: cover; background-attachment: fixed;"
        )
    elif bg_type == "Vaporwave Haze":
        bg_css = (
            "background-image:"
            " linear-gradient(rgba(0,0,0,0.72), rgba(0,0,0,0.84)),"
            " radial-gradient(circle at 15% 25%, rgba(255,90,200,0.16), transparent 55%),"
            " radial-gradient(circle at 85% 65%, rgba(80,220,255,0.14), transparent 60%),"
            f" linear-gradient(135deg, #0b0820 0%, #1a0b2e 40%, {p_color}20 100%);"
            "background-size: cover; background-attachment: fixed;"
        )
    else:
        bg_css = (
            f"background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('{bg_img_base64}'); "
            "background-size: cover; background-attachment: fixed;"
        )

    styles = {
        "Skleněný (Glassmorphism)": f"background: rgba(20, 20, 20, 0.35); backdrop-filter: blur(12px); border-left: 5px solid {p_color};",
        "Neonový (Glow)": f"background: rgba(5, 5, 5, 0.9); border: 1px solid {p_color}; box-shadow: 0 0 15px {p_color}40; border-left: 5px solid {p_color};",
        "Cyberpunk": f"background: #0d0d0d; border-right: 4px solid {p_color}; border-bottom: 4px solid {p_color}; clip-path: polygon(0 0, 100% 0, 100% 90%, 95% 100%, 0 100%); border-radius: 0;",
        "Retro Lo-Fi": f"background: #1e1e1e; border: 2px solid #666; box-shadow: 5px 5px 0px {p_color}; border-radius: 0;",
        "Čistý Minimal (Flat)": f"background: transparent; border: 1px solid {p_color}; border-radius: 5px; box-shadow: none;",
        "Metal (Brushed)": (
            "background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));"
            f"border: 1px solid rgba(255,255,255,0.10); box-shadow: inset 0 0 0 1px rgba(0,0,0,0.35); border-left: 5px solid {p_color};"
        ),
        "Vinyl Sleeve": (
            "background: radial-gradient(circle at 30% 25%, rgba(255,255,255,0.06), transparent 45%),"
            " radial-gradient(circle at 70% 80%, rgba(0,0,0,0.55), transparent 60%),"
            " rgba(18,18,18,0.60);"
            f"border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; border-left: 5px solid {p_color};"
        ),
        "Notebook (Ruled)": (
            "background-image:"
            " linear-gradient(rgba(0,0,0,0.60), rgba(0,0,0,0.70)),"
            " repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 20px);"
            f"border: 1px solid rgba(255,255,255,0.08); border-left: 5px solid {p_color};"
        ),
        "Tape Deck": (
            "background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(0,0,0,0.25));"
            f"border: 1px solid rgba(255,255,255,0.10); box-shadow: 0 12px 28px rgba(0,0,0,0.35); border-left: 5px solid {p_color};"
        ),
        "Brutalist Blocks": (
            "background: rgba(10,10,10,0.92);"
            f"border: 2px solid {p_color}; box-shadow: 8px 8px 0 rgba(0,0,0,0.55); border-radius: 0;"
        ),
        "Soft Shadow": (
            "background: rgba(18,18,18,0.48);"
            f"border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 18px 55px rgba(0,0,0,0.40); border-left: 5px solid {p_color};"
        ),
        "Outline Mono": (
            "background: rgba(0,0,0,0.30);"
            f"border: 1px dashed rgba(255,255,255,0.16); border-left: 5px solid {p_color}; border-radius: 14px;"
        ),
    }
    card_css = styles.get(card_style, f"background: rgba(10, 10, 10, 0.9); border-left: 8px solid {p_color};")

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={font_name.replace(" ", "+")}&display=swap');
    @keyframes gradientBG {{ 0% {{background-position: 0% 50%;}} 50% {{background-position: 100% 50%;}} 100% {{background-position: 0% 50%;}} }}
    @keyframes pulseBG {{ 0% {{background-color: #050505;}} 100% {{background-color: #1a1a1a;}} }}
    .main .block-container {{ max-width: 95%; padding-left: 2rem; padding-right: 2rem; padding-top: 2rem; margin: 0 auto; }}
    .stApp {{ {bg_css} color: #f0f0f0; font-family: '{font_name}', sans-serif !important; }}
    .topbar {{
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.55rem 0.75rem;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(10px);
    }}
    .topbar .stSelectbox, .topbar .stRadio, .topbar .stButton {{ margin: 0 !important; }}
    /* In the topbar we want a normal pointer cursor (avoid I-beam caret feel). */
    .topbar [data-testid="stSelectbox"], .topbar [data-testid="stSelectbox"] *,
    .topbar [data-baseweb="select"], .topbar [data-baseweb="select"] * {{
        cursor: pointer !important;
        user-select: none !important;
    }}
    .topbar [data-baseweb="select"] input {{
        caret-color: transparent !important;
    }}
    .topbar-mini {{
        font-size: 0.78rem;
        font-weight: 700;
        opacity: 0.9;
        text-align: center;
        line-height: 2.2;
        white-space: nowrap;
    }}
    .topbar [data-testid="stRadio"] label {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    /* Segmented style for the page switcher */
    .topbar [data-testid="stRadio"] div[role="radiogroup"] {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 4px;
        gap: 6px;
    }}
    .topbar [data-testid="stRadio"] div[role="radiogroup"] label {{
        background: transparent;
        border-radius: 10px;
        padding: 0.35rem 0.6rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        user-select: none;
    }}
    .topbar [data-testid="stRadio"] div[role="radiogroup"] label:hover {{
        background: rgba(255,255,255,0.06);
    }}
    /* One-line status row above the main Generate button: must never wrap. */
    .gen-statusline {{
        display: flex;
        flex-wrap: nowrap;
        justify-content: center;
        align-items: center;
        gap: clamp(0.25rem, 0.55vw, 0.55rem);
        font-size: clamp(0.66rem, 0.85vw, 0.82rem);
        font-weight: 700;
        opacity: 0.90;
        margin: 0.15rem 0 0.35rem 0;
        white-space: nowrap !important;
        overflow-x: auto;
        overflow-y: hidden;
        text-align: center;
        line-height: 1.15;
    }}
    .gen-statusline * {{
        white-space: nowrap !important;
    }}
    .gen-statusline code {{
        padding: 0.05rem 0.28rem;
        border-radius: 7px;
        font-size: 0.98em;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .gen-statusline .sep {{
        opacity: 0.65;
        padding: 0 0.05rem;
        flex: 0 0 auto;
    }}
    .gen-statusline::-webkit-scrollbar {{
        height: 0px;
    }}
    :root {{
        --ui-radius-sm: 10px;
        --ui-radius-md: 12px;
        --ui-radius-lg: 15px;
        --ui-pad-xs: 0.35rem;
        --ui-pad-sm: 0.55rem;
        --ui-pad-md: 0.7rem;
        --ui-gap-sm: 0.45rem;
        --ui-gap-md: 0.7rem;
        --ui-border-soft: 1px solid rgba(255,255,255,0.08);
        --ui-bg-soft: rgba(255,255,255,0.03);
        --ui-bg-panel: rgba(0,0,0,0.14);
    }}
    /* Remove "bands" between proposals: transparent cards + minimal spacing. */
    .card {{ {card_css} padding: 2px 12px 0px 12px; border-radius: var(--ui-radius-lg); margin-bottom: 0px; position: relative; overflow: visible; }}
    .card {{ background: transparent !important; box-shadow: none !important; }}
    .card h3 {{ margin-top: 0; margin-bottom: 0.15rem; }}
    .proposal-label {{ font-size: 1.18rem; font-weight: 800; letter-spacing: 0.1em; color: {p_color}; opacity: 0.98; margin: 0.05rem 0 0.05rem 0; text-transform: uppercase; }}
    .melody-plot {{ margin: 0; padding: 0 !important; }}
    .melody-plot > div {{ margin: 0 !important; padding: 0 !important; }}
    .melody-plot [data-testid="stImage"], .melody-plot [data-testid="stPlotlyChart"], .melody-plot [data-testid="stPyplot"] {{ margin: 0 !important; padding: 0 !important; }}
    .melody-plot [data-testid="stPyplot"] > div {{ margin: 0 !important; padding: 0 !important; }}
    .melody-plot img {{ margin: 0 !important; padding: 0 !important; display: block; }}
    .side-panel {{ background: var(--ui-bg-panel); border: var(--ui-border-soft); border-radius: var(--ui-radius-md); padding: 0.5rem var(--ui-pad-md) var(--ui-pad-md) var(--ui-pad-md); }}
    .side-panel [data-testid="stAudio"] {{ margin-top: 0 !important; margin-bottom: 0.25rem; }}
    .side-panel .stTextInput, .side-panel .stPopover, .side-panel .stButton, .side-panel .stDownloadButton {{
        margin-top: 0.18rem;
        margin-bottom: 0.18rem;
    }}
    .side-panel .stPopover [data-testid="stCaptionContainer"] {{
        margin-bottom: 0.2rem;
        opacity: 0.9;
    }}
    .side-panel .stPopover [data-testid="stRadio"] label {{
        padding-top: 0.1rem;
        padding-bottom: 0.1rem;
    }}
    .side-panel [data-testid="column"] {{
        padding-top: 0.02rem;
        padding-bottom: 0.02rem;
    }}
    .audio-deck {{ background: var(--ui-bg-soft); padding: 6px; border-radius: var(--ui-radius-sm); margin-top: 0px; }}
    .audio-row {{ background: var(--ui-bg-soft); border: var(--ui-border-soft); border-radius: var(--ui-radius-md); padding: var(--ui-pad-sm) 0.65rem; margin-top: 0.55rem; }}
    .layers-line {{ margin-top: 0.4rem; margin-bottom: 0.35rem; font-size: 0.92rem; opacity: 0.92; }}
    .bottom-bar {{ margin-top: 0.25rem; }}
    .octave-display {{ font-size: 0.8rem; font-weight: bold; color: {p_color}; opacity: 0.8; text-align: center; line-height: 2.2; white-space: nowrap; }}
    .card .stButton > button, .card .stDownloadButton > button {{
        border-radius: var(--ui-radius-sm);
        border: var(--ui-border-soft);
        background: rgba(255,255,255,0.04);
        font-weight: 700;
    }}
    .card .stButton > button:hover, .card .stDownloadButton > button:hover {{
        border-color: rgba(255,255,255,0.22);
        background: rgba(255,255,255,0.07);
    }}
    .card [data-testid="stTextInput"] input, .card [data-baseweb="select"] > div {{
        border-radius: var(--ui-radius-sm);
    }}
    .stExpander, .stExpander * {{ cursor: default; }}
    .stExpander summary, .stExpander summary *, .stExpander details summary, .stExpander details summary *, .stExpander [data-testid="stExpander"], .stExpander [data-testid="stExpander"] *, .stExpander label, .stExpander p, .stExpander span, .stExpander svg {{
        cursor: pointer !important;
        user-select: none !important;
        caret-color: transparent !important;
    }}
    </style>
    """


def create_piano_roll(melody_data, chart_style, p_color):
    fig, ax = plt.subplots(figsize=(8, 3.15))

    bg_color = "#050505"
    fig_bg = "#000000"
    bar_color = p_color
    bar_alpha = 0.6
    edgecolor = "none"

    if chart_style == "Neon":
        bar_alpha = 1.0
        edgecolor = "#ffffff"
    elif chart_style == "Minimalistický":
        # Matplotlib doesn't accept CSS "transparent"; use "none" (alpha=0).
        bg_color = "none"
        fig_bg = "none"
        bar_alpha = 0.8
    elif chart_style == "Synthwave (80s)":
        bg_color = "#1a0b2e"
        fig_bg = "#0d0218"
        ax.grid(color="#ff00ff", linestyle="--", linewidth=0.5, alpha=0.5)
        bar_alpha = 0.9
    elif chart_style == "Lo-Fi Grayscale":
        bg_color = "#2c2c2c"
        fig_bg = "#1a1a1a"
        bar_color = "#888888"
        bar_alpha = 0.7
    elif chart_style == "Hologram":
        bg_color = "none"
        fig_bg = "#000814"
        bar_alpha = 0.3
        edgecolor = p_color
    elif chart_style == "Blueprint":
        bg_color = "#041a2d"
        fig_bg = "#03111f"
        bar_color = "#7de7ff"
        bar_alpha = 0.75
        edgecolor = "#bdf5ff"
        ax.grid(color="#1e9cc6", linestyle="-", linewidth=0.4, alpha=0.35)
    elif chart_style == "Paper":
        bg_color = "#f4efe6"
        fig_bg = "#f4efe6"
        bar_color = "#2a2a2a"
        bar_alpha = 0.80
        edgecolor = "none"
    elif chart_style == "Jazz Club":
        bg_color = "#120b07"
        fig_bg = "#080504"
        bar_color = "#ffcf7a"
        bar_alpha = 0.85
        edgecolor = "#2b1b10"
        ax.grid(color="#3a2416", linestyle=":", linewidth=0.6, alpha=0.5)
    elif chart_style == "Arcade":
        bg_color = "#06030f"
        fig_bg = "#020105"
        bar_color = "#39ff14"  # arcade green
        bar_alpha = 0.95
        edgecolor = "#0b2b0a"
        ax.grid(color="#3b2a66", linestyle="--", linewidth=0.45, alpha=0.35)
    elif chart_style == "High Contrast":
        bg_color = "#000000"
        fig_bg = "#000000"
        bar_color = "#ffffff"
        bar_alpha = 0.92
        edgecolor = "none"
    elif chart_style == "Soft Pastel":
        bg_color = "#0b0b12"
        fig_bg = "#07070c"
        bar_color = "#a9c6ff"
        bar_alpha = 0.65
        edgecolor = "#ffd1f5"
        ax.grid(color="#ffffff", linestyle=":", linewidth=0.4, alpha=0.12)

    # Safety: never pass CSS "transparent" into matplotlib.
    if bg_color == "transparent":
        bg_color = "none"
    if fig_bg == "transparent":
        fig_bg = "none"

    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(fig_bg)

    for spine in ax.spines.values():
        spine.set_visible(False)

    for note in melody_data:
        ax.barh(
            note[1],
            note[2],
            left=note[0],
            color=bar_color,
            alpha=bar_alpha,
            height=0.7,
            edgecolor=edgecolor,
            linewidth=1 if edgecolor != "none" else 0,
        )

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.margins(x=0, y=0.12)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    return fig

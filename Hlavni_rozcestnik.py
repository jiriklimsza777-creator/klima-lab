# -*- coding: utf-8 -*-
import streamlit as st

import Pamet_a_archiv as db
from app.config import PAGE_ARCHIVE, PAGE_GENERATOR, PAGE_IMPORT
from app.state import init_state
from app.utils import get_theme_string
from ui.pages import render_archive_page, render_generator_page, render_import_page
from ui.sidebar import render_sidebar
from ui.theme import apply_visual_style


st.set_page_config(page_title="Klima_Lab Pro", page_icon="🎹", layout="wide")


init_state()
all_producers, all_themes = db.get_producers_and_themes()

uploaded_bg, page, selected_producer, selected_theme = render_sidebar(all_producers, all_themes)
final_theme_string = get_theme_string(selected_producer, selected_theme)
st.session_state["current_selected_producer"] = selected_producer
st.session_state["current_theme_string"] = final_theme_string
apply_visual_style(uploaded_bg)

if page == PAGE_GENERATOR:
    render_generator_page(selected_producer, final_theme_string)
elif page == PAGE_ARCHIVE:
    render_archive_page()
else:
    render_import_page(selected_producer, selected_theme)

# -*- coding: utf-8 -*-

import streamlit as st

import Vizual_a_grafika as ui
from app.config import BG_DEFAULT_PATH


def apply_visual_style(uploaded_bg):
    bg_img_b64 = ui.get_base64_uploaded(uploaded_bg) if uploaded_bg else ui.get_base64_image(BG_DEFAULT_PATH)
    st.markdown(
        ui.get_main_css(
            st.session_state.bg_type,
            st.session_state.p_color,
            st.session_state.card_style,
            st.session_state.font,
            bg_img_b64,
        ),
        unsafe_allow_html=True,
    )

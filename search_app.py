"""
search_app.py — Lance le module 2 seul (algorithmes de recherche).

    streamlit run search_app.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_interface import run_search_module      # noqa: E402

if __name__ == "__main__":
    st.set_page_config(page_title="Algorithmes de recherche", layout="wide",
                       initial_sidebar_state="collapsed")
    run_search_module()
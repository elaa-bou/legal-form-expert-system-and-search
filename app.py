"""
app.py — Page d'accueil (menu principal) de l'application.

Assignment 1 — IA et ML · II2 · ENSI
Menu principal :
    1. Systèmes experts
    2. Algorithmes de recherche
    3. Quitter

Lancement :
    streamlit run app.py

Organisation du projet (tous les fichiers dans le même dossier) :
    app.py               <- ce fichier : menu principal + navigation
    interface.py         <- Module 1 : interface du système expert
    engine.py            <- Module 1 : moteur d'inférence (chaînage avant / arrière)
    knowledge_base.py    <- Module 1 : base de faits et de règles
    search_interface.py  <- Module 2 : interface des algorithmes de recherche
    search_engine.py     <- Module 2 : graphe + algorithmes (BFS, DFS, UCS, Gloutonne, A*...)
"""

import os
import sys

import streamlit as st



# Permet d'importer les modules voisins quel que soit le dossier de lancement.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import run_expert_system          # noqa: E402  (Module 1)
from search_interface import run_search_module   # noqa: E402  (Module 2)

# Pages possibles de l'application
HOME, EXPERT, SEARCH, BYE = "home", "expert", "search", "bye"

# Même charte graphique que les deux modules (papier crème, encre, bleu-vert, cuivre)
HOME_CSS = """
<style>
.stApp {background:#f4efe6;}
.block-container {padding-top:1.3rem; max-width:1100px;}
.stApp p, .stApp label, .stApp li, .stApp [data-testid="stMarkdownContainer"] {color:#1c2230;}
.stApp h1, .stApp h2, .stApp h3 {font-family:Georgia,'Times New Roman',serif; color:#1c2230;}
.stApp button[data-testid="stBaseButton-primary"] {background:#0f4c5c; border-color:#0f4c5c;
  color:#fff; border-radius:2px; padding:.7rem 1rem;}
.stApp button[data-testid="stBaseButton-primary"] p {color:#fff !important; font-size:1.05rem;}
.stApp button[data-testid="stBaseButton-secondary"] {border-radius:2px; padding:.7rem 1rem;}

.mast {border-top:5px double #1c2230; border-bottom:1px solid #1c2230; padding:16px 0 14px 0;
  margin-bottom:28px;}
.mast .over {letter-spacing:.3em; font-size:.7rem; color:#6b6558; text-transform:uppercase;}
.mast .title {font-family:Georgia,'Times New Roman',serif; font-size:3rem; line-height:1.05;
  color:#1c2230; font-weight:700; margin-top:6px;}
.mast .sub {color:#6b6558; font-size:.95rem; margin-top:8px;}

.menu-label {font-size:.66rem; letter-spacing:.22em; text-transform:uppercase; color:#6b6558;
  border-bottom:1px solid #1c2230; padding-bottom:6px; margin:6px 0 16px 0;}

.card {background:#fffdf8; border:1px solid #ddd3bf; border-top:4px solid #b5651d;
  padding:18px 22px 16px 22px; margin-bottom:10px; min-height:215px;}
.card.alt {border-top-color:#0f4c5c;}
.card .num {font-family:Georgia,serif; font-size:2.6rem; color:#b5651d; line-height:1;}
.card.alt .num {color:#0f4c5c;}
.card .ttl {font-family:Georgia,serif; font-size:1.45rem; font-weight:700; color:#1c2230;
  margin:6px 0 8px 0;}
.card .dsc {font-size:.9rem; color:#1c2230; line-height:1.5;}
.card ul {margin:10px 0 0 0; padding-left:18px; color:#6b6558; font-size:.82rem; line-height:1.6;}

.foot {margin-top:34px; border-top:1px solid #1c2230; padding-top:8px; font-size:.76rem;
  color:#6b6558; display:flex; justify-content:space-between;}

.bye {background:#1c2230; color:#f4efe6; padding:44px 40px; border-left:12px solid #b5651d;
  margin:20px 0;}
.bye .big {font-family:Georgia,serif; font-size:2.6rem; font-weight:700; color:#f4efe6;}
.bye .small {opacity:.85; margin-top:8px; color:#f4efe6;}
</style>
"""


# ----------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------
def goto(page):
    """Callback de bouton : change de page (le rerun est automatique)."""
    st.session_state.page = page


def back_button():
    """Bouton 'Menu principal' affiché en haut des modules."""
    st.button("← Menu principal", on_click=goto, args=(HOME,), key="btn_back_home")


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
def home_page():
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="mast"><div class="over"> '
        "</div>"
        '<div class="title">Menu principal</div>'
        '<div class="sub">Systèmes experts et algorithmes de recherche</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="menu-label">Choisissez un module</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            '<div class="card"><div class="num">1</div>'
            '<div class="ttl">Systèmes experts</div>'
            '<div class="dsc">Base de faits et base de règles : identification de la forme ',
            unsafe_allow_html=True,
        )
        st.button("Ouvrir les systèmes experts", type="primary", use_container_width=True,
                  on_click=goto, args=(EXPERT,), key="btn_expert")
    with c2:
        st.markdown(
            '<div class="card alt"><div class="num">2</div>'
            '<div class="ttl">Algorithmes de recherche</div>'
            '<div class="dsc">Construction d\'un graphe orienté et pondéré, puis recherche '
            "d'un chemin entre un état initial et un état objectif.</div>",
            unsafe_allow_html=True,
        )
        st.button("Ouvrir les algorithmes de recherche", type="primary",
                  use_container_width=True, on_click=goto, args=(SEARCH,), key="btn_search")

    st.write("")
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.button("3 · Quitter", use_container_width=True, on_click=goto, args=(BYE,),
                  key="btn_quit")

    st.markdown('<div class="foot"><span>Module IA et Machine Learning</span>'
                "<span>Systèmes experts · Algorithmes de recherche</span></div>",
                unsafe_allow_html=True)


def bye_page():
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    st.markdown('<div class="bye"><div class="big">Au revoir !</div>'
                '<div class="small">Merci d\'avoir utilisé l\'application. '
                "Vous pouvez fermer cet onglet ; pour arrêter le serveur, utilisez Ctrl+C "
                "dans le terminal.</div></div>", unsafe_allow_html=True)
    st.button("Revenir au menu principal", on_click=goto, args=(HOME,), key="btn_bye_home")


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="IA et ML — Menu principal", layout="wide",
                       initial_sidebar_state="expanded")

    if "page" not in st.session_state:
        st.session_state.page = HOME

    page = st.session_state.page
    if page == EXPERT:
        back_button()
        run_expert_system()
    elif page == SEARCH:
        back_button()
        run_search_module()
    elif page == BYE:
        bye_page()
    else:
        home_page()


if __name__ == "__main__":
    main()

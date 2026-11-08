"""
search_interface.py — Interface Streamlit du module « Algorithmes de recherche » (autonome).

    streamlit run search_app.py

Trois onglets :
Une fonction par zone, sans logique d'algorithme (le moteur s'en charge) :
  theme()        : style
  draw_graph()   : graphe + état d'une étape -> DOT
  builder_tab()  : 01 construction du graphe (sommets, arcs, coûts, heuristique, départ/but, fichiers)
  runner_tab()   : 02 choix de l'algorithme, exécution pas à pas ou animée, panneau Open/Close, f(n)
  compare_tab()  : 03 tous les algorithmes sur le même graphe
"""

import copy
import html
import inspect
import json
import time

import pandas as pd
import streamlit as st

from search_engine import (ALGORITHMS, EXAMPLES, Graph, compare_all, example_graph, fmt,
                           make_algorithm, run_search)

CATEGORIES = {"Recherche non informée (aveugle)": "uninformed",
              "Recherche informée (heuristique)": "informed"}
TAGS = {"info": "Méthode", "expand": "Expansion", "skip": "Ignoré", "success": "Succès", "fail": "Échec"}
TAG_CSS = {"info": "info", "expand": "goal", "skip": "skip", "success": "success", "fail": "fail"}

CSS = """
<style>
.stApp {background:#f4efe6;}
.block-container {padding-top:1.3rem; max-width:1280px;}
.stApp p, .stApp label, .stApp li, .stApp [data-testid="stMarkdownContainer"] {color:#1c2230;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {font-family:Georgia,'Times New Roman',serif; color:#1c2230;}
.stApp button[data-testid="stBaseButton-primary"],
.stApp button[data-testid="stBaseButton-primaryFormSubmit"] {background:#0f4c5c; border-color:#0f4c5c; color:#fff; border-radius:2px;}
.stApp button[data-testid="stBaseButton-primary"] p,
.stApp button[data-testid="stBaseButton-primaryFormSubmit"] p {color:#fff !important;}
.stApp button[data-testid="stBaseButton-secondary"],
.stApp button[data-testid="stBaseButton-secondaryFormSubmit"] {border-radius:2px;}
.mast {border-top:5px double #1c2230; border-bottom:1px solid #1c2230; padding:16px 0 14px 0;
  margin-bottom:24px; display:flex; justify-content:space-between; align-items:flex-end;}
.mast .over {letter-spacing:.3em; font-size:.7rem; color:#6b6558; text-transform:uppercase;}
.mast .title {font-family:Georgia,'Times New Roman',serif; font-size:2.8rem; line-height:1.05;
  color:#1c2230; font-weight:700; margin-top:6px;}
.mast .meta {text-align:right; font-size:.82rem; color:#6b6558; line-height:1.5;}
.mast .meta b {color:#1c2230; font-family:Georgia,serif; font-size:1.5rem; margin-right:4px;}
.sec {display:flex; align-items:baseline; gap:14px; border-bottom:1px solid #1c2230;
  padding-bottom:6px; margin:4px 0 14px 0;}
.sec .num {font-family:Georgia,serif; font-size:2.3rem; color:#b5651d; line-height:1;}
.sec .ttl {font-family:Georgia,serif; font-size:1.4rem; font-weight:700; color:#1c2230;}
.sec .sub {margin-left:auto; font-size:.78rem; color:#6b6558;}
.note {border-left:4px solid #b5651d; background:#efe8d8; padding:9px 14px; font-size:.88rem;
  color:#1c2230; margin:8px 0;}
.note.err {border-left-color:#c0392b;}
.note.good {border-left-color:#2d6a4f;}
.verdict {background:#1c2230; color:#f4efe6; padding:26px 32px; border-left:12px solid #2d6a4f; margin:14px 0 0 0;}
.verdict.ko {border-left-color:#c0392b;}
.verdict .vlabel {letter-spacing:.26em; font-size:.68rem; text-transform:uppercase; opacity:.7; color:#f4efe6;}
.verdict .vmain {font-family:Georgia,'Times New Roman',serif; font-size:3.1rem; line-height:1.08;
  font-weight:700; margin:8px 0 6px 0; color:#f4efe6;}
.verdict .vsub {opacity:.88; font-size:1rem; color:#f4efe6;}
.verdict code {background:rgba(244,239,230,.14); color:#f4efe6; padding:1px 8px; border-radius:3px;}
.vstats {display:flex; background:#fffdf8; border:1px solid #ddd3bf; border-top:0;}
.vstats > div {flex:1; padding:14px 20px; border-right:1px solid #ddd3bf;}
.vstats > div:last-child {border-right:0;}
.vstats .n {font-family:Georgia,serif; font-size:2.1rem; font-weight:700; color:#1c2230; line-height:1;}
.vstats .l {font-size:.64rem; letter-spacing:.18em; text-transform:uppercase; color:#6b6558; margin-top:4px;}
.lab {font-size:.66rem; letter-spacing:.2em; text-transform:uppercase; color:#6b6558; margin:18px 0 6px 0;}
.chip {display:inline-block; border:1px solid #1c2230; padding:2px 11px; margin:3px 6px 3px 0;
  font-size:.8rem; color:#1c2230; background:#fffdf8; border-radius:2px;}
.chip.hl {background:#b5651d; border-color:#b5651d; color:#fff; font-weight:700;}
.formula {font-family:Georgia,serif; font-size:1.05rem; color:#1c2230; background:#fffdf8;
  border:1px solid #ddd3bf; padding:8px 14px; margin:4px 0;}
table.proof {width:100%; border-collapse:collapse; background:#fffdf8; font-size:.85rem; color:#1c2230;}
table.proof th {text-align:left; font-size:.64rem; letter-spacing:.18em; text-transform:uppercase;
  color:#6b6558; border-bottom:2px solid #1c2230; padding:7px 10px;}
table.proof td {border-bottom:1px solid #ddd3bf; padding:9px 10px; vertical-align:top; color:#1c2230;}
table.proof tr.best td {background:#e3f1e8; font-weight:700;}
.led {background:#fffdf8; border:1px solid #ddd3bf; padding:4px 0 8px 0;}
.cyc {background:#1c2230; color:#f4efe6; font-size:.68rem; letter-spacing:.24em;
  text-transform:uppercase; padding:6px 16px; margin:8px 0 3px 0;}
.st {display:grid; grid-template-columns:36px 86px 1fr; gap:8px; padding:5px 16px;
  color:#1c2230; font-size:.85rem; align-items:baseline;}
.st .no {font-family:Georgia,serif; color:#b5651d; font-weight:700;}
.st .tg {font-size:.6rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700;}
.tg.fire, .tg.success {color:#2d6a4f;}
.tg.fail {color:#c0392b;}
.tg.goal, .tg.try {color:#0f4c5c;}
.tg.check, .tg.skip, .tg.info {color:#6b6558;}
.st .tx {line-height:1.45; color:#1c2230;}
.legend {font-size:.78rem; color:#6b6558; margin:4px 0 10px 0;}
</style>
"""


def theme():
    st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------
def esc(x):
    return html.escape(str(x))


def stretch(fn):
    """Largeur 100 % compatible avec les anciennes et nouvelles versions de Streamlit."""
    return {"width": "stretch"} if "width" in inspect.signature(fn).parameters \
        else {"use_container_width": True}


def note(text, kind=""):
    st.markdown(f'<div class="note {kind}">{text}</div>', unsafe_allow_html=True)


def section(num, title, sub=""):
    st.markdown(f'<div class="sec"><span class="num">{num}</span><span class="ttl">{esc(title)}</span>'
                f'<span class="sub">{esc(sub)}</span></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# État de session
# ----------------------------------------------------------------------
def init_search_state():
    ss = st.session_state
    if "sg" not in ss:
        ss.sg = example_graph()
        ss.sres = None          # dernier résultat de recherche
        ss.scmp = None          # dernière comparaison
        ss.sflash = None
        ss.srun_counter = 0


def graph_changed(msg=None, kind="good"):
    st.session_state.sres = None
    st.session_state.scmp = None
    if msg:
        st.session_state.sflash = (kind, msg)


def attempt(action, success_msg):
    """Applique une modification du graphe ; en cas de succès, relance la page."""
    try:
        action()
    except ValueError as e:
        st.error(str(e))
        return
    graph_changed(success_msg)
    st.rerun()


def show_flash():
    if st.session_state.get("sflash"):
        kind, msg = st.session_state.sflash
        note(esc(msg), kind)
        st.session_state.sflash = None


# Callbacks (exécutés avant le rerun)
def cb_example():
    name = st.session_state.get("ex_sel")
    if name in EXAMPLES:
        st.session_state.sg = EXAMPLES[name]()
        graph_changed(f"Exemple chargé : {name}.")


def cb_empty():
    st.session_state.sg = Graph()
    graph_changed("Graphe vidé.")


def cb_toggle_directed():
    g = st.session_state.sg
    g.set_directed(not g.directed)
    graph_changed("Graphe " + ("orienté." if g.directed else "non orienté (arcs symétrisés)."))


def cb_load():
    f = st.session_state.get("sg_upload")
    if f is None:
        return
    try:
        st.session_state.sg = Graph.from_dict(json.load(f))
        graph_changed("Graphe chargé.")
    except ValueError as e:                       # inclut json.JSONDecodeError
        graph_changed(f"Fichier invalide : {e}", "err")


# ----------------------------------------------------------------------
# Dessin du graphe (DOT, rendu par Streamlit — aucune dépendance supplémentaire)
# ----------------------------------------------------------------------
def draw_graph(g, step=None):
    """Graphe (et état d'une étape de recherche) -> source DOT."""
    expanded = set(step.expanded) if step else set()
    frontier = set(step.frontier_nodes) if step else set()
    current = step.current if step else None
    path = (step.path or []) if step else []
    path_edges = set(zip(path, path[1:])) | (set(zip(path[1:], path)) if not g.directed else set())
    out = ['digraph G {', 'rankdir=LR; bgcolor="transparent"; nodesep=0.5; ranksep=0.7;',
           'node [shape=circle, style=filled, fontname="Georgia", fontsize=12, color="#1c2230", '
           'fillcolor="#fffdf8", fontcolor="#1c2230", penwidth=1.4];',
           'edge [fontname="Georgia", fontsize=11, color="#6b6558", fontcolor="#1c2230"'
           + ('' if g.directed else ', dir=none') + '];']
    for n in g.nodes:
        fill, font, border = "#fffdf8", "#1c2230", "#1c2230"
        if n in frontier:
            fill, border = "#f7e8cf", "#b5651d"
        if n in expanded:
            fill, border = "#cfe3e6", "#0f4c5c"
        if n == current:
            fill, font, border = "#b5651d", "#ffffff", "#b5651d"
        if n in path:
            fill, font, border = "#2d6a4f", "#ffffff", "#2d6a4f"
        shape = "box" if n == g.start else "doublecircle" if n == g.goal else "circle"
        style = "filled,rounded" if n == g.start else "filled"
        label = n + (f"\\nh={fmt(g.h[n])}" if n in g.h else "")
        out.append(f'"{n}" [label="{label}", shape={shape}, style="{style}", fillcolor="{fill}", '
                   f'fontcolor="{font}", color="{border}"];')
    for u, v, w in g.edge_list(unique=True):
        on = (u, v) in path_edges
        out.append(f'"{u}" -> "{v}" [label="{fmt(w)}"'
                   + (', color="#2d6a4f", penwidth=3, fontcolor="#2d6a4f"' if on else '') + '];')
    out.append("}")
    return "\n".join(out)


def graph_panel(g, step=None):
    if not g.nodes:
        note("Le graphe est vide : ajoutez des sommets dans l'onglet « Graphe ».")
        return
    st.graphviz_chart(draw_graph(g, step), **stretch(st.graphviz_chart))
    st.markdown('<div class="legend">Départ : carré arrondi · Objectif : double cercle · '
                'h(n) : sous le nom du sommet · explorés : bleu · frontière : beige · '
                'sommet courant : orange · chemin final : vert.</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Onglet 01 — Construction du graphe
# ----------------------------------------------------------------------
def edit_nodes(g):
    with st.form("f_add_node", clear_on_submit=True):
        name = st.text_input("Nom du nouveau sommet", placeholder="ex. A")
        ok = st.form_submit_button("Ajouter le sommet", type="primary")
    if ok:
        attempt(lambda: g.add_node(name), f"Sommet {name.strip()} ajouté.")
    if g.nodes:
        with st.form("f_ren_node", clear_on_submit=True):
            old = st.selectbox("Sommet à renommer", g.nodes)
            new = st.text_input("Nouveau nom")
            ok = st.form_submit_button("Renommer")
        if ok:
            attempt(lambda: g.rename_node(old, new), f"Sommet {old} renommé en {new.strip()}.")
        with st.form("f_del_node"):
            victim = st.selectbox("Sommet à supprimer", g.nodes)
            ok = st.form_submit_button("Supprimer le sommet")
        if ok:
            attempt(lambda: g.remove_node(victim), f"Sommet {victim} supprimé, avec ses arcs.")


def quick_edges(g):
    """Saisie rapide : une ligne « origine destination [coût] » ; les sommets manquants sont créés."""
    with st.form("f_quick"):
        text = st.text_area("Saisie rapide d'arcs (une ligne : origine destination coût)",
                            placeholder="S A 2\nS B 5\nA G 4", height=110)
        ok = st.form_submit_button("Ajouter ces arcs")
    if not ok:
        return
    tmp = copy.deepcopy(g)                       # atomique : tout ou rien
    try:
        for n, line in enumerate(text.strip().splitlines(), 1):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) not in (2, 3):
                raise ValueError(f"Ligne {n} invalide : « {line} » (format : origine destination [coût]).")
            for x in parts[:2]:
                if x not in tmp.nodes:
                    tmp.add_node(x)
            tmp.add_edge(parts[0], parts[1], parts[2] if len(parts) == 3 else 1)
    except ValueError as e:
        st.error(str(e))
        return
    st.session_state.sg = tmp
    graph_changed("Arcs ajoutés.")
    st.rerun()


def edit_edges(g):
    if len(g.nodes) >= 2:
        with st.form("f_add_edge"):
            c1, c2, c3 = st.columns(3)
            u = c1.selectbox("Origine", g.nodes)
            v = c2.selectbox("Destination", g.nodes, index=1)
            cost = c3.number_input("Coût", min_value=0.0, value=1.0, step=1.0)
            ok = st.form_submit_button("Ajouter / modifier l'arc", type="primary")
        if ok:
            attempt(lambda: g.add_edge(u, v, cost), f"Arc {u} → {v} enregistré (coût {fmt(float(cost))}).")
        edges = g.edge_list(unique=True)
        if edges:
            with st.form("f_del_edge"):
                e = st.selectbox("Arc à supprimer", edges,
                                 format_func=lambda x: f"{x[0]} {'→' if g.directed else '—'} {x[1]}  (coût {fmt(x[2])})")
                ok = st.form_submit_button("Supprimer l'arc")
            if ok:
                attempt(lambda: g.remove_edge(e[0], e[1]), f"Arc {e[0]} / {e[1]} supprimé.")
    else:
        note("Créez au moins deux sommets pour ajouter un arc (ou utilisez la saisie rapide).")
    quick_edges(g)


def edit_heuristic(g):
    if not g.nodes:
        note("Créez d'abord des sommets.")
        return
    st.caption("h(n) estime le coût restant de n jusqu'à l'objectif (utilisée par Gloutonne, A* et Hill climbing).")
    with st.form("f_h"):
        cols = st.columns(3)
        vals = {n: cols[i % 3].number_input(f"h({n})", min_value=0.0, step=1.0, value=float(g.h.get(n, 0.0)))
                for i, n in enumerate(g.nodes)}
        ok = st.form_submit_button("Enregistrer l'heuristique", type="primary")
    if ok:
        def save():
            for n, x in vals.items():
                g.set_heuristic(n, x)
        attempt(save, "Heuristique enregistrée.")


def edit_start_goal(g):
    if not g.nodes:
        note("Créez d'abord des sommets.")
        return
    with st.form("f_sg"):
        s = st.selectbox("État initial", g.nodes, index=g.nodes.index(g.start) if g.start in g.nodes else 0)
        t = st.selectbox("État objectif", g.nodes,
                         index=g.nodes.index(g.goal) if g.goal in g.nodes else len(g.nodes) - 1)
        ok = st.form_submit_button("Définir", type="primary")
    if ok:
        def save():
            g.set_start(s)
            g.set_goal(t)
        attempt(save, f"État initial = {s}, état objectif = {t}.")


def edit_files(g):
    st.markdown(f"**Type de graphe :** {'orienté' if g.directed else 'non orienté'}")
    st.button("Passer en " + ("non orienté" if g.directed else "orienté"), on_click=cb_toggle_directed,
              key="b_dir", **stretch(st.button))
    st.selectbox("Graphe d'exemple", list(EXAMPLES), key="ex_sel")
    c1, c2 = st.columns(2)
    c1.button("Charger l'exemple", on_click=cb_example, key="b_example", **stretch(st.button))
    c2.button("Graphe vide", on_click=cb_empty, key="b_empty", **stretch(st.button))
    st.download_button("Télécharger le graphe (JSON)", json.dumps(g.to_dict(), ensure_ascii=False, indent=2),
                       file_name="graphe.json", mime="application/json", **stretch(st.download_button))
    arcs = pd.DataFrame(g.edge_list(unique=True), columns=["origine", "destination", "cout"])
    st.download_button("Télécharger les arcs (CSV)", arcs.to_csv(index=False), file_name="arcs.csv",
                       mime="text/csv", **stretch(st.download_button))
    st.file_uploader("Charger un graphe (JSON)", type="json", key="sg_upload", on_change=cb_load)


def stats_block(g):
    s = g.stats()
    yn = lambda b: "—" if b is None else "Oui" if b else "Non"
    items = [(s["nodes"], "sommets"), (s["edges"], "arcs"), (f"{s['avg_degree']:.1f}", "degré moyen"),
             (yn(s["connected"]), "connexe"), (yn(s["goal_reachable"]), "objectif atteignable")]
    st.markdown('<div class="lab">Statistiques du graphe</div><div class="vstats">' + "".join(
        f'<div><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>' for n, l in items)
        + "</div>", unsafe_allow_html=True)





def builder_tab(g):
    section("01", "Construction du graphe", "sommets, arcs, coûts, heuristique, exemples")
    left, right = st.columns([5, 6], gap="large")
    with left:                                  # édition d'abord : le dessin reflète la modification
        t = st.tabs(["Sommets", "Arcs", "Heuristique", "Départ / but", "Exemples & fichiers"])
        with t[0]:
            edit_nodes(g)
        with t[1]:
            edit_edges(g)
        with t[2]:
            edit_heuristic(g)
        with t[3]:
            edit_start_goal(g)
        with t[4]:
            edit_files(g)
    with right:
        st.markdown('<div class="lab">Graphe construit</div>', unsafe_allow_html=True)
        graph_panel(g)


# ----------------------------------------------------------------------
# Onglet 02 — Recherche
# ----------------------------------------------------------------------
def chips(items, hl=None):
    return "".join(f'<span class="chip {"hl" if x == hl else ""}">{esc(x)}</span>' for x in items)


def search_verdict(g, run):
    res, spec = run["res"], ALGORITHMS[run["key"]]
    if res.found:
        main, css = "Chemin trouvé", ""
        sub = f"<code>{esc(' → '.join(res.path))}</code>"
    else:
        main, css = "Aucun chemin trouvé", "ko"
        sub = f"Aucun chemin de <code>{esc(g.start)}</code> à <code>{esc(g.goal)}</code> n'a été trouvé par cet algorithme."
    stats = [(fmt(res.cost) if res.found else "—", "coût total"), (res.n_expanded, "expansions"),
             (res.max_frontier, "frontière max"), (f"{res.time_ms:.2f}", "temps (ms)")]
    st.markdown(f'<div class="verdict {css}"><div class="vlabel">{esc(spec.name)}</div>'
                f'<div class="vmain">{esc(main)}</div><div class="vsub">{sub}</div></div>'
                '<div class="vstats">' + "".join(
                    f'<div><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>'
                    for n, l in stats) + "</div>", unsafe_allow_html=True)


def ledger(steps, upto):
    out = []
    for i, s in enumerate(steps[:upto]):
        if s.kind == "iter":
            out.append(f'<div class="cyc">{esc(s.text)}</div>')
            continue
        last = ' style="background:#f7e8cf"' if i == upto - 1 else ""
        out.append(f'<div class="st"{last}><span class="no">{s.n:02d}</span>'
                   f'<span class="tg {TAG_CSS[s.kind]}">{esc(TAGS[s.kind])}</span>'
                   f'<span class="tx">{esc(s.text)}</span></div>')
    st.markdown('<div class="led">' + "".join(out) + "</div>", unsafe_allow_html=True)


def live_panel(g, run, step):
    """Panneau de données en direct : Open / Close / ordre de parcours / f(n) / coût."""
    st.markdown('<div class="lab">Open list (frontière)</div>' +
                (chips(step.labels) or "<i>vide</i>"), unsafe_allow_html=True)
    st.markdown('<div class="lab">Close list (explorés)</div>' +
                (chips(step.expanded, step.current) or "<i>vide</i>"), unsafe_allow_html=True)
    order = " → ".join(step.expanded) or "—"
    st.markdown(f'<div class="lab">Ordre de parcours</div><div class="formula">{esc(order)}</div>',
                unsafe_allow_html=True)
    cur, gc = step.current, step.g
    if cur is not None and gc is not None:
        if ALGORITHMS[run["key"]].needs_h:
            hv = g.h_of(cur)
            txt = f"f({cur}) = g + h = {fmt(gc)} + {fmt(hv)} = {fmt(gc + hv)}"
        else:
            txt = f"g({cur}) = {fmt(gc)}"
        st.markdown(f'<div class="lab">Sommet courant</div><div class="formula">{esc(txt)}<br>'
                    f'Coût du chemin jusqu\'ici : {esc(fmt(gc))}</div>', unsafe_allow_html=True)
    if step.path:
        st.markdown('<div class="lab">Chemin trouvé</div><div class="formula">' +
                    esc(" → ".join(step.path)) + "</div>", unsafe_allow_html=True)


def frame(g, run, steps, idx):
    """Une image : graphe, panneau en direct et déroulé jusqu'à l'étape idx."""
    c1, c2 = st.columns([6, 5], gap="large")
    with c1:
        st.markdown('<div class="lab">Graphe à cette étape</div>', unsafe_allow_html=True)
        graph_panel(g, steps[idx - 1])
    with c2:
        live_panel(g, run, steps[idx - 1])
    st.markdown('<div class="lab">Déroulé de la recherche</div>', unsafe_allow_html=True)
    ledger(steps, idx)


def steps_csv(run):
    rows = [{"etape": s.n, "type": s.kind, "description": s.text, "courant": s.current or "",
             "g": "" if s.g is None else s.g, "explores": " ".join(s.expanded),
             "frontiere": " | ".join(s.labels)} for s in run["res"].steps]
    return pd.DataFrame(rows).to_csv(index=False)


def step_viewer(g, run):
    steps, rid = run["res"].steps, run["id"]
    total = len(steps)

    if not steps:
        note("Aucune étape disponible pour cette recherche.", "err")
        return

    b = st.columns([1.2, 1.6])

    animate = b[0].button(
        "▶ Animer",
        key=f"anim_{rid}",
        **stretch(st.button)
    )


    if animate:
        ph = st.empty()
        seen = []

        for step in make_algorithm(
            run["key"], g, run["limit"]
        ).steps():

            seen.append(step)

            with ph.container():
                frame(g, run, seen, len(seen))


        ph.empty()

    # Affichage permanent de l'état final
    st.markdown(
        '<div class="lab">État final de la recherche</div>',
        unsafe_allow_html=True
    )

    frame(g, run, steps, total)

   



def runner_tab(g):
    section("02", "Recherche d'un chemin", "choisir une catégorie puis un algorithme")
    ss = st.session_state
    if g.start is None or g.goal is None:
        note("Définissez l'état initial et l'état objectif dans l'onglet « Graphe » (Départ / but).", "err")
        return
    cat = CATEGORIES[st.radio("Type de recherche", list(CATEGORIES), horizontal=True, key="s_cat")]
    keys = [k for k, s in ALGORITHMS.items() if s.category == cat]
    algo = st.selectbox("Algorithme", keys, format_func=lambda k: ALGORITHMS[k].name, key=f"s_algo_{cat}")
    spec = ALGORITHMS[algo]
    note(esc(spec.info))
    with st.expander("Fiche de l'algorithme"):
        st.markdown(f"**Complet :** {spec.complete}  \n**Optimal :** {spec.optimal}  \n"
                    f"**Temps :** {spec.time}  \n**Espace :** {spec.space}")
    limit = 3
    if spec.param == "limit":
        limit = int(st.number_input("Limite de profondeur (en nombre d'arcs)", min_value=0, value=3,
                                    step=1, key="s_limit"))
    st.markdown('<div class="lab">États</div>' + f'<span class="chip hl">Initial : {esc(g.start)}</span>'
                f'<span class="chip hl">Objectif : {esc(g.goal)}</span>', unsafe_allow_html=True)
    if spec.needs_h:
        missing = [n for n in g.nodes if n not in g.h]
        if missing:
            note("h(n) n'est pas définie pour " + esc(", ".join(missing)) + " : valeur 0 utilisée.", "err")

    if st.button("Lancer la recherche", type="primary", key="s_run"):
        ss.srun_counter += 1
        ss.sres = {"id": ss.srun_counter, "key": algo, "limit": limit, "res": run_search(algo, g, limit)}
    run = ss.sres
    if run is None:
        return
    if run["key"] != algo:
        note(f"Résultat affiché pour l'algorithme précédent ({esc(ALGORITHMS[run['key']].name)}). "
             "Relancez pour le nouvel algorithme.", "err")
    search_verdict(g, run)
    step_viewer(g, run)


# ----------------------------------------------------------------------
# Onglet 03 — Comparaison
# ----------------------------------------------------------------------
def compare_tab(g):
    section("03", "Comparaison des algorithmes", "même graphe, même départ, même objectif")
    if g.start is None or g.goal is None:
        note("Définissez l'état initial et l'état objectif dans l'onglet « Graphe ».", "err")
        return
    ss = st.session_state
    limit = int(st.number_input("Limite de profondeur pour DLS", min_value=0, value=3, step=1, key="c_limit"))
    if st.button("Comparer tous les algorithmes", type="primary", key="c_run"):
        ss.scmp = compare_all(g, limit)
    results = ss.scmp
    if not results:
        return
    costs = [r.cost for r in results if r.found]
    best = min(costs) if costs else None
    rows = []
    for r in results:
        opt = r.found and abs(r.cost - best) < 1e-9
        rows.append(f'<tr class="{"best" if opt else ""}"><td>{esc(ALGORITHMS[r.key].name)}</td>'
                    f'<td>{"Oui" if r.found else "Non"}</td>'
                    f'<td>{esc(" → ".join(r.path)) if r.found else "—"}</td>'
                    f'<td>{esc(fmt(r.cost)) if r.found else "—"}</td><td>{r.n_expanded}</td>'
                    f'<td>{r.max_frontier}</td><td>{r.time_ms:.3f}</td></tr>')
    st.markdown('<div class="lab">Résultats (en vert : coût minimal trouvé)</div>'
                '<table class="proof"><tr><th>Algorithme</th><th>Trouvé</th><th>Chemin</th><th>Coût</th>'
                '<th>Expansions</th><th>Frontière max</th><th>Temps (ms)</th></tr>' + "".join(rows) + "</table>",
                unsafe_allow_html=True)
    df = pd.DataFrame({"Algorithme": [ALGORITHMS[r.key].short for r in results],
                       "Expansions": [r.n_expanded for r in results]}).set_index("Algorithme")
    st.markdown('<div class="lab">Nombre d\'expansions</div>', unsafe_allow_html=True)
    st.bar_chart(df)
    if g.heuristic_report()["missing"]:
        note("L'heuristique n'est pas définie pour tous les sommets (valeur 0 utilisée par les algorithmes informés).", "err")


# ----------------------------------------------------------------------
# Point d'entrée du module
# ----------------------------------------------------------------------
def run_search_module():
    init_search_state()
    g = st.session_state.sg
    theme()
    st.markdown(
        '<div class="mast"><div><div class="over" style="margin:20px">Algorithmes de recherche · Espaces d\'états</div>'
        '<div class="title">Quel chemin suivre ?</div></div>', unsafe_allow_html=True)
    show_flash()
    t1, t2, t3 = st.tabs(["01 · Graphe", "02 · Recherche", "03 · Comparaison"])
    with t1:
        builder_tab(g)
    with t2:
        runner_tab(g)
    with t3:
        compare_tab(g)
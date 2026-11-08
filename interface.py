"""
interface.py — Interface Streamlit du module « Systèmes experts » (version éditoriale).

    streamlit run interface.py

Architecture : trois zones distinctes
  Barre latérale : faits de départ (modifiés en direct), scénarios types, base de connaissances
  Fenêtre modale : gestion des règles (consulter, ajouter, modifier, supprimer)
  Page principale : raisonnement uniquement
                    chaînage avant SANS but / chaînage arrière AVEC but
                    verdict, table de preuve, déroulé numéroté (rejouable étape par étape)
"""

import html
import inspect
import json
import os
import re
import sys

import streamlit as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import ExpertSystem, OPERATORS          # noqa: E402
from knowledge_base import RULES, FACTS_SCHEMA      # noqa: E402

SAVE_FILE = "base_connaissances.json"

PRESETS = {
    "SUARL": dict(nombre_associes=1, capital=1000, parts_sociales=True,
                  actions=False, appel_public_epargne=False),
    "SARL": dict(nombre_associes=5, capital=5000, parts_sociales=True,
                 actions=False, appel_public_epargne=False),
    "SA": dict(nombre_associes=10, capital=10000, parts_sociales=False,
               actions=True, appel_public_epargne=False),
    "SA avec appel public à l'épargne": dict(nombre_associes=10, capital=60000,
                                             parts_sociales=False, actions=True,
                                             appel_public_epargne=True),
}
MANUAL = "Saisie manuelle"

LEVELS = {
    1: "Niveau 1 — Faits intermédiaires",
    2: "Niveau 2 — Formes candidates",
    3: "Niveau 3 — Identification finale",
    0: "Règles personnalisées",
}

TAGS = {"info": "Méthode", "fire": "Déduit", "skip": "Déjà connu", "success": "Succès",
        "fail": "Échec", "goal": "But", "try": "Essai", "check": "Test"}

CSS = """
<style>
.stApp {background:#f4efe6;}
.block-container {padding-top:1.3rem; max-width:1280px;}
section[data-testid="stSidebar"] {background:#ebe4d4; border-right:1px solid #1c2230;}
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
.side-title {font-family:Georgia,serif; font-size:1.35rem; font-weight:700; color:#1c2230;
  border-bottom:1px solid #1c2230; padding-bottom:5px; margin:2px 0 12px 0;}
.lvl {font-size:.68rem; letter-spacing:.22em; text-transform:uppercase; color:#6b6558;
  margin:20px 0 6px 0; border-bottom:1px dashed #cfc4ad; padding-bottom:3px;}
.rule {display:grid; grid-template-columns:56px minmax(0,1fr); gap:8px; background:#fffdf8;
  border:1px solid #ddd3bf; border-radius:3px; padding:10px 12px; margin:6px 0 2px 0;}
.rule .rid {font-family:Georgia,serif; font-size:1.35rem; font-weight:700; color:#b5651d;}
.rule .rb {color:#1c2230; line-height:1.9; font-size:.9rem; min-width:0; overflow-wrap:break-word;}
.rule code {background:#efe8d8; color:#1c2230; padding:1px 7px; border-radius:3px; font-size:.8rem; white-space:nowrap;}
.kw {font-size:.66rem; letter-spacing:.16em; font-weight:700; color:#0f4c5c; margin:0 6px;}
.concl {font-family:Georgia,serif; font-style:italic; font-weight:700; color:#0f4c5c; font-size:1rem;}
.desc {color:#6b6558; font-size:.76rem; line-height:1.3;}
.note {border-left:4px solid #b5651d; background:#efe8d8; padding:9px 14px; font-size:.88rem;
  color:#1c2230; margin:8px 0;}
.note.err {border-left-color:#c0392b;}
.note.good {border-left-color:#2d6a4f;}
.verdict {background:#1c2230; color:#f4efe6; padding:26px 32px; border-left:12px solid #2d6a4f;
  margin:14px 0 0 0;}
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
.base {background:#fffdf8; border:1px solid #ddd3bf; padding:14px 18px; color:#1c2230;
  font-size:.92rem; line-height:1.6;}
table.proof {width:100%; border-collapse:collapse; background:#fffdf8; font-size:.85rem; color:#1c2230;}
table.proof th {text-align:left; font-size:.64rem; letter-spacing:.18em; text-transform:uppercase;
  color:#6b6558; border-bottom:2px solid #1c2230; padding:7px 10px;}
table.proof td {border-bottom:1px solid #ddd3bf; padding:9px 10px; vertical-align:top; color:#1c2230;}
table.proof tr.goal td {background:#f7e8cf; font-weight:700;}
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
</style>
"""


# ----------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------
def stretch(fn):
    """Largeur 100 % compatible avec les anciennes et nouvelles versions de Streamlit."""
    return {"width": "stretch"} if "width" in inspect.signature(fn).parameters \
        else {"use_container_width": True}


def esc(x):
    return html.escape(str(x))


def parse_value(text):
    t = text.strip()
    if t.lower() in ("true", "vrai"):
        return True
    if t.lower() in ("false", "faux"):
        return False
    for cast in (int, float):
        try:
            return cast(t)
        except ValueError:
            pass
    return t


def parse_conditions(text):
    conds = []
    for n, line in enumerate(text.strip().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 3 or parts[1] not in OPERATORS:
            raise ValueError(f"Ligne {n} invalide : « {line} ». Format : fait opérateur valeur "
                             f"(opérateurs : {' '.join(OPERATORS)}).")
        conds.append({"fact": parts[0], "operator": parts[1], "value": parse_value(parts[2])})
    if not conds:
        raise ValueError("Une règle doit avoir au moins une condition.")
    return conds


def conds_to_text(rule):
    return "\n".join(f"{c['fact']} {c['operator']} {c['value']}" for c in rule["conditions"])


def next_rule_id(es):
    nums = [int(re.sub(r"\D", "", r["id"]) or 0) for r in es.rules]
    return f"R{max(nums, default=0) + 1}"


def section(num, title, sub=""):
    st.markdown(f'<div class="sec"><span class="num">{num}</span><span class="ttl">{esc(title)}</span>'
                f'<span class="sub">{esc(sub)}</span></div>', unsafe_allow_html=True)


def note(text, kind=""):
    st.markdown(f'<div class="note {kind}">{text}</div>', unsafe_allow_html=True)


def frag_rerun():
    """Relance uniquement le contenu de la fenêtre modale (elle reste ouverte)."""
    try:
        st.rerun(scope="fragment")
    except TypeError:
        st.rerun()


# ----------------------------------------------------------------------
# État de session
# ----------------------------------------------------------------------
def new_es():
    return ExpertSystem(RULES, PRESETS["SARL"])


def invalidate_results():
    st.session_state.fwd = None
    st.session_state.bwd = None


def init_state():
    if "es" not in st.session_state:
        st.session_state.es = new_es()
        st.session_state.run_counter = 0
        st.session_state.flash = None
        st.session_state.dlg_flash = None
        invalidate_results()
        for k, v in PRESETS["SARL"].items():
            st.session_state[f"fact_{k}"] = v


def flash(msg, kind="good"):
    st.session_state.flash = (kind, msg)


def show_flash():
    if st.session_state.get("flash"):
        kind, msg = st.session_state.flash
        note(esc(msg), kind)
        st.session_state.flash = None


# Callbacks : exécutés avant le rerun, donc autorisés à modifier les clés des widgets
def apply_preset(name):
    for k, v in PRESETS[name].items():
        st.session_state[f"fact_{k}"] = v


def on_preset():
    choice = st.session_state.get("preset_sel")
    if choice in PRESETS:
        apply_preset(choice)
        st.session_state.preset_sel = MANUAL


def reset_kb():
    st.session_state.es = new_es()
    apply_preset("SARL")
    invalidate_results()
    flash("Base d'origine restaurée.")


def load_kb():
    f = st.session_state.get("kb_upload")
    if f is None:
        return
    try:
        data = json.load(f)
        es = st.session_state.es
        es.facts = data.get("facts", {})
        es.rules = data.get("rules", [])
        es.reset()
        for name, info in FACTS_SCHEMA.items():
            if name in es.facts:
                v = es.facts[name]
                st.session_state[f"fact_{name}"] = bool(v) if info["type"] is bool else int(v)
        invalidate_results()
        flash("Base de connaissances chargée.")
    except (ValueError, AttributeError, TypeError) as e:
        flash(f"Fichier invalide : {e}", "err")


def save_kb_disk():
    st.session_state.es.save(SAVE_FILE)
    flash(f"Base sauvegardée dans {SAVE_FILE}.")


# ----------------------------------------------------------------------
# Fenêtre modale : gestion des règles
# ----------------------------------------------------------------------
def make_dialog(title):
    """st.dialog (ou son ancien nom) ; le reste de la page est relancé à la fermeture."""
    d = getattr(st, "dialog", None) or getattr(st, "experimental_dialog")
    kwargs = {"width": "large"}
    if "on_dismiss" in inspect.signature(d).parameters:
        kwargs["on_dismiss"] = "rerun"
    return d(title, **kwargs)


def rule_card(es, r):
    conds = '<span class="kw">ET</span>'.join(f'<code>{esc(es.cond_to_str(c))}</code>'
                                             for c in r["conditions"])
    desc = f'<div class="desc">{esc(r["description"])}</div>' if r.get("description") else ""
    concl = esc(r["conclusion"]).replace("_", "_<wbr>")
    st.markdown(f'<div class="rule"><div class="rid">{esc(r["id"])}</div><div class="rb">'
                f'<span class="kw" style="margin-left:0">SI</span>{conds}'
                f'<span class="kw">ALORS</span><span class="concl">{concl}</span>'
                f'{desc}</div></div>', unsafe_allow_html=True)


def dlg_done(msg):
    invalidate_results()
    st.session_state.dlg_flash = msg
    frag_rerun()


@make_dialog("Base de règles")
def rules_dialog():
    es = st.session_state.es
    if st.session_state.get("dlg_flash"):
        note(esc(st.session_state.dlg_flash), "good")
        st.session_state.dlg_flash = None

    t_view, t_add, t_edit = st.tabs(["Consulter", "Ajouter une règle", "Modifier ou supprimer"])

    with t_view:
        q = st.text_input("Filtrer", placeholder="Filtrer par identifiant, fait ou conclusion",
                          key="rule_filter", label_visibility="collapsed")
        shown = [r for r in es.rules
                 if not q or q.lower() in (es.rule_to_str(r) + " " + r.get("description", "")).lower()]
        st.caption(f"{len(shown)} règle(s) affichée(s) sur {len(es.rules)}")
        for lvl in sorted({r.get("level", 0) for r in shown}, key=lambda l: (l == 0, l)):
            st.markdown(f'<div class="lvl">{esc(LEVELS.get(lvl, f"Niveau {lvl}"))}</div>',
                        unsafe_allow_html=True)
            for r in [x for x in shown if x.get("level", 0) == lvl]:
                rule_card(es, r)

    with t_add:
        with st.form("new_rule"):
            rid = st.text_input("Identifiant", value=next_rule_id(es))
            conds = st.text_area("Conditions, une par ligne (fait opérateur valeur)",
                                 placeholder="nombre_associes >= 2\nparts_sociales == true")
            concl = st.text_input("Conclusion")
            desc = st.text_input("Description")
            level = st.number_input("Niveau", min_value=0, step=1, value=0)
            if st.form_submit_button("Ajouter la règle", type="primary"):
                try:
                    if not rid.strip() or not concl.strip():
                        raise ValueError("Identifiant et conclusion obligatoires.")
                    es.add_rule({"id": rid.strip(), "level": int(level),
                                 "conditions": parse_conditions(conds),
                                 "conclusion": concl.strip(), "description": desc.strip()})
                    dlg_done(f"Règle {rid.strip()} ajoutée.")
                except ValueError as e:
                    st.error(str(e))

    with t_edit:
        if not es.rules:
            note("La base ne contient aucune règle.")
        else:
            rid = st.selectbox("Règle", [r["id"] for r in es.rules], key="edit_sel",
                               format_func=lambda i: f"{i} — {es.get_rule(i)['conclusion']}")
            r = es.get_rule(rid)
            rule_card(es, r)
            with st.form(f"edit_{rid}"):
                e_conds = st.text_area("Conditions", value=conds_to_text(r), key=f"ec_{rid}")
                e_concl = st.text_input("Conclusion", value=r["conclusion"], key=f"ek_{rid}")
                e_desc = st.text_input("Description", value=r.get("description", ""),
                                       key=f"ed_{rid}")
                e_lvl = st.number_input("Niveau", min_value=0, step=1,
                                        value=int(r.get("level", 0)), key=f"el_{rid}")
                b1, b2 = st.columns(2)
                save = b1.form_submit_button("Enregistrer", type="primary")
                delete = b2.form_submit_button("Supprimer cette règle")
                if save:
                    try:
                        if not e_concl.strip():
                            raise ValueError("La conclusion est obligatoire.")
                        es.update_rule(rid, {"id": rid, "level": int(e_lvl),
                                             "conditions": parse_conditions(e_conds),
                                             "conclusion": e_concl.strip(),
                                             "description": e_desc.strip()})
                        dlg_done(f"Règle {rid} modifiée.")
                    except ValueError as e:
                        st.error(str(e))
                if delete:
                    es.remove_rule(rid)
                    dlg_done(f"Règle {rid} supprimée.")

    if st.button("Terminer et fermer", type="primary", key="dlg_close"):
        st.rerun()


# ----------------------------------------------------------------------
# Barre latérale : faits de départ et base de connaissances
# ----------------------------------------------------------------------
def sidebar(es):
    with st.sidebar:
        st.markdown('<div class="side-title">Faits de départ</div>', unsafe_allow_html=True)
        st.selectbox("Scénario type", [MANUAL] + list(PRESETS), key="preset_sel",
                     on_change=on_preset)
        vals = {}
        for name, info in FACTS_SCHEMA.items():
            key = f"fact_{name}"
            if info["type"] is bool:
                vals[name] = st.toggle(info["description"], key=key)
            elif info["type"] is int:
                vals[name] = int(st.number_input(info["description"], min_value=0, step=1, key=key))
            else:
                vals[name] = int(st.number_input(info["description"], min_value=0, step=1000,
                                                 key=key))

       


    extras = {k: v for k, v in es.facts.items() if k not in FACTS_SCHEMA}
    new_facts = {**vals, **extras}
    if new_facts != es.facts:
        es.facts = new_facts
        es.reset()
        invalidate_results()


# ----------------------------------------------------------------------
# Résultats
# ----------------------------------------------------------------------
def snapshot(es, steps, goal=None):
    st.session_state.run_counter += 1
    return {"id": st.session_state.run_counter, "steps": steps, "goal": goal,
            "derivs": list(es.derivations), "fired": list(es.fired), "result": es.result,
            "facts": dict(es.facts),
            "derived": [k for k in es.working if k not in es.facts],
            "cycles": sum(1 for s in steps if s["type"] == "cycle")}


def stats_html(items):
    return '<div class="vstats">' + "".join(
        f'<div><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>'
        for n, l in items) + "</div>"


def forward_verdict(res):
    derived = res["derived"]
    forms = [d.replace("type_societe_", "") for d in derived if d.startswith("type_societe_")]
    if forms:
        main, css = f"Forme juridique : {' / '.join(forms)}", ""
    elif derived:
        main, css = f"{len(derived)} fait(s) déduit(s)", ""
    else:
        main, css = "Aucun fait déductible", "ko"
    sub = (f"Saturation atteinte : plus aucune règle ne peut s'appliquer ({res['cycles']} cycles)."
           if derived else "Aucune règle n'est applicable avec les faits de départ.")
    st.markdown(f'<div class="verdict {css}"><div class="vlabel">Résultat du chaînage avant</div>'
                f'<div class="vmain">{esc(main)}</div><div class="vsub">{esc(sub)}</div></div>'
                + stats_html([(len(derived), "faits déduits"), (len(res["fired"]), "règles déclenchées"),
                              (res["cycles"], "cycles")]), unsafe_allow_html=True)
    if derived:
        st.markdown('<div class="lab">Faits déduits</div>' + "".join(
            f'<span class="chip {"hl" if d.startswith("type_societe_") else ""}">{esc(d)}</span>'
            for d in derived), unsafe_allow_html=True)


def backward_verdict(res):
    goal, ok = res["goal"], res["result"]
    if ok:
        main, css = "But démontré", ""
        sub = f"<code>{esc(goal)}</code> est établi à partir des faits et des règles."
        if goal.startswith("type_societe_"):
            sub = f"La société est une {esc(goal.replace('type_societe_', ''))}."
    else:
        main, css = "But non démontré", "ko"
        sub = f"<code>{esc(goal)}</code> ne peut pas être établi avec les faits et règles actuels."
    st.markdown(f'<div class="verdict {css}"><div class="vlabel">Résultat du chaînage arrière</div>'
                f'<div class="vmain">{esc(main)}</div><div class="vsub">{sub}</div></div>'
                + stats_html([("Oui" if ok else "Non", "but démontré"),
                              (len(res["fired"]), "règles réussies"),
                              (len([s for s in res["steps"] if s["type"] != "cycle"]),
                               "étapes de preuve")]), unsafe_allow_html=True)


def proof_table(res, label):
    st.markdown(f'<div class="lab">{esc(label)}</div>', unsafe_allow_html=True)
    if not res["derivs"]:
        note("Aucune règle n'a pu être appliquée.")
        return
    rows = []
    for i, d in enumerate(res["derivs"], 1):
        prem = ", ".join(f"{esc(p)} = {esc(res['facts'][p])}" if p in res["facts"] else esc(p)
                         for p in d["premises"])
        cls = ' class="goal"' if res.get("goal") == d["conclusion"] else ""
        rows.append(f'<tr{cls}><td>{i:02d}</td><td><b>{esc(d["rule"])}</b></td><td>{prem}</td>'
                    f'<td>{esc(d["conclusion"])}</td></tr>')
    st.markdown('<table class="proof"><tr><th>N°</th><th>Règle</th><th>Conditions satisfaites</th>'
                '<th>Fait établi</th></tr>' + "".join(rows) + "</table>", unsafe_allow_html=True)


def ledger(res, kind):
    """Déroulé numéroté ; le curseur permet de le rejouer étape par étape."""
    steps = res["steps"]
    total = sum(1 for s in steps if s["type"] != "cycle")
    st.markdown('<div class="lab">Déroulé du raisonnement</div>', unsafe_allow_html=True)
    upto = total
    if total > 1:
        upto = st.slider("Afficher jusqu'à l'étape", 1, total, total, key=f"led_{kind}_{res['id']}")
    out, n = [], 0
    for s in steps:
        if s["type"] == "cycle":
            if n < upto:
                out.append(f'<div class="cyc">{esc(s["text"].strip("- "))}</div>')
            continue
        n += 1
        if n > upto:
            break
        text = "<br>".join(esc(line.strip()) for line in s["text"].split("\n"))
        row = (f'<div class="st"><span class="no">{n:02d}</span>'
               f'<span class="tg {s["type"]}">{esc(TAGS.get(s["type"], ""))}</span>'
               f'<span class="tx">{text}</span></div>')
        if s["depth"]:
            row = f'<div style="margin-left:{s["depth"] * 20}px;border-left:2px solid #d8cdb5">{row}</div>'
        out.append(row)
    st.markdown('<div class="led">' + "".join(out) + "</div>", unsafe_allow_html=True)


def show_result(res, kind, table_label):
    (forward_verdict if kind == "fwd" else backward_verdict)(res)
    c1, c2 = st.columns([6, 5], gap="large")
    with c1:
        proof_table(res, table_label)
    with c2:
        ledger(res, kind)


# ----------------------------------------------------------------------
# Page principale : raisonnement
# ----------------------------------------------------------------------
def base_panel(es):
    section("01", "Base de départ", "faits modifiables dans la barre latérale")
    facts = "".join(f'<span class="chip">{esc(k)} = {esc(v)}</span>' for k, v in es.facts.items())
    levels = len({r.get("level", 0) for r in es.rules})
    c1, c2 = st.columns([4, 1], gap="large")
    c1.markdown(f'<div class="base"><b>Faits :</b> {facts}<br><b>Règles :</b> {len(es.rules)} règles '
                f'réparties en {levels} niveau(x), à consulter et modifier dans une fenêtre dédiée.</div>',
                unsafe_allow_html=True)
    if c2.button("Gérer les règles", key="open_rules", **stretch(st.button)):
        rules_dialog()


def reasoning_panel(es):
    section("02", "Raisonnement")
    mode = st.radio("Méthode", ["Chaînage avant", "Chaînage arrière"], horizontal=True,
                    key="mode", label_visibility="collapsed")

    if mode == "Chaînage avant":
        note("<b>Sans objectif.</b> On part des faits de départ et on applique toutes les règles "
             "possibles, cycle après cycle, jusqu'à saturation : le moteur découvre tout ce qui "
             "est déductible.")
        if st.button("Lancer le chaînage avant", type="primary", key="run_fwd"):
            es.reset()
            steps = list(es.forward_chaining())
            st.session_state.fwd = snapshot(es, steps)
        res = st.session_state.fwd
        if res is not None:
            show_result(res, "fwd", "Faits déduits, dans l'ordre d'application")
        return

    # Chaînage arrière : le seul avec un but
    note("<b>Avec objectif.</b> On part du fait à démontrer et on remonte : quelles règles le "
         "concluent, et que faut-il prouver pour les appliquer (sous-buts).")
    derived = sorted(es.derived_facts())
    names = derived + [n for n in es.all_facts_names() if n not in derived]
    idx = names.index("type_societe_SARL") if "type_societe_SARL" in names else 0
    c1, c2 = st.columns([3, 1])
    goal = c1.selectbox("Fait à démontrer", names, index=idx, key="bwd_goal")
    c2.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
    run = c2.button("Démontrer", type="primary", key="run_bwd", **stretch(st.button))
    if goal in es.facts:
        note(f"<code>{esc(goal)}</code> est déjà présent dans la base de faits "
             f"(valeur = {esc(es.facts[goal])}).")
    if run:
        es.reset()
        steps = list(es.backward_chaining(goal))
        st.session_state.bwd = snapshot(es, steps, goal)
    res = st.session_state.bwd
    if res is None:
        return
    if res["goal"] != goal:
        note(f"Résultat affiché pour l'objectif précédent (<code>{esc(res['goal'])}</code>). "
             "Relancez pour le nouvel objectif.", "err")
    show_result(res, "bwd", "Chaîne de preuve, des faits vers le but")


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------
def run_expert_system():
    init_state()
    es = st.session_state.es
    st.markdown(CSS, unsafe_allow_html=True)
    sidebar(es)
    st.markdown(
        '<div class="mast"><div><div class="over">Système expert · Droit des sociétés tunisiennes</div>'
        '<div class="title">Quelle forme juridique ?</div></div>', unsafe_allow_html=True)
    show_flash()
    base_panel(es)
    reasoning_panel(es)


if __name__ == "__main__":
    st.set_page_config(page_title="Quelle forme juridique ?", layout="wide",
                       initial_sidebar_state="expanded")
    run_expert_system()

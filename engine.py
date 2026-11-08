"""engine.py — Moteur d'inférence du système expert (version complète)."""

import copy
import json
import operator as op

OPERATORS = {
    "==": op.eq, "!=": op.ne,
    ">=": op.ge, "<=": op.le,
    ">": op.gt, "<": op.lt,
}


def step(type_, text, depth=0):
    """Une étape de raisonnement (utilisée par l'interface)."""
    return {"type": type_, "text": text, "depth": depth}


class ExpertSystem:
    def __init__(self, rules, facts=None):
        self.rules = copy.deepcopy(rules)
        self.facts = dict(facts or {})      # faits initiaux
        self.working = dict(self.facts)     # faits de travail (+ faits déduits)
        self.result = None
        self.fired = []                     # ids des règles déclenchées
        self.derivations = []               # [{"rule", "premises", "conclusion"}] -> sert au graphe

    # ------------------------------------------------------------------
    # Outils
    # ------------------------------------------------------------------
    def reset(self):
        self.working = dict(self.facts)
        self.result = None
        self.fired = []
        self.derivations = []

    def derived_facts(self):
        return {r["conclusion"] for r in self.rules}

    def all_facts_names(self):
        names = set(self.facts) | self.derived_facts()
        for r in self.rules:
            names |= {c["fact"] for c in r["conditions"]}
        return sorted(names)

    def get_rule(self, rule_id):
        for r in self.rules:
            if r["id"] == rule_id:
                return r
        return None

    @staticmethod
    def cond_to_str(cond):
        return f"{cond['fact']} {cond['operator']} {cond['value']}"

    def rule_to_str(self, rule):
        conds = " ET ".join(self.cond_to_str(c) for c in rule["conditions"])
        return f"{rule['id']}: SI {conds} ALORS {rule['conclusion']}"

    def check_condition(self, cond, facts):
        """Retourne (ok, valeur). Fait absent : (False, None)."""
        name = cond["fact"]
        if name not in facts:
            return False, None
        try:
            return OPERATORS[cond["operator"]](facts[name], cond["value"]), facts[name]
        except TypeError:
            return False, facts[name]

    def _record(self, rule):
        """Enregistre une inférence réussie (pour le graphe d'explication)."""
        premises = list(dict.fromkeys(c["fact"] for c in rule["conditions"]))
        self.derivations.append({"rule": rule["id"], "premises": premises,
                                 "conclusion": rule["conclusion"]})

    # ------------------------------------------------------------------
    # Gestion de la base de connaissances
    # ------------------------------------------------------------------
    def set_fact(self, name, value):
        self.facts[name] = value

    def remove_fact(self, name):
        return self.facts.pop(name, None) is not None

    def add_rule(self, rule):
        if self.get_rule(rule["id"]):
            raise ValueError(f"La règle {rule['id']} existe déjà.")
        self.rules.append(rule)

    def update_rule(self, rule_id, new_rule):
        for i, r in enumerate(self.rules):
            if r["id"] == rule_id:
                self.rules[i] = new_rule
                return True
        return False

    def remove_rule(self, rule_id):
        before = len(self.rules)
        self.rules = [r for r in self.rules if r["id"] != rule_id]
        return len(self.rules) < before

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"facts": self.facts, "rules": self.rules}, f,
                      ensure_ascii=False, indent=2)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.facts = data.get("facts", {})
        self.rules = data.get("rules", [])
        self.reset()

    # ------------------------------------------------------------------
    # Chaînage AVANT — SANS but : on sature la base de faits
    # ------------------------------------------------------------------
    def forward_chaining(self, goal=None):
        """
        Chaînage avant dirigé par les données. Sans but, il déduit TOUT ce qui
        est déductible et s'arrête au point fixe (un cycle sans nouveau fait).
        (Un `goal` optionnel est accepté : le moteur s'arrête alors dès qu'il
        est atteint — l'interface ne l'utilise pas.)
        """
        self.reset()
        used = set()
        cycle = 0
        yield step("info", "Chaînage AVANT — saturation de la base de faits (sans but)"
                   if goal is None else f"Chaînage AVANT — but : {goal}")

        if goal is not None and goal in self.working:
            yield step("success", f"Le but '{goal}' est déjà dans la base de faits.")
            self.result = True
            return

        while True:
            cycle += 1
            yield step("cycle", f"--- Cycle {cycle} ---")
            new_fact = False

            for rule in self.rules:
                if rule["id"] in used:
                    continue
                results = [self.check_condition(c, self.working) for c in rule["conditions"]]
                if not all(ok for ok, _ in results):
                    continue

                used.add(rule["id"])
                concl = rule["conclusion"]
                detail = ", ".join(f"{c['fact']}={v}"
                                   for c, (_, v) in zip(rule["conditions"], results))

                if concl in self.working:
                    yield step("skip", f"{rule['id']} applicable ({detail}) "
                                       f"mais '{concl}' est déjà connu.", 1)
                    continue

                self.working[concl] = True
                self.fired.append(rule["id"])
                self._record(rule)
                new_fact = True
                yield step("fire", f"{rule['id']} déclenchée : {self.rule_to_str(rule)}\n"
                                   f"    conditions vérifiées : {detail}\n"
                                   f"    => nouveau fait : {concl} = True", 1)

                if goal is not None and concl == goal:
                    yield step("success", f"But atteint : '{goal}' a été déduit.")
                    self.result = True
                    return

            if not new_fact:
                derived = [k for k in self.working if k not in self.facts]
                if goal is None:
                    yield step("success", f"Point fixe atteint : {len(derived)} fait(s) déduit(s).")
                    self.result = bool(derived)
                else:
                    yield step("fail", f"Aucune nouvelle règle applicable : "
                                       f"'{goal}' ne peut pas être démontré.")
                    self.result = False
                return

    # ------------------------------------------------------------------
    # Chaînage ARRIÈRE — le seul qui possède un but
    # ------------------------------------------------------------------
    def backward_chaining(self, goal):
        self.reset()
        yield step("info", f"Chaînage ARRIÈRE — but : {goal}")
        self.result = yield from self._prove(goal, 0, [])
        if self.result:
            yield step("success", f"But '{goal}' DÉMONTRÉ.")
        else:
            yield step("fail", f"But '{goal}' NON démontré.")

    def _prove(self, goal, depth, stack):
        yield step("goal", f"But : {goal} ?", depth)

        if goal in self.working:
            yield step("success", f"'{goal}' est déjà dans la base de faits "
                                  f"(valeur = {self.working[goal]}).", depth + 1)
            return True

        if goal in stack:
            yield step("fail", f"Cycle détecté sur '{goal}' : branche abandonnée.", depth + 1)
            return False

        candidates = [r for r in self.rules if r["conclusion"] == goal]
        if not candidates:
            yield step("fail", f"Aucune règle ne conclut '{goal}' et le fait est "
                               f"absent de la base : non prouvable.", depth + 1)
            return False

        stack = stack + [goal]
        for rule in candidates:
            yield step("try", f"Essai de {self.rule_to_str(rule)}", depth + 1)
            all_ok = True
            for cond in rule["conditions"]:
                ok = yield from self._prove_condition(cond, depth + 2, stack)
                if not ok:
                    all_ok = False
                    yield step("fail", f"Condition non satisfaite -> {rule['id']} échoue.",
                               depth + 2)
                    break
            if all_ok:
                self.working[goal] = True
                self.fired.append(rule["id"])
                self._record(rule)
                yield step("fire", f"{rule['id']} réussie => '{goal}' est établi.", depth + 1)
                return True
        return False

    def _prove_condition(self, cond, depth, stack):
        name = cond["fact"]
        if name in self.derived_facts() and name not in self.facts:
            proved = yield from self._prove(name, depth, stack)
            if not proved:
                return False
            return OPERATORS[cond["operator"]](True, cond["value"])

        ok, val = self.check_condition(cond, self.working)
        if val is None:
            yield step("fail", f"Fait '{name}' inconnu : {self.cond_to_str(cond)} "
                               f"impossible à vérifier.", depth)
        else:
            yield step("check", f"Test {self.cond_to_str(cond)} avec {name} = {val} "
                                f"-> {'OK' if ok else 'ÉCHEC'}", depth)
        return ok
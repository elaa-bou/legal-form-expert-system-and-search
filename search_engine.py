"""
search_engine.py — Module 2 : algorithmes de recherche dans un espace d'états.

Organisation (aucune dépendance à Streamlit) :
  1. Graph            : données seulement — sommets, arcs orientés pondérés, h(n), départ, objectif
  2. Step, SearchResult, Node : ce que le moteur produit
  3. SearchAlgorithm  : un algorithme = un générateur d'étapes (exécution progressive)
     FrontierSearch   : boucle commune à BFS / DFS / UCS / Gloutonne / A*
     (seule la structure de frontière change : file, pile, file de priorité sur g, h ou g+h)
  4. ALGORITHMS, run_search, compare_all, graphes d'exemple
"""
import heapq
import itertools
import json
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

INF = float("inf")
EPS = 1e-12
NAME_RE = re.compile(r"^[\w\-]{1,20}$")


def fmt(x):
    """Affichage compact d'un nombre (3.0 -> '3', 2.5 -> '2.5')."""
    if isinstance(x, float):
        if x == INF:
            return "∞"
        return str(int(x)) if x.is_integer() else f"{x:.2f}".rstrip("0").rstrip(".")
    return str(x)


# ----------------------------------------------------------------------
# Graphe orienté pondéré
# ----------------------------------------------------------------------
class Graph:
    def __init__(self):
        self.nodes = []        # sommets (ordre d'insertion = ordre d'exploration)
        self.edges = {}        # u -> {v: coût}
        self.h = {}            # heuristique h(n)
        self.directed = True   # False : chaque arc est symétrique (graphe non orienté)
        self.start = None
        self.goal = None

    # --- lecture -------------------------------------------------------
    def successors(self, n):
        return list(self.edges.get(n, {}).items())

    def predecessors(self, n):
        return [(u, d[n]) for u, d in self.edges.items() if n in d]

    def edge_list(self, unique=False):
        """Arcs (u, v, coût). unique=True : un seul arc par paire si le graphe est non orienté."""
        out, seen = [], set()
        for u, d in self.edges.items():
            for v, w in d.items():
                if unique and not self.directed:
                    if (v, u) in seen:
                        continue
                    seen.add((u, v))
                out.append((u, v, w))
        return out

    def h_of(self, n):
        return self.h.get(n, 0.0)

    def path_cost(self, path):
        return sum(self.edges[a][b] for a, b in zip(path, path[1:]))

    # --- modification --------------------------------------------------
    def add_node(self, name):
        name = name.strip()
        if not NAME_RE.match(name):
            raise ValueError("Nom invalide : 1 à 20 caractères (lettres, chiffres, _ ou -).")
        if name in self.nodes:
            raise ValueError(f"Le sommet « {name} » existe déjà.")
        self.nodes.append(name)
        self.edges[name] = {}

    def remove_node(self, name):
        if name not in self.nodes:
            return
        self.nodes.remove(name)
        self.edges.pop(name, None)
        for d in self.edges.values():
            d.pop(name, None)
        self.h.pop(name, None)
        if self.start == name:
            self.start = None
        if self.goal == name:
            self.goal = None

    def add_edge(self, u, v, cost):
        """Ajoute l'arc u -> v (ou met à jour son coût s'il existe déjà)."""
        if u not in self.nodes or v not in self.nodes:
            raise ValueError("Sommet inexistant.")
        if u == v:
            raise ValueError("Les boucles (arc d'un sommet vers lui-même) ne sont pas autorisées.")
        try:
            cost = float(cost)
        except (TypeError, ValueError):
            raise ValueError("Le coût doit être un nombre.")
        if cost != cost or cost < 0 or cost == INF:
            raise ValueError("Le coût doit être un nombre positif ou nul.")
        self.edges[u][v] = cost
        if not self.directed:
            self.edges[v][u] = cost

    def remove_edge(self, u, v):
        self.edges.get(u, {}).pop(v, None)
        if not self.directed:
            self.edges.get(v, {}).pop(u, None)

    def rename_node(self, old, new):
        new = new.strip()
        if old not in self.nodes:
            raise ValueError(f"Sommet inexistant : {old}")
        if new == old:
            return
        if not NAME_RE.match(new):
            raise ValueError("Nom invalide : 1 à 20 caractères (lettres, chiffres, _ ou -).")
        if new in self.nodes:
            raise ValueError(f"Le sommet « {new} » existe déjà.")
        self.nodes[self.nodes.index(old)] = new
        self.edges = {(new if u == old else u): {(new if v == old else v): w for v, w in d.items()}
                      for u, d in self.edges.items()}
        if old in self.h:
            self.h[new] = self.h.pop(old)
        self.start = new if self.start == old else self.start
        self.goal = new if self.goal == old else self.goal

    def set_directed(self, flag):
        """Bascule orienté / non orienté (vers non orienté : chaque arc est symétrisé, coût minimal.)"""
        self.directed = bool(flag)
        if not self.directed:
            for u, v, w in list(self.edge_list()):
                w2 = min(w, self.edges[v].get(u, w))
                self.edges[u][v] = self.edges[v][u] = w2

    def stats(self):
        n, e = len(self.nodes), len(self.edge_list(unique=True))
        out = {"nodes": n, "edges": e, "avg_degree": (e * (1 if self.directed else 2) / n) if n else 0.0,
               "connected": None, "goal_reachable": None}
        if n:
            adj = {x: set(self.edges[x]) for x in self.nodes}
            for u, d in self.edges.items():
                for v in d:
                    adj[v].add(u)
            seen, stack = {self.nodes[0]}, [self.nodes[0]]
            while stack:
                for v in adj[stack.pop()]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            out["connected"] = len(seen) == n
        if self.start is not None and self.goal is not None:
            seen, stack = {self.start}, [self.start]
            while stack:
                for v in self.edges[stack.pop()]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            out["goal_reachable"] = self.goal in seen
        return out

    def set_heuristic(self, n, value):
        if n not in self.nodes:
            raise ValueError(f"Sommet inexistant : {n}")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("L'heuristique doit être un nombre.")
        if value != value or value < 0 or value == INF:
            raise ValueError("L'heuristique doit être un nombre positif ou nul.")
        self.h[n] = value

    def set_start(self, n):
        if n is not None and n not in self.nodes:
            raise ValueError(f"Sommet inexistant : {n}")
        self.start = n

    def set_goal(self, n):
        if n is not None and n not in self.nodes:
            raise ValueError(f"Sommet inexistant : {n}")
        self.goal = n

    # --- sauvegarde ----------------------------------------------------
    def to_dict(self):
        return {"directed": self.directed, "nodes": list(self.nodes),
                "edges": [{"from": u, "to": v, "cost": w} for u, v, w in self.edge_list(unique=True)],
                "heuristics": dict(self.h), "start": self.start, "goal": self.goal}

    @classmethod
    def from_dict(cls, data):
        g = cls()
        try:
            g.directed = bool(data.get("directed", True))
            for n in data["nodes"]:
                g.add_node(str(n))
            for e in data.get("edges", []):
                g.add_edge(e["from"], e["to"], e["cost"])
            for n, v in data.get("heuristics", {}).items():
                g.set_heuristic(n, v)
            g.set_start(data.get("start"))
            g.set_goal(data.get("goal"))
        except (KeyError, TypeError, AttributeError) as e:
            raise ValueError(f"Structure de graphe invalide ({e!r}).")
        return g

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    # --- contrôle de l'heuristique ------------------------------------
    def true_costs(self):
        """h*(n) : coût optimal de chaque sommet vers l'objectif (Dijkstra inversé)."""
        if self.goal is None:
            return {}
        dist, heap = {self.goal: 0.0}, [(0.0, self.goal)]
        while heap:
            d, n = heapq.heappop(heap)
            if d > dist.get(n, INF):
                continue
            for u, w in self.predecessors(n):
                if d + w < dist.get(u, INF):
                    dist[u] = d + w
                    heapq.heappush(heap, (d + w, u))
        return dist

    def heuristic_report(self):
        """Admissibilité (h <= h*) et cohérence (h(u) <= c(u,v) + h(v))."""
        star = self.true_costs()
        rows = []
        for n in self.nodes:
            hv, hs = self.h.get(n), star.get(n, INF)
            rows.append({"node": n, "h": hv, "h_star": hs,
                         "admissible": None if hv is None else hv <= hs + EPS})
        bad = [(u, v, w) for u, v, w in self.edge_list()
               if u in self.h and v in self.h and self.h[u] > w + self.h[v] + EPS]
        return {"rows": rows, "admissible": all(r["admissible"] is not False for r in rows),
                "consistent": not bad, "bad_edges": bad,
                "missing": [n for n in self.nodes if n not in self.h]}


def example_graph():
    """Graphe d'exemple : BFS, UCS/A* et Glouton y donnent des résultats différents."""
    g = Graph()
    for n in "SABCDEGH":                     # H est isolé : sert à tester « aucun chemin »
        g.add_node(n)
    for u, v, w in [("S", "A", 1), ("S", "B", 4), ("A", "C", 3), ("A", "D", 6), ("B", "D", 2),
                    ("B", "E", 5), ("C", "G", 8), ("D", "G", 3), ("E", "G", 1)]:
        g.add_edge(u, v, w)
    for n, v in {"S": 8, "A": 8, "B": 5, "C": 7, "D": 3, "E": 1, "G": 0, "H": 2}.items():
        g.set_heuristic(n, v)
    g.set_start("S")
    g.set_goal("G")
    return g


# ----------------------------------------------------------------------
# Étapes et résultat (ce que le moteur « montre » à l'interface)
# ----------------------------------------------------------------------
@dataclass
class Step:
    """Un instantané de la recherche, produit une fois par étape."""
    n: int
    kind: str                       # info | expand | skip | iter | success | fail
    text: str
    current: Optional[str] = None   # sommet en cours d'expansion
    g: Optional[float] = None       # coût du chemin jusqu'au sommet courant
    expanded: list = field(default_factory=list)    # sommets explorés (Close list)
    frontier: list = field(default_factory=list)    # [(sommet, étiquette)] (Open list)
    path: Optional[list] = None     # chemin final (dernière étape seulement)

    @property
    def frontier_nodes(self):
        return list(dict.fromkeys(n for n, _ in self.frontier))

    @property
    def labels(self):
        return [lab for _, lab in self.frontier]


@dataclass
class SearchResult:
    key: str
    found: bool
    path: list
    cost: Optional[float]
    steps: list
    n_expanded: int
    max_frontier: int
    time_ms: float


@dataclass
class Node:
    """Nœud de recherche : sommet atteint, chemin parcouru, coût cumulé g."""
    name: str
    path: list
    cost: float = 0.0

    def child(self, v, w):
        return Node(v, self.path + [v], self.cost + w)


# ----------------------------------------------------------------------
# Classe de base : un algorithme = un générateur d'étapes
# ----------------------------------------------------------------------
class SearchAlgorithm:
    """
    Usage :  alg = BFS(graph);  for step in alg.steps(): ...
    Les étapes sont produites UNE PAR UNE (exécution progressive) ; à la fin,
    alg.path et alg.cost contiennent le résultat (None si aucun chemin).
    Les sous-classes n'écrivent que _search(), un générateur qui renvoie (chemin, coût) ou None.
    """
    key = name = short = category = info = ""
    needs_h = False
    param = None                    # "limit" si l'algorithme a un paramètre de profondeur
    complete = optimal = time = space = ""

    def __init__(self, graph, limit=3):
        if graph.start is None or graph.goal is None:
            raise ValueError("Définissez l'état initial et l'état objectif.")
        self.graph, self.start, self.goal, self.limit = graph, graph.start, graph.goal, limit
        self.expanded, self.n_expanded, self.cur_g = [], 0, None
        self.path = self.cost = None
        self._n, self._frontier = 0, []

    # --- outils pour les sous-classes ------------------------------------
    def expand(self, n, g=None):
        self.n_expanded += 1
        self.cur_g = g
        if n not in self.expanded:
            self.expanded.append(n)

    def step(self, text, kind="info", current=None, frontier=None, path=None):
        """frontier=None : reprend la frontière de l'étape précédente."""
        if frontier is not None:
            self._frontier = list(frontier)
        self._n += 1
        return Step(self._n, kind, text, current, self.cur_g if current is not None else None,
                    list(self.expanded), list(self._frontier), path)

    # --- à redéfinir -----------------------------------------------------
    def _search(self):
        raise NotImplementedError

    # --- exécution -------------------------------------------------------
    def steps(self):
        out = yield from self._search()
        if out is not None:
            self.path, self.cost = out
            yield self.step(f"Chemin trouvé : {' → '.join(self.path)} (coût total = {fmt(self.cost)}).",
                            "success", self.path[-1], path=self.path)
        else:
            yield self.step(f"Aucun chemin trouvé de {self.start} à {self.goal}.", "fail")


# ----------------------------------------------------------------------
# Famille « frontière » : une seule boucle, seule la structure de frontière change
# ----------------------------------------------------------------------
class FrontierSearch(SearchAlgorithm):
    """
    Boucle commune à BFS, DFS, UCS, Gloutonne et A* :
        extraire un nœud de la frontière -> test d'objectif -> développer -> ajouter les enfants.
    Chaque algorithme ne redéfinit que : init / push / pop / is_empty / view (structure de
    frontière), et éventuellement label / accept / skip_reason / order.
    """

    def init(self, root): raise NotImplementedError
    def push(self, node): raise NotImplementedError
    def pop(self): raise NotImplementedError
    def is_empty(self): raise NotImplementedError
    def view(self): raise NotImplementedError          # [(sommet, étiquette)]

    def label(self, node): return node.name
    def accept(self, child): return True                # faut-il ajouter cet enfant ?
    def skip_reason(self, node): return None            # None : on traite ; "" : on ignore en silence
    def order(self, children): return children

    def _search(self):
        root = Node(self.start, [self.start])
        self.init(root)
        yield self.step(f"Initialisation : frontière = {[lab for _, lab in self.view()]}",
                        frontier=self.view())
        while not self.is_empty():
            node = self.pop()
            reason = self.skip_reason(node)
            if reason is not None:
                if reason:
                    yield self.step(reason, "skip", node.name, self.view())
                continue
            self.expand(node.name, node.cost)
            if node.name == self.goal:
                return node.path, node.cost
            children = [c for c in (node.child(v, w) for v, w in self.graph.successors(node.name))
                        if self.accept(c)]
            for c in self.order(children):
                self.push(c)
            added = [self.label(c) for c in children]
            yield self.step(f"Expansion de {self.label(node)} : ajoute {added or 'aucun sommet'} "
                            f"à la frontière.", "expand", node.name, self.view())
        return None


class BFS(FrontierSearch):
    key, short, category, name = "bfs", "BFS", "uninformed", "BFS — Parcours en largeur"
    info = "Complet. Trouve le chemin ayant le moins d'arcs, pas forcément le moins coûteux."
    complete, optimal, time, space = "Oui", "Oui si coûts unitaires (moins d'arcs)", "O(b^d)", "O(b^d)"

    def init(self, root):
        self.queue, self.seen = deque([root]), {root.name}      # FIFO

    def push(self, node): self.queue.append(node)
    def pop(self): return self.queue.popleft()
    def is_empty(self): return not self.queue
    def view(self): return [(n.name, n.name) for n in self.queue]

    def accept(self, child):
        if child.name in self.seen:
            return False
        self.seen.add(child.name)
        return True


class DFS(FrontierSearch):
    key, short, category, name = "dfs", "DFS", "uninformed", "DFS — Parcours en profondeur"
    info = "Non optimal. Explore en profondeur ; les sommets déjà explorés ne sont pas repris."
    complete = "Oui (graphe fini, sommets explorés mémorisés)"
    optimal, time, space = "Non", "O(b^m)", "O(b·m)"

    def init(self, root): self.stack = [root]                   # LIFO

    def push(self, node): self.stack.append(node)
    def pop(self): return self.stack.pop()
    def is_empty(self): return not self.stack
    def view(self): return [(n.name, n.name) for n in self.stack]
    def order(self, children): return reversed(children)        # le 1er successeur sort en premier
    def accept(self, child): return child.name not in self.expanded

    def skip_reason(self, node):
        return f"{node.name} est déjà exploré : ignoré." if node.name in self.expanded else None


class BestFirst(FrontierSearch):
    """File de priorité sur f(n). UCS : f=g ; Gloutonne : f=h ; A* : f=g+h."""
    reopen = True                   # False : un sommet n'est jamais ré-évalué (Gloutonne)

    def priority(self, node): raise NotImplementedError

    def init(self, root):
        self.heap, self.counter, self.best = [], itertools.count(), {root.name: 0.0}
        self.push(root)

    def push(self, node):           # le compteur départage les égalités (premier arrivé, premier servi)
        heapq.heappush(self.heap, (self.priority(node), next(self.counter), node))

    def pop(self): return heapq.heappop(self.heap)[2]
    def is_empty(self): return not self.heap

    def view(self):
        return [(e[2].name, self.label(e[2])) for e in sorted(self.heap)
                if e[2].cost <= self.best[e[2].name] + EPS]

    def accept(self, child):
        if self.reopen:
            ok = child.cost < self.best.get(child.name, INF) - EPS    # chemin strictement meilleur
        else:
            ok = child.name not in self.best                          # jamais vu
        if ok:
            self.best[child.name] = child.cost
        return ok

    def skip_reason(self, node):    # entrée périmée : un meilleur chemin existe déjà
        return "" if node.cost > self.best[node.name] + EPS else None


class UCS(BestFirst):
    key, short, category, name = "ucs", "UCS", "uninformed", "UCS — Coût uniforme"
    info = "Développe toujours le sommet de plus petit coût cumulé g(n) : complet et optimal (coûts ≥ 0)."
    complete, optimal = "Oui (coûts ≥ 0)", "Oui"
    time = space = "O(b^(1+C*/ε))"

    def priority(self, node): return node.cost
    def label(self, node): return f"{node.name} (g={fmt(node.cost)})"


class Greedy(BestFirst):
    key, short, category, name = "greedy", "Glouton", "informed", "Gloutonne (Greedy best-first)"
    needs_h, reopen = True, False
    info = "Développe le sommet de plus petit h(n). Rapide, mais ni optimale ni toujours complète."
    complete, optimal, time, space = "Non en général", "Non", "O(b^m)", "O(b^m)"

    def priority(self, node): return self.graph.h_of(node.name)
    def label(self, node): return f"{node.name} (h={fmt(self.graph.h_of(node.name))})"


class AStar(BestFirst):
    key, short, category, name = "astar", "A*", "informed", "A*"
    needs_h = True
    info = "Développe le sommet de plus petit f(n) = g(n) + h(n) : optimal si h est admissible."
    complete, optimal = "Oui", "Oui si h admissible"
    time, space = "exponentiel dans le pire cas", "O(b^d)"

    def priority(self, node): return node.cost + self.graph.h_of(node.name)

    def label(self, node):
        h = self.graph.h_of(node.name)
        return f"{node.name} (f={fmt(node.cost + h)} = {fmt(node.cost)}+{fmt(h)})"


# ----------------------------------------------------------------------
# Autres algorithmes non informés
# ----------------------------------------------------------------------
class DLS(SearchAlgorithm):
    key, short, category, name = "dls", "DLS", "uninformed", "DLS — Profondeur limitée"
    param = "limit"
    info = "Coupe chaque branche à la limite fixée ; incomplet si la limite est trop faible."
    complete = "Non (si limite < profondeur de la solution)"
    optimal, time, space = "Non", "O(b^l)", "O(b·l)"

    def limited(self, limit):
        """Recherche en profondeur bornée ; renvoie (résultat, coupure). Évite les cycles du chemin courant."""
        stack, cutoff = [Node(self.start, [self.start])], False
        yield self.step(f"Initialisation : pile = [{self.start}], limite = {limit}",
                        frontier=[(n.name, n.name) for n in stack])
        while stack:
            node = stack.pop()
            self.expand(node.name, node.cost)
            view = lambda: [(n.name, n.name) for n in stack]
            if node.name == self.goal:
                return (node.path, node.cost), cutoff
            depth = len(node.path) - 1
            children = [node.child(v, w) for v, w in self.graph.successors(node.name) if v not in node.path]
            if depth >= limit:
                if children:
                    cutoff = True
                    yield self.step(f"{node.name} est à la profondeur {depth} = limite : coupure.",
                                    "skip", node.name, view())
                else:
                    yield self.step(f"{node.name} est une impasse.", "skip", node.name, view())
                continue
            stack.extend(reversed(children))
            yield self.step(f"Expansion de {node.name} (profondeur {depth}) : empile "
                            f"{[c.name for c in children] or 'aucun sommet'}.", "expand", node.name, view())
        return None, cutoff

    def _search(self):
        res, cutoff = yield from self.limited(self.limit)
        if res is None and cutoff:
            yield self.step("Échec par coupure : un chemin plus profond peut exister (augmentez la limite).",
                            "fail")
        return res


class IDS(DLS):
    key, short, name = "ids", "IDS", "IDS — Approfondissement itératif"
    param = None
    info = "Répète DLS avec une limite croissante : complet, optimal en nombre d'arcs, peu de mémoire."
    complete, optimal = "Oui", "Oui si coûts unitaires (moins d'arcs)"
    time, space = "O(b^d)", "O(b·d)"

    def _search(self):
        for lim in range(max(len(self.graph.nodes) - 1, 0) + 1):
            self.expanded.clear()
            yield self.step(f"Itération : limite de profondeur = {lim}", "iter", frontier=[])
            res, cutoff = yield from self.limited(lim)
            if res:
                return res
            if not cutoff:
                yield self.step("Aucune coupure : tout l'espace accessible est exploré, "
                                "il n'y a pas de chemin.", "fail")
                return None
        return None



# ----------------------------------------------------------------------
# Registre et exécution
# ----------------------------------------------------------------------
ALGORITHMS = {cls.key: cls for cls in (BFS, DFS, DLS, IDS, UCS, Greedy, AStar)}


def make_algorithm(key, graph, limit=3):
    """Crée l'algorithme ; ses étapes s'obtiennent avec .steps() (générateur)."""
    return ALGORITHMS[key](graph, limit)


def run_search(key, graph, limit=3):
    """Exécute l'algorithme jusqu'au bout et rassemble les étapes."""
    alg = make_algorithm(key, graph, limit)
    t0 = time.perf_counter()
    steps = list(alg.steps())
    dt = (time.perf_counter() - t0) * 1000
    return SearchResult(key, alg.path is not None, alg.path or [], alg.cost, steps, alg.n_expanded,
                        max((len(s.frontier) for s in steps), default=0), dt)


def compare_all(graph, limit=3):
    return [run_search(k, graph, limit) for k in ALGORITHMS]


# ----------------------------------------------------------------------
# Graphes d'exemple
# ----------------------------------------------------------------------
def _build(nodes, edges, h, start, goal, directed=True):
    g = Graph()
    g.directed = directed
    for n in nodes:
        g.add_node(n)
    for u, v, w in edges:
        g.add_edge(u, v, w)
    for n, x in h.items():
        g.set_heuristic(n, x)
    g.set_start(start)
    g.set_goal(goal)
    return g


def simple_path_graph():
    nodes = list("ABCDE")
    return _build(nodes, [(a, b, 1) for a, b in zip(nodes, nodes[1:])],
                  {n: 4 - i for i, n in enumerate(nodes)}, "A", "E")


def binary_tree_graph():
    nodes = [str(i) for i in range(1, 16)]
    edges = [(str(i), str(c), 1) for i in range(1, 8) for c in (2 * i, 2 * i + 1)]
    depth = lambda i: i.bit_length() - 1
    return _build(nodes, edges, {n: max(0, 3 - depth(int(n))) for n in nodes}, "1", "13")


def grid_graph():
    """Grille 4x4 non orientée avec deux obstacles (B2, C3) ; h = distance de Manhattan."""
    cells = [f"{r}{c}" for r in "ABCD" for c in range(1, 5) if f"{r}{c}" not in ("B2", "C3")]
    edges = []
    for r in "ABCD":
        for c in range(1, 5):
            a = f"{r}{c}"
            for b in (f"{r}{c + 1}", f"{chr(ord(r) + 1)}{c}"):
                if a in cells and b in cells:
                    edges.append((a, b, 1))
    h = {n: (ord("D") - ord(n[0])) + (4 - int(n[1])) for n in cells}
    return _build(cells, edges, h, "A1", "D4", directed=False)


def weighted_graph():
    return _build(list("SABCG"), [("S", "A", 7), ("S", "B", 2), ("B", "A", 3), ("B", "C", 8),
                                  ("A", "C", 1), ("C", "G", 4)],
                  {"S": 9, "A": 5, "B": 7, "C": 4, "G": 0}, "S", "G")


EXAMPLES = {"Exemple de comparaison (orienté)": example_graph, "Chemin simple": simple_path_graph,
            "Arbre binaire": binary_tree_graph, "Grille 4×4 (non orientée)": grid_graph,
            "Graphe pondéré": weighted_graph}
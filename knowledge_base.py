
# ============================================================
# KNOWLEDGE BASE
# Identification des formes juridiques des sociétés tunisiennes
# ============================================================

RULES = [

    # --------------------------------------------------------
    # LEVEL 1: Intermediate rules
    # Deriving facts from the initial information
    # --------------------------------------------------------

    {
        "id": "R1",
        "level": 1,
        "conditions": [
            {"fact": "nombre_associes", "operator": "==", "value": 1}
        ],
        "conclusion": "associe_unique",
        "description": "La société possède un seul associé."
    },

    {
        "id": "R2",
        "level": 1,
        "conditions": [
            {"fact": "nombre_associes", "operator": ">=", "value": 2}
        ],
        "conclusion": "pluralite_associes",
        "description": "La société possède plusieurs associés."
    },

    {
        "id": "R3",
        "level": 1,
        "conditions": [
            {"fact": "nombre_associes", "operator": ">=", "value": 2},
            {"fact": "nombre_associes", "operator": "<=", "value": 50}
        ],
        "conclusion": "nombre_associes_valide_sarl",
        "description": "Le nombre d'associés se situe entre 2 et 50."
    },

    {
        "id": "R4",
        "level": 1,
        "conditions": [
            {"fact": "nombre_associes", "operator": ">=", "value": 7}
        ],
        "conclusion": "nombre_actionnaires_suffisant",
        "description": "Le nombre d'actionnaires atteint au moins 7."
    },

    {
        "id": "R5",
        "level": 1,
        "conditions": [
            {"fact": "parts_sociales", "operator": "==", "value": True}
        ],
        "conclusion": "capital_divise_en_parts_sociales",
        "description": "Le capital est divisé en parts sociales."
    },

    {
        "id": "R6",
        "level": 1,
        "conditions": [
            {"fact": "actions", "operator": "==", "value": True}
        ],
        "conclusion": "capital_divise_en_actions",
        "description": "Le capital est divisé en actions."
    },

    {
        "id": "R7",
        "level": 1,
        "conditions": [
            {"fact": "capital", "operator": ">=", "value": 5000},
            {"fact": "appel_public_epargne", "operator": "==", "value": False}
        ],
        "conclusion": "capital_sa_suffisant_sans_appel_public",
        "description": "Le capital atteint le seuil prévu dans la base pour une SA sans appel public."
    },

    {
        "id": "R8",
        "level": 1,
        "conditions": [
            {"fact": "capital", "operator": ">=", "value": 50000},
            {"fact": "appel_public_epargne", "operator": "==", "value": True}
        ],
        "conclusion": "capital_sa_suffisant_avec_appel_public",
        "description": "Le capital atteint le seuil prévu dans la base pour une SA avec appel public."
    },


    # --------------------------------------------------------
    # LEVEL 2: Candidate legal forms
    # Combining intermediate facts
    # --------------------------------------------------------

    {
        "id": "R9",
        "level": 2,
        "conditions": [
            {"fact": "associe_unique", "operator": "==", "value": True},
            {"fact": "capital_divise_en_parts_sociales", "operator": "==", "value": True}
        ],
        "conclusion": "candidat_SUARL",
        "description": "Les caractéristiques correspondent à une SUARL."
    },

    {
        "id": "R10",
        "level": 2,
        "conditions": [
            {"fact": "pluralite_associes", "operator": "==", "value": True},
            {"fact": "nombre_associes_valide_sarl", "operator": "==", "value": True},
            {"fact": "capital_divise_en_parts_sociales", "operator": "==", "value": True}
        ],
        "conclusion": "candidat_SARL",
        "description": "Les caractéristiques correspondent à une SARL."
    },

    {
        "id": "R11",
        "level": 2,
        "conditions": [
            {"fact": "nombre_actionnaires_suffisant", "operator": "==", "value": True},
            {"fact": "capital_divise_en_actions", "operator": "==", "value": True},
            {"fact": "capital_sa_suffisant_sans_appel_public", "operator": "==", "value": True}
        ],
        "conclusion": "candidat_SA_sans_appel_public",
        "description": "Les caractéristiques correspondent à une SA sans appel public à l'épargne."
    },

    {
        "id": "R12",
        "level": 2,
        "conditions": [
            {"fact": "nombre_actionnaires_suffisant", "operator": "==", "value": True},
            {"fact": "capital_divise_en_actions", "operator": "==", "value": True},
            {"fact": "capital_sa_suffisant_avec_appel_public", "operator": "==", "value": True}
        ],
        "conclusion": "candidat_SA_avec_appel_public",
        "description": "Les caractéristiques correspondent à une SA avec appel public à l'épargne."
    },


    # --------------------------------------------------------
    # LEVEL 3: Final identification
    # Producing the final legal form
    # --------------------------------------------------------

    {
        "id": "R13",
        "level": 3,
        "conditions": [
            {"fact": "candidat_SUARL", "operator": "==", "value": True}
        ],
        "conclusion": "type_societe_SUARL",
        "description": "La forme juridique identifiée est SUARL."
    },

    {
        "id": "R14",
        "level": 3,
        "conditions": [
            {"fact": "candidat_SARL", "operator": "==", "value": True}
        ],
        "conclusion": "type_societe_SARL",
        "description": "La forme juridique identifiée est SARL."
    },

    {
        "id": "R15",
        "level": 3,
        "conditions": [
            {"fact": "candidat_SA_sans_appel_public", "operator": "==", "value": True}
        ],
        "conclusion": "type_societe_SA",
        "description": "La forme juridique identifiée est SA sans appel public à l'épargne."
    },

    {
        "id": "R16",
        "level": 3,
        "conditions": [
            {"fact": "candidat_SA_avec_appel_public", "operator": "==", "value": True}
        ],
        "conclusion": "type_societe_SA",
        "description": "La forme juridique identifiée est SA avec appel public à l'épargne."
    }
]


# ------------------------------------------------------------
# Initial facts expected from the user
# ------------------------------------------------------------

FACTS_SCHEMA = {
    "nombre_associes": {
        "type": int,
        "description": "Nombre d'associés ou d'actionnaires."
    },
    "capital": {
        "type": (int, float),
        "description": "Montant du capital social."
    },
    "parts_sociales": {
        "type": bool,
        "description": "Le capital est-il divisé en parts sociales ?"
    },
    "actions": {
        "type": bool,
        "description": "Le capital est-il divisé en actions ?"
    },
    "appel_public_epargne": {
        "type": bool,
        "description": "La société fait-elle appel public à l'épargne ?"
    }
}

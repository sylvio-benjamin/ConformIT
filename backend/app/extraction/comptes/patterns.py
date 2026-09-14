"""Faits comptes sociaux. attendu ≠ nécessaire."""

from __future__ import annotations

AMOUNT_LABELS = {
    "disponibilites": ("disponibilités", "banque", "caisse"),
    "creances_clients": ("créances clients", "creances clients"),
    "stocks": ("stocks",),
    "actif_circulant": ("actif circulant", "actif courant"),
    "dettes_fournisseurs": ("dettes fournisseurs", "fournisseurs"),
    "dettes_court_terme": ("dettes à court terme", "passif circulant"),
    "dettes_financieres": ("dettes financières", "emprunts"),
    "capitaux_propres": ("capitaux propres", "fonds propres"),
    "capitaux_propres_n1": ("capitaux propres n-1", "capitaux propres n−1"),
    "chiffre_affaires": ("chiffre d'affaires", "chiffre daffaires"),
    "chiffre_affaires_n1": ("chiffre d'affaires n-1",),
    "achats": ("achats de marchandises", "achats"),
    "resultat_net": ("résultat net", "bénéfice net"),
    "charges_financieres": ("charges financières",),
    "resultat_exploitation": ("résultat d'exploitation", "ebit"),
    "total_passif": ("total passif",),
}

# Un exercice unique doit les porter. Pas les séries N-1.
EXPECTED_FACTS = ("chiffre_affaires", "capitaux_propres")
AMBIGUOUS_FACTS = ("capitaux_propres_n1", "chiffre_affaires_n1")

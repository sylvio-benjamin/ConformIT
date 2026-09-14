"""
Module de calculs pour l'analyse de documents.
Exporte tous les modules de calcul pour faciliter les imports.
"""

from .calculs_base import (
    determiner_risque,
    is_positive,
    normaliser_score,
    calculer_precision,
    NiveauRisque
)

from .calculs_kbis import (
    analyser_et_calculer,
    calculer_score_total,
    calculer_score_rcs,
    calculer_score_forme_juridique,
    calculer_score_capital,
    calculer_score_adresse_stable,
    calculer_score_anciennete,
    calculer_score_commissaire_comptes,
    calculer_score_etablissements,
    calculer_score_duree_vie,
    calculer_score_date_activite,
    calculer_score_nationalite_dirigeants,
    calculer_score_adresse_dirigeants,
    determiner_niveau_risque
)

from .calculs_bilan import (
    calculer_score_bilan,
    extraire_valeurs_bilan,
    BilanParser
)

from .calculs_comptes_sociaux import (
    calculer_score_comptes_sociaux,
    extraire_valeurs_comptes_sociaux,
    ComptesSociauxParser
)

from .calculs_compte_resultat import calculer_score_compte_resultat
from .calculs_liasse import calculer_score_liasse
from .calculs_releve import calculer_score_releve
from .calculs_statuts import calculer_score_statuts
from .calculs_attestation import calculer_score_attestation
from .calculs_generique import calculer_score_generique

__all__ = [
    # Base
    "determiner_risque",
    "is_positive",
    "normaliser_score",
    "calculer_precision",
    "NiveauRisque",
    # Kbis
    "analyser_et_calculer",
    "calculer_score_total",
    "calculer_score_rcs",
    "calculer_score_forme_juridique",
    "calculer_score_capital",
    "calculer_score_adresse_stable",
    "calculer_score_anciennete",
    "calculer_score_commissaire_comptes",
    "calculer_score_etablissements",
    "calculer_score_duree_vie",
    "calculer_score_date_activite",
    "calculer_score_nationalite_dirigeants",
    "calculer_score_adresse_dirigeants",
    "determiner_niveau_risque",
    # Bilan
    "calculer_score_bilan",
    "extraire_valeurs_bilan",
    "BilanParser",
    # Comptes sociaux
    "calculer_score_comptes_sociaux",
    "extraire_valeurs_comptes_sociaux",
    "ComptesSociauxParser",
    # Autres
    "calculer_score_compte_resultat",
    "calculer_score_liasse",
    "calculer_score_releve",
    "calculer_score_statuts",
    "calculer_score_attestation",
    "calculer_score_generique",
]


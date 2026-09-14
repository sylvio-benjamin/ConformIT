"""
Tests unitaires pour le module calculs.py.

Ces tests vérifient que toutes les formules Excel sont correctement
implémentées en Python pur.
"""

import pytest
from app import (
    calculer_score_rcs,
    calculer_score_forme_juridique,
    calculer_score_capital,
    calculer_score_adresse_stable,
    calculer_score_anciennete,
    calculer_score_commissaire_comptes,
    calculer_score_taille_entreprise,
    calculer_score_duree_vie,
    calculer_score_derniere_modification,
    calculer_score_question_11,
    calculer_score_question_12,
    calculer_score_total,
    determiner_niveau_risque,
    calculer_precision,
    analyser_et_calculer,
    NiveauRisque
)


class TestCalculRCS:
    """Tests pour le calcul du score RCS."""
    
    def test_oui_retourne_0(self):
        assert calculer_score_rcs("Oui") == 0
        assert calculer_score_rcs("oui") == 0
        assert calculer_score_rcs(" OUI ") == 0
    
    def test_non_retourne_40(self):
        assert calculer_score_rcs("Non") == 40
        assert calculer_score_rcs("non") == 40
        assert calculer_score_rcs(" NON ") == 40
    
    def test_autre_retourne_0(self):
        assert calculer_score_rcs("") == 0
        assert calculer_score_rcs("Autre") == 0
        assert calculer_score_rcs(None) == 0


class TestCalculFormeJuridique:
    """Tests pour le calcul du score selon la forme juridique."""
    
    def test_sas_retourne_0(self):
        assert calculer_score_forme_juridique("SAS") == 0
        assert calculer_score_forme_juridique("sas") == 0
    
    def test_sa_retourne_1(self):
        assert calculer_score_forme_juridique("SA") == 1
        assert calculer_score_forme_juridique("sa") == 1
    
    def test_sarl_retourne_2(self):
        assert calculer_score_forme_juridique("SARL") == 2
    
    def test_eurl_retourne_3(self):
        assert calculer_score_forme_juridique("EURL") == 3
    
    def test_ei_retourne_4(self):
        assert calculer_score_forme_juridique("EI") == 4
        assert calculer_score_forme_juridique("Micro-entreprise") == 4
    
    def test_non_precise_retourne_4(self):
        assert calculer_score_forme_juridique("") == 4
        assert calculer_score_forme_juridique(None) == 4
        assert calculer_score_forme_juridique("Inconnu") == 4


class TestCalculCapital:
    """Tests pour le calcul du score selon le capital social."""
    
    def test_moins_10000_retourne_6(self):
        assert calculer_score_capital(5000) == 6
        assert calculer_score_capital(9999) == 6
        assert calculer_score_capital("5000 €") == 6
    
    def test_10000_50000_retourne_4(self):
        assert calculer_score_capital(10000) == 4
        assert calculer_score_capital(25000) == 4
        assert calculer_score_capital(50000) == 4
    
    def test_50001_200000_retourne_3(self):
        assert calculer_score_capital(50001) == 3
        assert calculer_score_capital(100000) == 3
        assert calculer_score_capital(200000) == 3
    
    def test_200001_500000_retourne_2(self):
        assert calculer_score_capital(200001) == 2
        assert calculer_score_capital(350000) == 2
        assert calculer_score_capital(500000) == 2
    
    def test_plus_500000_retourne_1(self):
        assert calculer_score_capital(500001) == 1
        assert calculer_score_capital(1000000) == 1
    
    def test_non_precise_retourne_6(self):
        assert calculer_score_capital("") == 6
        assert calculer_score_capital(None) == 6
        assert calculer_score_capital("Non précisé") == 6


class TestCalculScoreTotal:
    """Tests pour le calcul du score total."""
    
    def test_score_total_simple(self):
        reponses = {
            2: "Oui",  # 0
            3: "SAS",   # 0
            4: 100000,  # 3
            5: "5 ans", # 0
            6: "3 ans", # 2
            7: "Oui",   # 1
            8: "grande", # 0
            9: "Oui",   # 0
            10: "1 an", # 1
            11: "Oui",  # 1
            12: "Oui"   # 1
        }
        score = calculer_score_total(reponses)
        assert score == 0 + 0 + 3 + 0 + 2 + 1 + 0 + 0 + 1 + 1 + 1  # = 9
    
    def test_score_total_avec_scores_precalcules(self):
        reponses = {
            2: 40,  # Score déjà calculé
            3: 2,   # Score déjà calculé
            4: 3    # Score déjà calculé
        }
        score = calculer_score_total(reponses)
        assert score == 40 + 2 + 3  # = 45


class TestDeterminerNiveauRisque:
    """Tests pour la détermination du niveau de risque."""
    
    def test_low_risque(self):
        assert determiner_niveau_risque(0).value == "Low"
        assert determiner_niveau_risque(5).value == "Low"
        assert determiner_niveau_risque(10).value == "Low"
    
    def test_medium_risque(self):
        assert determiner_niveau_risque(11).value == "Medium"
        assert determiner_niveau_risque(20).value == "Medium"
        assert determiner_niveau_risque(24).value == "Medium"
    
    def test_high_risque(self):
        assert determiner_niveau_risque(25).value == "High"
        assert determiner_niveau_risque(30).value == "High"
    
    def test_critical_risque(self):
        assert determiner_niveau_risque(31).value == "Critical"
        assert determiner_niveau_risque(50).value == "Critical"
        assert determiner_niveau_risque(100).value == "Critical"


class TestCalculPrecision:
    """Tests pour le calcul de la précision."""
    
    def test_precision_100_pourcent(self):
        reponses = {
            2: "Oui",
            5: "Non",
            7: "Oui",
            8: "Non",
            9: "Oui"
        }
        precision = calculer_precision(reponses)
        assert precision == 100.0
    
    def test_precision_partielle(self):
        reponses = {
            2: "Oui",
            5: "Peut-être",  # Non valide
            7: "Oui"
        }
        precision = calculer_precision(reponses)
        assert precision == round((2 / 3) * 100, 2)
    
    def test_precision_zero(self):
        reponses = {
            2: "Peut-être",
            5: "Inconnu"
        }
        precision = calculer_precision(reponses)
        assert precision == 0.0
    
    def test_precision_vide(self):
        precision = calculer_precision({})
        assert precision == 0.0


class TestAnalyserEtCalculer:
    """Tests pour la fonction principale d'analyse."""
    
    def test_analyse_complete(self):
        reponses = {
            2: "Oui",
            3: "SAS",
            4: 50000,
            5: "5 ans",
            6: "3 ans",
            7: "Oui",
            8: "grande",
            9: "Oui",
            10: "1 an",
            11: "Oui",
            12: "Oui"
        }
        
        resultat = analyser_et_calculer(reponses)
        
        assert "score_total" in resultat
        assert "niveau_risque" in resultat
        assert "precision" in resultat
        assert "scores_detail" in resultat
        
        assert isinstance(resultat["score_total"], int)
        assert resultat["niveau_risque"] in ["Low", "Medium", "High", "Critical"]
        assert 0 <= resultat["precision"] <= 100
    
    def test_analyse_avec_reponses_binaires(self):
        reponses = {
            2: "Oui",
            3: "SARL",
            4: 10000
        }
        
        reponses_binaires = {
            2: "Oui",
            5: "Non",
            7: "Oui"
        }
        
        resultat = analyser_et_calculer(reponses, reponses_binaires)
        
        assert resultat["precision"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


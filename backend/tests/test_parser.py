"""
Tests unitaires pour le module parser.py.
"""

import pytest
from app.parser import (
    extraire_texte,
    detecter_type_document,
    parser_document,
    extraire_texte_async,
    detecter_type_document_async,
    parser_document_async
)


class TestExtractionTexte:
    """Tests pour l'extraction de texte."""
    
    def test_extraction_texte_vide(self, tmp_path):
        """Test avec un PDF vide ou inexistant."""
        pdf_path = tmp_path / "test.pdf"
        # Créer un fichier PDF minimal (simulé)
        # En réalité, on utiliserait un vrai PDF de test
        result = extraire_texte(str(pdf_path), max_pages=1, max_chars=100)
        assert isinstance(result, str)
    
    def test_limite_max_chars(self):
        """Test que la limite de caractères est respectée."""
        # Ce test nécessiterait un vrai PDF
        pass


class TestDetectionType:
    """Tests pour la détection de type de document."""
    
    def test_detecter_kbis(self):
        texte = "Extrait Kbis - Registre du Commerce et des Sociétés - Greffe de Nanterre"
        assert detecter_type_document(texte) == "extrait_kbis"
    
    def test_detecter_assurance(self):
        texte = "Attestation d'assurance - Compagnie d'assurance - Numéro de police 12345"
        assert detecter_type_document(texte) == "attestation_assurance"
    
    def test_detecter_bilan(self):
        texte = "Bilan comptable - Actif - Passif"
        assert detecter_type_document(texte) == "bilan_comptable"
    
    def test_detecter_autorisation(self):
        texte = "Autorisation d'exploitation commerciale - Permis d'exploitation"
        assert detecter_type_document(texte) == "autorisation_commerciale"
    
    def test_detecter_inconnu(self):
        texte = "Document quelconque sans type spécifique"
        assert detecter_type_document(texte) == "type_inconnu"
    
    def test_detecter_vide(self):
        assert detecter_type_document("") == "type_inconnu"
        assert detecter_type_document(None) == "type_inconnu"


class TestParserDocument:
    """Tests pour le parsing complet de document."""
    
    @pytest.mark.asyncio
    async def test_parser_document_async(self, tmp_path):
        """Test de la version async."""
        # Ce test nécessiterait un vrai PDF
        pdf_path = tmp_path / "test.pdf"
        # Pour l'instant, on teste juste que la fonction existe
        # et ne lève pas d'erreur
        try:
            result = await parser_document_async(str(pdf_path))
            assert isinstance(result, str)
        except FileNotFoundError:
            # Attendu si le fichier n'existe pas
            pass


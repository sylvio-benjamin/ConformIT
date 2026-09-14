"""
Module de parsing de documents PDF avec optimisations async et performance.
"""

import asyncio
import pdfplumber
from typing import Optional, Dict, Set
from pathlib import Path
from functools import lru_cache
import re


# Cache pour les types de documents détectés (évite de re-parser le même fichier)
@lru_cache(maxsize=100)
def _detecter_type_document_cached(texte_hash: int, texte_snippet: str) -> str:
    """
    Version cachée de la détection de type de document.
    
    Args:
        texte_hash: Hash du texte pour cache
        texte_snippet: Extrait du texte (premiers 5000 caractères)
        
    Returns:
        Type de document détecté
    """
    return _detecter_type_document_internal(texte_snippet)


def _detecter_type_document_internal(texte: str) -> str:
    """
    Logique interne de détection de type de document.
    
    Args:
        texte: Texte à analyser
        
    Returns:
        Type de document détecté
    """
    texte_lower = texte.lower()
    types_detectes: Dict[str, bool] = {}

    # Extrait Kbis - Patterns optimisés (priorité haute car très spécifique)
    # Pour éviter les faux positifs, on cherche des combinaisons de patterns
    kbis_score = 0
    if "registre du commerce" in texte_lower or "extrait kbis" in texte_lower or "extrait k bis" in texte_lower:
        kbis_score += 3  # Patterns très spécifiques
    if "rcs" in texte_lower:
        # Vérifier qu'on a des indices supplémentaires pour éviter les faux positifs
        if any(word in texte_lower for word in ["paris", "lyon", "versailles", "nanterre", "bobigny", "creteil", "tribunal", "greffe"]):
            kbis_score += 2
        else:
            kbis_score += 1
    if "greffe" in texte_lower and "tribunal" in texte_lower:
        kbis_score += 2
    if kbis_score >= 2:
        types_detectes["kbis"] = True

    # Attestation d'assurance - Patterns spécifiques
    assurance_patterns = [
        "attestation d'assurance",
        "attestation assurance",
        "compagnie d'assurance",
        "numéro de police",
        "police d'assurance",
        "contrat d'assurance"
    ]
    if any(pattern in texte_lower for pattern in assurance_patterns):
        types_detectes["assurance"] = True

    # Comptes sociaux (bilan + compte de résultat + annexe) - Détection plus précise
    # On cherche des patterns explicites OU une combinaison cohérente de termes financiers
    comptes_sociaux_explicit = [
        "comptes sociaux",
        "comptes annuels",
        "compte de résultat",
        "compte de resultat",
        "annexe comptable"
    ]
    # Patterns de bilan (plus spécifiques pour éviter les faux positifs)
    bilan_patterns = [
        "bilan",
        "total actif",
        "total passif",
        "actif total",
        "passif total"
    ]
    # Patterns de compte de résultat
    compte_resultat_patterns = [
        "compte de résultat",
        "compte de resultat",
        "chiffre d'affaires",
        "chiffre daffaires",
        "résultat net",
        "resultat net"
    ]
    
    # Détection explicite de comptes sociaux
    has_explicit_comptes_sociaux = any(pattern in texte_lower for pattern in comptes_sociaux_explicit)
    
    # Détection par combinaison : besoin d'au moins 2 éléments pour éviter les faux positifs
    has_bilan = any(pattern in texte_lower for pattern in bilan_patterns)
    has_compte_resultat = any(pattern in texte_lower for pattern in compte_resultat_patterns)
    
    # Compter les occurrences pour être plus précis
    bilan_count = sum(1 for pattern in bilan_patterns if pattern in texte_lower)
    compte_resultat_count = sum(1 for pattern in compte_resultat_patterns if pattern in texte_lower)
    
    # Vérifier la présence de termes financiers clés
    has_actif_passif = "actif" in texte_lower and "passif" in texte_lower
    has_produits_charges = "produits" in texte_lower and "charges" in texte_lower
    
    # Détecter comptes sociaux si :
    # 1. Patterns explicites présents, OU
    # 2. (Bilan ET compte de résultat), OU
    # 3. (Bilan avec plusieurs occurrences ET actif/passif), OU
    # 4. (Compte de résultat avec plusieurs occurrences ET produits/charges)
    if has_explicit_comptes_sociaux:
        types_detectes["comptes_sociaux"] = True
    elif has_bilan and has_compte_resultat:
        types_detectes["comptes_sociaux"] = True
    elif (bilan_count >= 2 and has_actif_passif):
        types_detectes["comptes_sociaux"] = True
    elif (compte_resultat_count >= 2 and has_produits_charges):
        types_detectes["comptes_sociaux"] = True
    elif (bilan_count >= 1 and compte_resultat_count >= 1):
        types_detectes["comptes_sociaux"] = True

    # Statuts - Patterns spécifiques
    statuts_patterns = [
        "statuts",
        "statut",
        "règlement intérieur",
        "reglement interieur",
        "pacte d'actionnaires",
        "pacte dactionnaires",
        "répartition du capital",
        "repartition du capital",
        "clauses d'agrément",
        "clauses dagrement",
        "apports en numéraire",
        "apports en nature",
        "clauses de préemption",
        "clauses de preemption",
        "pouvoirs du gérant",
        "pouvoirs du president",
        "durée de vie",
        "duree de vie",
        "modalités de décision",
        "modalites de decision"
    ]
    if any(pattern in texte_lower for pattern in statuts_patterns):
        types_detectes["statuts"] = True

    # Relevé bancaire - Patterns spécifiques
    releve_patterns = [
        "relevé bancaire",
        "releve bancaire",
        "relevé de compte",
        "releve de compte",
        "extrait de compte",
        "solde moyen",
        "solde bancaire",
        "découvert autorisé",
        "decouvert autorise",
        "incidents de paiement",
        "rejets de prélèvements",
        "rejets de prelevements",
        "agios",
        "virements urgents",
        "encaissements",
        "décaissements",
        "decaisements",
        "opérations suspectes",
        "operations suspectes"
    ]
    if any(pattern in texte_lower for pattern in releve_patterns):
        types_detectes["releve"] = True

    # Liasse fiscale - Patterns spécifiques
    liasse_patterns = [
        "liasse fiscale",
        "liasse",
        "tableau des flux",
        "flux de trésorerie",
        "flux de tresorerie",
        "créances douteuses",
        "creances douteuses",
        "rotation des stocks",
        "immobilisations amorties",
        "provisions pour risques",
        "produits exceptionnels",
        "charges à payer",
        "charges a payer",
        "produits constatés d'avance",
        "produits constates davance",
        "report à nouveau",
        "report a nouveau",
        "subventions d'exploitation",
        "subventions dexploitation"
    ]
    if any(pattern in texte_lower for pattern in liasse_patterns):
        types_detectes["liasse"] = True

    # Compte de résultat - Patterns spécifiques (différencier des comptes sociaux)
    compte_resultat_patterns_detailed = [
        "compte de résultat",
        "compte de resultat",
        "résultat net",
        "resultat net",
        "marge brute",
        "marge nette",
        "résultat d'exploitation",
        "resultat dexploitation",
        "ebit",
        "ebitda",
        "chiffre d'affaires",
        "chiffre daffaires",
        "charges de personnel",
        "charges financières",
        "charges financieres",
        "résultat exceptionnel",
        "resultat exceptionnel",
        "capacité d'autofinancement",
        "capacite dautofinancement",
        "caf"
    ]
    # Détecter compte de résultat seulement si on a plusieurs patterns ET pas de bilan
    compte_resultat_count = sum(1 for pattern in compte_resultat_patterns_detailed if pattern in texte_lower)
    if compte_resultat_count >= 3 and not has_bilan:
        types_detectes["compte_resultat"] = True

    # Autorisations commerciales
    autorisation_patterns = [
        "autorisation d'exploitation",
        "autorisation commerciale",
        "permis d'exploitation",
        "licence d'exploitation"
    ]
    if any(pattern in texte_lower for pattern in autorisation_patterns):
        types_detectes["autorisation"] = True

    # Retour du type détecté (priorité)
    if types_detectes.get("kbis"):
        return "extrait_kbis"
    elif types_detectes.get("assurance"):
        return "attestation_assurance"
    elif types_detectes.get("statuts"):
        return "statuts"
    elif types_detectes.get("releve"):
        return "releve_bancaire"
    elif types_detectes.get("liasse"):
        return "liasse_fiscale"
    elif types_detectes.get("compte_resultat"):
        return "compte_resultat"
    elif types_detectes.get("comptes_sociaux"):
        return "comptes_sociaux"
    elif types_detectes.get("autorisation"):
        return "autorisation_commerciale"
    else:
        return "type_inconnu"


def extraire_texte(pdf_path: str, max_pages: int = 10, max_chars: int = 10000) -> str:
    """
    Extrait le texte d'un PDF de manière optimisée.
    
    Args:
        pdf_path: Chemin du fichier PDF
        max_pages: Nombre maximum de pages à extraire
        max_chars: Nombre maximum de caractères à extraire
        
    Returns:
        Texte extrait (en minuscules)
    """
    texte = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Limiter le nombre de pages pour performance
            pages_to_process = min(max_pages, len(pdf.pages))
            
            for i in range(pages_to_process):
                page = pdf.pages[i]
                page_text = page.extract_text() or ""
                
                if page_text:
                    texte += page_text + "\n"
                    
                    # Arrêter si on a assez de caractères
                    if len(texte) >= max_chars:
                        break
    except Exception as e:
        print(f"⚠️ Erreur lors de l'extraction du texte PDF : {e}")
    
    # Limiter la taille finale et convertir en minuscules
    return texte[:max_chars].lower()


async def extraire_texte_async(pdf_path: str, max_pages: int = 10, max_chars: int = 10000) -> str:
    """
    Version asynchrone de l'extraction de texte (pour I/O non-bloquantes).
    
    Args:
        pdf_path: Chemin du fichier PDF
        max_pages: Nombre maximum de pages à extraire
        max_chars: Nombre maximum de caractères à extraire
        
    Returns:
        Texte extrait (en minuscules)
    """
    # Exécuter dans un thread pool pour éviter de bloquer
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extraire_texte, pdf_path, max_pages, max_chars)


def detecter_type_document(texte: str, use_cache: bool = True) -> str:
    """
    Détecte le type de document à partir du texte extrait.
    
    Args:
        texte: Texte du document à analyser
        use_cache: Utiliser le cache pour améliorer les performances
        
    Returns:
        Type de document détecté
    """
    if not texte:
        return "type_inconnu"
    
    # Utiliser un snippet pour le cache (premiers 5000 caractères)
    texte_snippet = texte[:5000]
    texte_hash = hash(texte_snippet)
    
    if use_cache:
        return _detecter_type_document_cached(texte_hash, texte_snippet)
    else:
        return _detecter_type_document_internal(texte)


async def detecter_type_document_async(texte: str, use_cache: bool = True) -> str:
    """
    Version asynchrone de la détection de type de document.
    
    Args:
        texte: Texte du document à analyser
        use_cache: Utiliser le cache pour améliorer les performances
        
    Returns:
        Type de document détecté
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, detecter_type_document, texte, use_cache)


def parser_document(pdf_path: str, max_pages: int = 10, max_chars: int = 10000) -> str:
    """
    Parse un document PDF et détecte son type.
    
    Args:
        pdf_path: Chemin du fichier PDF
        max_pages: Nombre maximum de pages à analyser
        max_chars: Nombre maximum de caractères à extraire
        
    Returns:
        Type de document détecté
    """
    texte = extraire_texte(pdf_path, max_pages, max_chars)
    return detecter_type_document(texte)


async def parser_document_async(pdf_path: str, max_pages: int = 10, max_chars: int = 10000) -> str:
    """
    Version asynchrone du parsing de document.
    
    Args:
        pdf_path: Chemin du fichier PDF
        max_pages: Nombre maximum de pages à analyser
        max_chars: Nombre maximum de caractères à extraire
        
    Returns:
        Type de document détecté
    """
    texte = await extraire_texte_async(pdf_path, max_pages, max_chars)
    return await detecter_type_document_async(texte)


# Exemple d'utilisation
if __name__ == "__main__":
    chemin_pdf = "document_test.pdf"
    type_doc = parser_document(chemin_pdf)
    print(f"✅ Type de document détecté : {type_doc}")

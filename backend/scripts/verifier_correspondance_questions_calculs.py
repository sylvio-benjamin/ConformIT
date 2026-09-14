"""
Script de vérification de la correspondance entre les questions JSON et les fichiers de calcul.

Ce script vérifie que :
1. Chaque question dans les fichiers JSON a une logique de calcul correspondante
2. Le nombre de questions correspond
3. Les numéros de questions sont cohérents
"""

import json
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mapping des types de documents vers les fichiers de questions et de calculs
MAPPING = {
    "extrait_kbis": {
        "questions": "questions.json",
        "calculs": "calculs_kbis.py",
        "questions_keys": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # 11 questions
    },
    "comptes_sociaux": {
        "questions": "questions_comptes_sociaux.json",
        "calculs": "calculs_comptes_sociaux.py",
        "questions_keys": list(range(1, 16)),  # 15 questions
    },
    "bilan_comptable": {
        "questions": "questions_bilan_comptable.json",
        "calculs": "calculs_bilan.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
    "compte_resultat": {
        "questions": "questions_compte_resultat.json",
        "calculs": "calculs_compte_resultat.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
    "liasse_fiscale": {
        "questions": "questions_liasse_fiscale.json",
        "calculs": "calculs_liasse.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
    "releve_bancaire": {
        "questions": "questions_releve_bancaire.json",
        "calculs": "calculs_releve.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
    "statuts": {
        "questions": "questions_statuts.json",
        "calculs": "calculs_statuts.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
    "attestation_assurance": {
        "questions": "questions_attestation.json",
        "calculs": "calculs_attestation.py",
        "questions_keys": list(range(1, 11)),  # 10 questions
    },
}

DOCUMENTS_ROOT = Path(__file__).parent.parent / "documents"
APP_ROOT = Path(__file__).parent.parent / "app"


def verifier_correspondance():
    """Vérifie la correspondance entre les questions JSON et les fichiers de calcul."""
    print("=" * 80)
    print("VERIFICATION DE LA CORRESPONDANCE QUESTIONS JSON <-> FICHIERS DE CALCUL")
    print("=" * 80)
    print()
    
    tous_ok = True
    
    for type_doc, config in MAPPING.items():
        print(f"\n{'='*80}")
        print(f"[*] Type de document : {type_doc}")
        print(f"{'='*80}")
        
        # Charger les questions JSON
        questions_path = DOCUMENTS_ROOT / config["questions"]
        if not questions_path.exists():
            print(f"[ERROR] Fichier de questions non trouve : {questions_path}")
            tous_ok = False
            continue
        
        with open(questions_path, "r", encoding="utf-8") as f:
            questions_json = json.load(f)
        
        questions_keys_json = sorted([int(k) for k in questions_json.keys()])
        questions_attendu = config["questions_keys"]
        
        print(f"[OK] Fichier de questions : {config['questions']}")
        print(f"   Questions dans JSON : {questions_keys_json}")
        print(f"   Questions attendues : {questions_attendu}")
        
        # Vérifier que les clés correspondent
        if questions_keys_json != questions_attendu:
            print(f"[ERROR] INCOHERENCE : Les cles de questions ne correspondent pas !")
            print(f"   Difference : {set(questions_keys_json) ^ set(questions_attendu)}")
            tous_ok = False
        else:
            print(f"[OK] Les cles de questions correspondent")
        
        # Vérifier que le fichier de calcul existe
        calculs_path = APP_ROOT / config["calculs"]
        if not calculs_path.exists():
            print(f"[ERROR] Fichier de calcul non trouve : {calculs_path}")
            tous_ok = False
            continue
        
        print(f"[OK] Fichier de calcul : {config['calculs']}")
        
        # Lire le fichier de calcul pour vérifier qu'il traite toutes les questions
        with open(calculs_path, "r", encoding="utf-8") as f:
            calculs_content = f.read()
        
        # Vérifier que chaque question est traitée dans le fichier de calcul
        questions_manquantes = []
        for q_num in questions_attendu:
            # Chercher des références à cette question dans le code
            # Patterns possibles : "question {q_num}", "Q{q_num}", "enregistrer({q_num}", etc.
            patterns = [
                f"question {q_num}",
                f"Q{q_num}",
                f"enregistrer({q_num}",
                f"enregistrer({q_num},",
                f"enregistrer({q_num} ",
                f"enregistrer(\n        {q_num}",
                f"enregistrer(\n        {q_num},",
                f"reponses.get({q_num}",
                f"reponses[{q_num}",
                f"Question {q_num}",
                f"# Question {q_num}",
                f"# Question {q_num}:",
            ]
            
            # Chercher aussi avec regex pour les patterns multi-lignes
            import re
            trouve = False
            for pattern in patterns:
                if pattern.lower() in calculs_content.lower():
                    trouve = True
                    break
            
            # Chercher aussi le pattern "enregistrer(\n        {q_num}," avec regex
            if not trouve:
                regex_pattern = rf"enregistrer\s*\(\s*{q_num}\s*,"
                if re.search(regex_pattern, calculs_content, re.IGNORECASE | re.MULTILINE):
                    trouve = True
            
            if not trouve:
                questions_manquantes.append(q_num)
        
        if questions_manquantes:
            print(f"[ERROR] Questions non traitees dans le fichier de calcul : {questions_manquantes}")
            tous_ok = False
        else:
            print(f"[OK] Toutes les questions sont traitees dans le fichier de calcul")
        
        # Afficher les questions pour vérification manuelle
        print(f"\n[*] Questions dans le JSON :")
        for q_num in questions_keys_json:
            question_text = questions_json[str(q_num)]
            print(f"   Q{q_num}: {question_text[:60]}...")
    
    print(f"\n{'='*80}")
    if tous_ok:
        print("[OK] TOUTES LES VERIFICATIONS SONT PASSEES")
    else:
        print("[ERROR] DES PROBLEMES ONT ETE DETECTES")
    print(f"{'='*80}")
    
    return tous_ok


if __name__ == "__main__":
    success = verifier_correspondance()
    sys.exit(0 if success else 1)


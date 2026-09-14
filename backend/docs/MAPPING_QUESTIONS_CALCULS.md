# Mapping Questions JSON ↔ Fichiers de Calcul

Ce document détaille la correspondance exacte entre chaque question dans les fichiers JSON et la logique de calcul dans les fichiers Python.

## 1. Bilan Comptable (questions_bilan_comptable.json ↔ calculs_bilan.py)

| Q# | Question JSON | Logique de Calcul | Condition | Pénalité |
|----|---------------|-------------------|-----------|----------|
| 1 | Le ratio de liquidité générale (actif circulant / dettes court terme) est-il supérieur à 1 ? | `ratio_liquidite >= 1.0` | `ratio_liquidite = actif_circulant / dettes_court_terme` | HIGH (10) si False |
| 2 | Le fonds de roulement net global (FRNG) est-il positif ? | `frng > 0` | `frng = financement_permanent - actif_circulant` | HIGH (10) si False |
| 3 | Le besoin en fonds de roulement (BFR) est-il maîtrisé (< 90 jours de CA) ? | `bfr_jours <= 90` | `bfr_jours = (bfr / ca) * 365` | MEDIUM (6) si False |
| 4 | Les capitaux propres sont-ils positifs ? | `cp > 0` | `cp = capitaux_propres` | HIGH (10) si False |
| 5 | Le ratio d'endettement (dettes financières / capitaux propres) est-il inférieur à 1 ? | `ratio_endettement < 1` | `ratio_endettement = dettes_financieres / capitaux_propres` | MEDIUM (6) si False |
| 6 | Les capitaux propres ont-ils augmenté sur les 3 derniers exercices ? | `cp >= cp_n1` | Nécessite données multi-exercices | MEDIUM (6) si False |
| 7 | La trésorerie nette est-elle positive ? | `tresorerie_nette > 0` | `tresorerie_nette = disponibilites - dettes_court_terme` | HIGH (10) si False |
| 8 | Le ratio d'autonomie financière (capitaux propres / total passif) est-il supérieur à 20% ? | `ratio_autonomie >= 0.20` | `ratio_autonomie = capitaux_propres / total_passif` | MEDIUM (6) si False |
| 9 | Les créances clients représentent-elles moins de 90 jours de CA ? | `creances_clients_jours <= 90` | `creances_clients_jours = (creances_clients / ca) * 365` | MEDIUM (6) si False |
| 10 | Les dettes fournisseurs sont-elles inférieures à 90 jours d'achats ? | `dettes_fournisseurs_jours <= 90` | `dettes_fournisseurs_jours = (dettes_fournisseurs / achats) * 365` | MEDIUM (6) si False |

**Score max théorique** : 4 * 10 + 6 * 6 = 76 points → Normalisé sur 100

## 2. Comptes Sociaux (questions_comptes_sociaux.json ↔ calculs_comptes_sociaux.py)

Questions 1-10 : Identiques au bilan comptable (voir ci-dessus)
Questions 11-15 : Compte de résultat

| Q# | Question JSON | Logique de Calcul | Condition | Pénalité |
|----|---------------|-------------------|-----------|----------|
| 11 | Le résultat net de l'exercice est-il positif ? | `resultat_net > 0` | `resultat_net` extrait du compte de résultat | HIGH (10) si False |
| 12 | La marge brute est-elle supérieure à 30% du chiffre d'affaires ? | `marge_brute_pct >= 30` | `marge_brute_pct = (marge_brute / ca) * 100` | MEDIUM (6) si False |
| 13 | Le taux de croissance du chiffre d'affaires est-il positif ? | `None` (données multi-exercices non disponibles) | Nécessite plusieurs années | LOW (0) - Non critique |
| 14 | Les charges financières sont-elles inférieures à 10% du résultat d'exploitation ? | `charges_financieres_pct <= 10` | `charges_financieres_pct = (charges_financieres / resultat_exploitation) * 100` | MEDIUM (6) si False |
| 15 | Le ratio de couverture des dettes (résultat d'exploitation / charges financières) est-il supérieur à 3 ? | `ratio_couverture_dettes >= 3` | `ratio_couverture_dettes = resultat_exploitation / charges_financieres` | MEDIUM (6) si False |

**Score max théorique** : 5 * 10 + 9 * 6 = 104 points → Normalisé sur 100

## 3. Compte de Résultat (questions_compte_resultat.json ↔ calculs_compte_resultat.py)

| Q# | Question JSON | Logique de Calcul | Condition | Pénalité |
|----|---------------|-------------------|-----------|----------|
| 1 | L'entreprise est-elle bénéficiaire (résultat net positif) ? | `_is_positive(reponses.get(1))` | Groq répond "Oui"/"Non" | HIGH (10) si False |
| 2 | La marge brute (sur ventes) est-elle supérieure à 20% ? | `_is_positive(reponses.get(2))` | Groq répond "Oui"/"Non" | HIGH (10) si False |
| 3 | Le résultat d'exploitation (EBIT) est-il positif ? | `_is_positive(reponses.get(3))` | Groq répond "Oui"/"Non" | HIGH (10) si False |
| 4 | La marge nette est-elle supérieure à 5% ? | `_is_positive(reponses.get(4))` | Groq répond "Oui"/"Non" | HIGH (10) si False |
| 5 | L'EBITDA est-il positif ? | `_is_positive(reponses.get(5))` | Groq répond "Oui"/"Non" | HIGH (10) si False |
| 6 | Le chiffre d'affaires a-t-il progressé sur les 3 derniers exercices ? | `_is_positive(reponses.get(6))` | Groq répond "Oui"/"Non" | MEDIUM (5) si False |
| 7 | Les charges de personnel représentent-elles moins de 60% du CA ? | `_is_positive(reponses.get(7))` | Groq répond "Oui"/"Non" | MEDIUM (5) si False |
| 8 | Les charges financières représentent-elles moins de 5% du CA ? | `_is_positive(reponses.get(8))` | Groq répond "Oui"/"Non" | MEDIUM (5) si False |
| 9 | Le résultat exceptionnel impacte-t-il négativement le résultat net de plus de 20% ? | `_is_positive(reponses.get(9))` | **INVERSÉ** : Si Oui = RISQUE | HIGH (10) si True (risque) |
| 10 | La capacité d'autofinancement (CAF) est-elle positive ? | `_is_positive(reponses.get(10))` | Groq répond "Oui"/"Non" | HIGH (10) si False |

**Score max théorique** : 6 * 10 + 3 * 5 + 1 * 10 = 85 points → Normalisé sur 100

## Notes importantes

1. **Fichiers avec calculs directs** (bilan, comptes sociaux) : Les valeurs sont extraites du PDF et les ratios sont calculés directement.
2. **Fichiers avec Groq** (compte_resultat, liasse, releve, statuts, attestation) : Les réponses de Groq sont interprétées avec `_is_positive()` qui cherche des mots-clés comme "oui", "positif", etc.
3. **Questions inversées** : Certaines questions (Q9 compte_resultat, Q5/Q6 liasse, Q2/Q3/Q4/Q8/Q10 releve, Q7 statuts) sont inversées (Oui = Risque).


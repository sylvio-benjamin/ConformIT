# Scénarios Métiers - Plateforme SaaS de Gestion des Risques

## Vue d'ensemble

Documentation des principaux scénarios métiers pour la plateforme de gestion des risques.

---

## 1. Scénario 1 : TPE importe son bilan comptable

### 1.1 Contexte

**Utilisateur :** TPE (Très Petite Entreprise)
**Objectif :** Analyser automatiquement le bilan comptable et identifier les risques financiers
**Résultat attendu :** Score de risque, risques identifiés, actions recommandées

### 1.2 Workflow Détaillé

**Étape 1 : Upload du bilan**
1. **Utilisateur** se connecte à l'application
2. **Utilisateur** navigue vers "Analyses" → "Importer un document"
3. **Utilisateur** upload le bilan comptable (PDF)
4. **Système** valide le fichier (taille, format, type MIME)
5. **Système** sauvegarde le fichier dans le dossier `uploads/`

**Étape 2 : Extraction des données**
1. **Système** détecte le type de document ("comptes_sociaux")
2. **Système** extrait le texte du PDF (OCR si nécessaire)
3. **Système** utilise l'IA (Groq) pour extraire les données structurées :
   - **Actif circulant** : 50 000 €
   - **Dettes court terme** : 30 000 €
   - **Capitaux propres** : 100 000 €
   - **Chiffre d'affaires** : 200 000 €
   - **Résultat net** : 20 000 €
   - **Marge brute** : 60 000 € (30% du CA)
   - **Charges financières** : 5 000 €
   - **Résultat d'exploitation** : 25 000 €
   - etc.
4. **Système** valide et corrige les données extraites
5. **Système** enregistre les données dans la base de données

**Étape 3 : Calcul des ratios**
1. **Système** calcule automatiquement les ratios financiers :
   - **Ratio de liquidité** = Actif circulant / Dettes court terme = 50 000 / 30 000 = 1.67 (> 1) ✅
   - **FRNG** = Financement permanent - Actif circulant = (100 000 + 0) - 50 000 = 50 000 € (> 0) ✅
   - **BFR** = Actif circulant - Dettes court terme = 50 000 - 30 000 = 20 000 €
   - **BFR en jours de CA** = (20 000 / 200 000) × 365 = 36.5 jours (< 90) ✅
   - **Ratio d'endettement** = Dettes financières / Capitaux propres = 0 / 100 000 = 0 (< 1) ✅
   - **Ratio d'autonomie** = Capitaux propres / Total passif = 100 000 / 130 000 = 76.9% (> 20%) ✅
   - **Créances clients en jours** = (10 000 / 200 000) × 365 = 18.25 jours (< 90) ✅
   - **Dettes fournisseurs en jours** = (15 000 / 50 000) × 365 = 109.5 jours (> 90) ⚠️
   - **Résultat net** = 20 000 € (> 0) ✅
   - **Marge brute** = 30% (> 30%) ✅
   - **Charges financières** = 5 000 / 25 000 = 20% (> 10%) ⚠️
   - **Ratio de couverture** = 25 000 / 5 000 = 5 (> 3) ✅
   - etc.

**Étape 4 : Évaluation des risques**
1. **Système** évalue chaque indicateur (15 questions pour comptes sociaux) :
   - **Q1** : Ratio de liquidité > 1 ? → **Oui** (1.67) → 0 point
   - **Q2** : FRNG positif ? → **Oui** (50 000 €) → 0 point
   - **Q3** : BFR < 90 jours ? → **Oui** (36.5 jours) → 0 point
   - **Q4** : Capitaux propres positifs ? → **Oui** (100 000 €) → 0 point
   - **Q5** : Ratio d'endettement < 1 ? → **Oui** (0) → 0 point
   - **Q6** : Capitaux propres augmentés ? → **Non précisé** (données multi-exercices non disponibles) → 6 points
   - **Q7** : Trésorerie nette positive ? → **Oui** (20 000 €) → 0 point
   - **Q8** : Ratio d'autonomie > 20% ? → **Oui** (76.9%) → 0 point
   - **Q9** : Créances clients < 90 jours ? → **Oui** (18.25 jours) → 0 point
   - **Q10** : Dettes fournisseurs < 90 jours ? → **Non** (109.5 jours) → 6 points
   - **Q11** : Résultat net positif ? → **Oui** (20 000 €) → 0 point
   - **Q12** : Marge brute > 30% ? → **Oui** (30%) → 0 point
   - **Q13** : Croissance du CA positive ? → **Non précisé** (données multi-exercices non disponibles) → 0 point
   - **Q14** : Charges financières < 10% ? → **Non** (20%) → 6 points
   - **Q15** : Ratio de couverture > 3 ? → **Oui** (5) → 0 point
2. **Système** calcule le score de risque :
   - **Score brut** = 0 + 0 + 0 + 0 + 0 + 6 + 0 + 0 + 0 + 6 + 0 + 0 + 0 + 6 + 0 = 18 points
   - **Score max théorique** = 104 points (5 × 10 + 9 × 6)
   - **Score normalisé** = (18 / 104) × 100 = 17.3 points (arrondi à 17)
   - **Niveau de risque** = Low (0-30)
   - **Couleur** = Vert (#00A859)

**Étape 5 : Identification des risques**
1. **Système** identifie automatiquement les risques :
   - **Risque de délais de paiement fournisseurs** (Q10 : Dettes fournisseurs > 90 jours)
   - **Risque de charges financières élevées** (Q14 : Charges financières > 10%)
   - **Risque d'évolution des capitaux propres** (Q6 : Données multi-exercices non disponibles)
2. **Système** crée automatiquement des risques dans le registre :
   - **RISK-001** : Risque de délais de paiement fournisseurs (Score : 6/10, Niveau : Medium)
   - **RISK-002** : Risque de charges financières élevées (Score : 6/10, Niveau : Medium)
   - **RISK-003** : Risque d'évolution des capitaux propres (Score : 6/10, Niveau : Medium)

**Étape 6 : Actions recommandées**
1. **Système** propose des actions recommandées :
   - **Pour RISK-001** : Négocier des délais de paiement avec les fournisseurs, améliorer la trésorerie
   - **Pour RISK-002** : Renégocier les taux d'intérêt, refinancer les dettes
   - **Pour RISK-003** : Importer les bilans des années précédentes pour analyser l'évolution
2. **Utilisateur** consulte les actions recommandées
3. **Utilisateur** crée des plans d'action pour traiter les risques
4. **Système** crée des tâches pour les responsables
5. **Système** suit l'avancement des actions

**Étape 7 : Rapport et suivi**
1. **Système** génère automatiquement un rapport d'analyse :
   - **Score de risque** : 17/100 (Low)
   - **Niveau de risque** : Low (Risque faible)
   - **Risques identifiés** : 3 risques (Medium)
   - **Actions recommandées** : 3 actions
   - **Détails** : Détails de chaque indicateur, justification, score
2. **Utilisateur** consulte le rapport
3. **Utilisateur** exporte le rapport (PDF, Excel)
4. **Utilisateur** partage le rapport avec les parties prenantes
5. **Système** suit l'avancement des actions
6. **Système** génère des rapports périodiques

### 1.3 Résultat

**Score de risque :** 17/100 (Low - Risque faible)
**Risques identifiés :** 3 risques (Medium)
**Actions recommandées :** 3 actions
**Rapport généré :** Oui (PDF, Excel)
**Suivi :** Oui (avancement des actions)

---

## 2. Scénario 2 : ETI évalue ses risques opérationnels

### 2.1 Contexte

**Utilisateur :** ETI (Entreprise de Taille Intermédiaire)
**Objectif :** Évaluer les risques opérationnels et définir des contrôles
**Résultat attendu :** Risques évalués, contrôles définis, plans d'action créés

### 2.2 Workflow Détaillé

**Étape 1 : Création du risque**
1. **Risk Manager** crée un risque opérationnel :
   - **Titre** : "Risque de panne informatique"
   - **Description** : "Risque de panne du système informatique principal, impactant la continuité d'activité"
   - **Catégorie** : Opérationnel
   - **Propriétaire** : Directeur IT
   - **Statut** : Identifié
2. **Système** génère un ID unique : RISK-004
3. **Système** enregistre dans l'audit trail
4. **Système** envoie une notification au propriétaire

**Étape 2 : Évaluation du risque**
1. **Risk Manager** évalue le risque :
   - **Probabilité** : 4/5 (Élevée - Probable)
   - **Impact** : 5/5 (Critique - Impact majeur)
   - **Justification** : "Système informatique vieillissant, pas de redondance, impact majeur sur la continuité d'activité"
   - **Méthodologie** : Semi-quantitatif
   - **Confiance** : 4/5 (Élevée)
2. **Système** calcule le niveau de risque :
   - **Score** = Probabilité × Impact = 4 × 5 = 20/25
   - **Niveau** = Critical (19-25)
   - **Score normalisé** = (20 / 25) × 100 = 80/100
   - **Couleur** = Rouge (#E74C3C)
3. **Système** positionne le risque sur la matrice (heatmap)
4. **Système** propose des actions recommandées :
   - **Éviter** : Remplacer le système informatique (coût élevé)
   - **Réduire** : Implémenter des contrôles (sauvegarde, redondance, PCA)
   - **Transférer** : Sous-traiter l'infrastructure (cloud)
   - **Accepter** : Accepter le risque (non recommandé pour un risque critique)
5. **Risk Manager** sélectionne "Réduire"
6. **Système** met à jour le statut à "Évalué"

**Étape 3 : Définition des contrôles**
1. **Risk Manager** définit des contrôles :
   - **Contrôle 1** : Sauvegarde automatique des données (quotidienne)
   - **Contrôle 2** : Redondance des systèmes (serveurs de backup)
   - **Contrôle 3** : Plan de continuité d'activité (PCA)
   - **Contrôle 4** : Tests réguliers de restauration (mensuels)
2. **Système** propose des contrôles standards basés sur la catégorie
3. **Risk Manager** sélectionne les contrôles pertinents
4. **Système** crée les contrôles dans le registre
5. **Système** associe les contrôles au risque

**Étape 4 : Plan d'action**
1. **Risk Manager** définit un plan d'action :
   - **Action 1** : Mettre en place la sauvegarde automatique (Échéance : 1 mois, Responsable : Admin IT)
   - **Action 2** : Implémenter la redondance des systèmes (Échéance : 3 mois, Responsable : Directeur IT)
   - **Action 3** : Élaborer le PCA (Échéance : 2 mois, Responsable : Risk Manager)
   - **Action 4** : Tester la restauration (Échéance : 1 mois, Responsable : Admin IT)
2. **Système** crée des tâches pour les responsables
3. **Système** envoie des notifications aux responsables
4. **Système** met à jour le statut du risque à "Traité"

**Étape 5 : Suivi et réévaluation**
1. **Responsables** consultent les tâches assignées
2. **Responsables** implémentent les contrôles
3. **Responsables** mettent à jour le statut des plans d'action
4. **Système** suit l'avancement et génère des alertes pour les échéances
5. **Risk Manager** teste l'efficacité des contrôles
6. **Risk Manager** réévalue le risque après implémentation :
   - **Probabilité** : 2/5 (Faible - Peu probable) → Amélioration
   - **Impact** : 5/5 (Critique - Impact majeur) → Inchangé
   - **Score** = 2 × 5 = 10/25
   - **Niveau** = Medium (7-12)
   - **Score normalisé** = (10 / 25) × 100 = 40/100
   - **Couleur** = Orange (#FF9F1C)
7. **Système** met à jour le score et le niveau de risque
8. **Système** enregistre dans l'historique

### 2.3 Résultat

**Risque initial :** Critical (80/100)
**Risque après traitement :** Medium (40/100)
**Contrôles implémentés :** 4 contrôles
**Plans d'action :** 4 plans d'action
**Amélioration :** Réduction de 40 points (de 80 à 40)

---

## 3. Scénario 3 : Cabinet de conseil génère un rapport d'audit

### 3.1 Contexte

**Utilisateur :** Cabinet de conseil
**Objectif :** Générer un rapport d'audit pour un client
**Résultat attendu :** Rapport d'audit complet (PDF, Excel)

### 3.2 Workflow Détaillé

**Étape 1 : Configuration du rapport**
1. **Auditor** navigue vers "Rapports"
2. **Auditor** sélectionne "Rapport d'audit"
3. **Auditor** configure les paramètres :
   - **Période** : Année 2024
   - **Organisation** : Client X
   - **Filtres** : Tous les risques, tous les contrôles, tous les incidents
   - **Format** : PDF
   - **Modèle** : Modèle d'audit standard
4. **Système** valide les paramètres

**Étape 2 : Génération du rapport**
1. **Système** collecte les données :
   - **Risques** : 25 risques identifiés, 20 évalués, 15 traités
   - **Contrôles** : 30 contrôles définis, 25 implémentés, 20 testés
   - **Incidents** : 5 incidents enregistrés, 4 résolus
   - **Conformité** : ISO 31000 (80% conforme), ISO 27005 (70% conforme)
   - **KRIs** : 10 KRIs suivis, 2 alertes actives
2. **Système** génère les sections du rapport :
   - **Vue d'ensemble** : Résumé exécutif, KPIs principaux
   - **Matrice de risque** : Heatmap des risques
   - **Risques détaillés** : Liste des risques avec évaluations
   - **Contrôles** : Liste des contrôles avec efficacité
   - **Incidents** : Liste des incidents avec analyses
   - **Conformité** : Évaluations de conformité par norme
   - **KRIs** : Indicateurs clés de risque avec tendances
   - **Recommandations** : Actions recommandées
3. **Système** prévisualise le rapport
4. **Auditor** personnalise le rapport :
   - Ajoute des commentaires
   - Modifie les styles
   - Ajoute des graphiques
   - Ajoute des annexes
5. **Système** génère le rapport final (PDF)

**Étape 3 : Export et distribution**
1. **Auditor** exporte le rapport (PDF, Excel, Word)
2. **Système** archive le rapport
3. **Auditor** configure la distribution :
   - **Destinataires** : Client X, Direction, CA
   - **Format** : PDF
   - **Planification** : Envoi immédiat
4. **Système** envoie le rapport par email
5. **Système** enregistre dans l'audit trail

**Étape 4 : Consultation et actions**
1. **Client** consulte le rapport
2. **Client** analyse les risques et recommandations
3. **Client** prend des décisions basées sur le rapport
4. **Client** définit des plans d'action
5. **Système** suit l'avancement des actions

### 3.3 Résultat

**Rapport généré :** Oui (PDF, Excel, Word)
**Sections :** Vue d'ensemble, Matrice de risque, Risques détaillés, Contrôles, Incidents, Conformité, KRIs, Recommandations
**Destinataires :** Client X, Direction, CA
**Distribution :** Oui (email)
**Archivage :** Oui

---

## 4. Scénario 4 : Direction risques suit les KRIs

### 4.1 Contexte

**Utilisateur :** Direction risques
**Objectif :** Suivre les indicateurs clés de risque (KRIs) et générer des alertes
**Résultat attendu :** Dashboard KRIs, alertes automatiques, actions correctives

### 4.2 Workflow Détaillé

**Étape 1 : Définition des KRIs**
1. **Direction risques** définit des KRIs :
   - **KRI-001** : Taux de rotation des stocks (< 90 jours)
   - **KRI-002** : Taux de créances douteuses (< 5% des créances)
   - **KRI-003** : Taux de turnover du personnel (< 10% par an)
   - **KRI-004** : Taux de disponibilité des systèmes (> 99.5%)
   - **KRI-005** : Taux de conformité RGPD (> 95%)
2. **Système** configure les KRIs :
   - **Formule de calcul** : Formule pour calculer l'indicateur
   - **Source de données** : API, import, saisie manuelle
   - **Fréquence** : Quotidienne, hebdomadaire, mensuelle
   - **Seuils d'alerte** : Vert (< seuil), Jaune (≈ seuil), Orange (> seuil), Rouge (>> seuil)
3. **Système** enregistre les KRIs dans la base de données

**Étape 2 : Collecte de données**
1. **Système** collecte automatiquement les données :
   - **Via API** : Données depuis systèmes externes (ERP, CRM)
   - **Via import** : Import de fichiers CSV, Excel
   - **Via saisie manuelle** : Saisie par les utilisateurs
2. **Système** calcule les indicateurs :
   - **KRI-001** : Taux de rotation = 45 jours (< 90) → Vert ✅
   - **KRI-002** : Taux de créances douteuses = 3% (< 5%) → Vert ✅
   - **KRI-003** : Taux de turnover = 12% (> 10%) → Orange ⚠️
   - **KRI-004** : Taux de disponibilité = 98.5% (< 99.5%) → Orange ⚠️
   - **KRI-005** : Taux de conformité = 92% (< 95%) → Orange ⚠️
3. **Système** compare avec les seuils d'alerte
4. **Système** génère des alertes si seuils dépassés

**Étape 3 : Alertes et notifications**
1. **Système** génère des alertes :
   - **Alerte 1** : KRI-003 (Taux de turnover > 10%) → Orange
   - **Alerte 2** : KRI-004 (Taux de disponibilité < 99.5%) → Orange
   - **Alerte 3** : KRI-005 (Taux de conformité < 95%) → Orange
2. **Système** envoie des notifications :
   - **Email** : Notification par email aux responsables
   - **SMS** : Notification par SMS pour les alertes critiques
   - **Notifications in-app** : Notifications dans l'application
3. **Direction risques** consulte les alertes
4. **Direction risques** analyse les causes

**Étape 4 : Actions correctives**
1. **Direction risques** définit des actions correctives :
   - **Pour KRI-003** : Améliorer la rétention du personnel (formation, salaires)
   - **Pour KRI-004** : Améliorer la disponibilité des systèmes (maintenance, redondance)
   - **Pour KRI-005** : Améliorer la conformité RGPD (formation, processus)
2. **Système** crée des plans d'action
3. **Système** suit l'avancement
4. **Système** met à jour les KRIs après actions
5. **Système** génère des rapports de suivi

**Étape 5 : Dashboard et rapports**
1. **Direction risques** consulte le dashboard KRIs
2. **Système** affiche les graphiques et tendances
3. **Direction risques** analyse l'évolution des indicateurs
4. **Direction risques** exporte le dashboard (PDF, Excel)
5. **Système** génère des rapports périodiques

### 4.3 Résultat

**KRIs définis :** 5 KRIs
**Alertes générées :** 3 alertes (Orange)
**Actions correctives :** 3 plans d'action
**Dashboard :** Oui (graphiques, tendances)
**Rapports :** Oui (PDF, Excel)

---

## 5. Scénario 5 : Audit interne évalue la conformité ISO 31000

### 5.1 Contexte

**Utilisateur :** Audit interne
**Objectif :** Évaluer la conformité avec ISO 31000
**Résultat attendu :** Rapport de conformité, écarts identifiés, plan de remédiation

### 5.2 Workflow Détaillé

**Étape 1 : Sélection du cadre de conformité**
1. **Audit interne** navigue vers "Conformité"
2. **Audit interne** sélectionne "ISO 31000"
3. **Système** affiche les exigences ISO 31000 :
   - **Section 1** : Principes (5 exigences)
   - **Section 2** : Cadre (8 exigences)
   - **Section 3** : Processus (6 exigences)
   - **Total** : 19 exigences
4. **Système** affiche le statut de conformité pour chaque exigence

**Étape 2 : Évaluation de conformité**
1. **Audit interne** évalue chaque exigence :
   - **Exigence 1** : Principes de gestion des risques → Conforme ✅
   - **Exigence 2** : Cadre de gestion des risques → Partiellement conforme ⚠️
   - **Exigence 3** : Processus de gestion des risques → Conforme ✅
   - **Exigence 4** : Documentation → Non conforme ❌
   - **Exigence 5** : Amélioration continue → Partiellement conforme ⚠️
   - etc.
2. **Système** calcule le taux de conformité :
   - **Conformes** : 12 exigences (63%)
   - **Partiellement conformes** : 5 exigences (26%)
   - **Non conformes** : 2 exigences (11%)
   - **Taux de conformité global** : 74.7%
3. **Système** identifie automatiquement les écarts (gaps)

**Étape 3 : Plan de remédiation**
1. **Audit interne** définit un plan de remédiation pour chaque écart :
   - **Écart 1** : Documentation incomplète → Action : Compléter la documentation (Échéance : 2 mois)
   - **Écart 2** : Amélioration continue insuffisante → Action : Mettre en place un processus d'amélioration continue (Échéance : 3 mois)
2. **Système** crée des plans d'action
3. **Système** suit l'avancement
4. **Système** génère des alertes pour les échéances

**Étape 4 : Rapport de conformité**
1. **Système** génère automatiquement un rapport de conformité :
   - **Taux de conformité** : 74.7%
   - **Écarts identifiés** : 7 écarts (2 non conformes, 5 partiellement conformes)
   - **Plans de remédiation** : 7 plans d'action
   - **Recommandations** : Actions recommandées pour améliorer la conformité
2. **Audit interne** consulte le rapport
3. **Audit interne** exporte le rapport (PDF, Excel)
4. **Audit interne** partage le rapport avec la direction
5. **Direction** prend des décisions basées sur le rapport

### 5.3 Résultat

**Taux de conformité :** 74.7%
**Écarts identifiés :** 7 écarts
**Plans de remédiation :** 7 plans d'action
**Rapport généré :** Oui (PDF, Excel)
**Suivi :** Oui (avancement des actions)

---

## 6. Scénarios Additionnels

### 6.1 Scénario : Import de données depuis un système GRC existant

**Workflow :**
1. **Utilisateur** configure l'intégration avec un système GRC externe
2. **Système** synchronise les données (risques, contrôles, incidents)
3. **Système** mappe les données (champs source → champs cible)
4. **Système** valide et corrige les données
5. **Système** importe les données dans l'application
6. **Utilisateur** consulte les données importées
7. **Système** suit l'avancement

---

### 6.2 Scénario : Génération automatique de rapports périodiques

**Workflow :**
1. **Utilisateur** configure un rapport périodique (mensuel, trimestriel, annuel)
2. **Système** génère automatiquement le rapport à la date prévue
3. **Système** exporte le rapport (PDF, Excel)
4. **Système** envoie le rapport par email aux destinataires
5. **Système** archive le rapport
6. **Destinataires** consulte le rapport
7. **Destinataires** prennent des décisions basées sur le rapport

---

### 6.3 Scénario : Intégration avec PowerBI

**Workflow :**
1. **Utilisateur** configure l'intégration PowerBI
2. **Système** exporte les données vers PowerBI (via API REST)
3. **Système** met à jour les datasets PowerBI
4. **Utilisateur** consulte les dashboards PowerBI
5. **Système** synchronise automatiquement les données
6. **Utilisateur** personnalise les dashboards PowerBI

---

## 7. Métriques de Succès

### 7.1 Métriques Clés

**Utilisation :**
- Nombre d'utilisateurs actifs
- Nombre de risques créés
- Nombre d'évaluations effectuées
- Nombre de contrôles implémentés
- Nombre de rapports générés

**Efficacité :**
- Taux de résolution des risques
- Temps moyen de traitement
- Efficacité des contrôles
- Taux de conformité
- Satisfaction des utilisateurs

**Qualité :**
- Précision des évaluations
- Qualité des données
- Pertinence des recommandations
- Utilité des rapports

---

## 8. Optimisations Futures

### 8.1 IA et Machine Learning

**Prédiction des risques :**
- Prédiction des risques futurs basée sur l'historique
- Détection d'anomalies
- Classification automatique des risques
- Recommandations de contrôles

**Optimisation :**
- Optimisation des workflows
- Amélioration de l'expérience utilisateur
- Personnalisation de l'interface
- Automatisation des tâches répétitives

---

## 9. Documentation

### 9.1 Documentation Utilisateur

**Guides :**
- Guide d'utilisation
- Tutoriels vidéo
- FAQ
- Support technique

**Documentation technique :**
- Documentation des APIs
- Documentation des intégrations
- Documentation des workflows
- Documentation des scénarios métiers


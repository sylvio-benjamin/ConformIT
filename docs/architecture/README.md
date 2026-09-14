# Documentation Architecture - Plateforme SaaS de Gestion des Risques

## État réel du dépôt (lire en premier)

Les fichiers `01_` à `08_` ci-dessous sont une **cible produit historique**. Ils décrivent parfois Firebase, Redis, Celery, microservices ou un monorepo que **ce repository n’a pas**.

L’état livré P0–P10 est documenté ici :

| Fichier | Contenu réel |
|---------|----------------|
| [FIREBASE_MIGRATION.md](./FIREBASE_MIGRATION.md) | Inventaire Firebase → Neon (runtime déjà coupé) |
| [DATABASE.md](./DATABASE.md) | Neon, Alembic `0001`–`0007`, pas de couche `database/` |
| [ISO_DATA_SOURCES.md](./ISO_DATA_SOURCES.md) | Source officielle ISO Open Data (ODC-By) |
| [ISO_CATALOG.md](./ISO_CATALOG.md) | Catalogue Niveau A — métadonnées, pas les PDF |
| [ISO_APPLICABILITY.md](./ISO_APPLICABILITY.md) | Moteur d’applicabilité existant + lien catalogue |
| [EVALUATION_LAYERS.md](./EVALUATION_LAYERS.md) | Modèle figé : catalogue ≠ applicabilité ≠ évaluation |
| [STORAGE.md](./STORAGE.md) | `app.storage` → local / R2 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Next + FastAPI, secrets, GCP (révocation), checklist ops |
| [GO_LIVE_EVIDENCE.md](./GO_LIVE_EVIDENCE.md) | Preuves Go-Live (**NO-GO** infra ; code prêt) |
| [R2_GO_LIVE.md](./R2_GO_LIVE.md) | Procédure bucket R2 privé + tests A→B |
| [NEON_BACKUP_RESTORE.md](./NEON_BACKUP_RESTORE.md) | PITR / clone — [DOCUMENTED], pas [PASS] |
| [CI_CD_GO_LIVE.md](./CI_CD_GO_LIVE.md) | CI [PASS] définition ; CD [BLOCKED] |
| [GCP_SECRET_REVOCATION.md](./GCP_SECRET_REVOCATION.md) | Checklist humaine révocation Admin |
| [STORAGE_MIGRATION.md](./STORAGE_MIGRATION.md) | Inventaire local → R2 (0 fichier métier ici) |
| [../../PROJECT_AUDIT.md](../../PROJECT_AUDIT.md) | Baseline Go-Live figée + checklist exploitation |

Structure conservée : `src/app/employe`, `src/app/grc`, `backend/app/{main,api,core,models,services,storage,calculs}`. Pas de refonte.

---

## Vue d'ensemble (cible historique)

Cette documentation présente l'architecture complète de la plateforme SaaS de gestion des risques, conçue pour être modulaire, scalable et conforme aux normes ISO 31000, ISO 27005, COSO ERM, COBIT, SOX.

---

## 📚 Documents Disponibles

### 1. Architecture Fonctionnelle
**Fichier :** `01_ARCHITECTURE_FONCTIONNELLE.md`

**Contenu :**
- Modules fonctionnels (10 modules)
- Flux utilisateurs principaux
- Architecture technique (stack, microservices)
- Sécurité & conformité
- Intégrations externes
- Métriques & analytics
- Roadmap & versions

**Modules :**
- Registre des Risques (Risk Register)
- Évaluation & Scoring des Risques
- Contrôles/Mesures de Maîtrise
- Indicateurs Clés de Risque (KRIs) & Dashboards
- Incident/Événement Management
- Conformité & Normes GRC
- Intégrations Externes/API
- Rapports Automatiques
- Sécurité & Gouvernance
- Interface Pro UI/UX

---

### 2. Modèle de Données
**Fichier :** `02_MODELE_DONNEES.md`

**Contenu :**
- Schéma de base de données (PostgreSQL)
- Entités principales (Users, Organizations, Risks, Controls, Incidents, etc.)
- Relations entre entités
- Index et performances
- Contraintes et validations
- Migration et évolution
- Sécurité des données
- Backup et restauration

**Entités principales :**
- Users, Organizations, Roles, Permissions
- Risks, RiskCategories, RiskAssessments, RiskMatrices
- Controls, ActionPlans, ControlTests
- KRIs, KRIMetrics, KRIAlerts, Dashboards
- Incidents, RootCauseAnalyses, CorrectiveActions, PreventiveActions
- ComplianceFrameworks, ComplianceRequirements, ComplianceAssessments, ComplianceGaps
- ExternalIntegrations, APICredentials, DataSyncs
- Reports, ReportTemplates, ReportSchedules
- AuditLogs, SecurityPolicies

---

### 3. Arborescence UI/UX
**Fichier :** `03_UI_UX_ARBORESCENCE.md`

**Contenu :**
- Palette de couleurs (bleu foncé #003366, gris clair #F5F7FA, blanc, accent vert #00A859, orange #FF9F1C)
- Typographie (Inter/Roboto)
- Structure de navigation (Header, Sidebar, Footer)
- Pages principales (Dashboard, Risques, Contrôles, Incidents, Conformité, KRIs, Rapports, Intégrations, Paramètres)
- Composants UI réutilisables (Boutons, Formulaires, Tableaux, Cartes, Modales, Notifications)
- Responsive design (Mobile, Tablet, Desktop)
- Accessibilité (WCAG 2.1 Level AA)
- Performance (optimisations, métriques)
- Guidelines visuelles (simplicité, cohérence, professionnalisme)
- Thèmes et personnalisation
- Documentation et aide

---

### 4. Intégrations API & Externes
**Fichier :** `04_INTEGRATIONS_API.md`

**Contenu :**
- Intégrations externes (Infogreffe, INSEE, Dun & Bradstreet, PowerBI, APIs financières)
- Extraction IA de données (Groq, OCR, NLP)
- APIs REST internes (Risques, Contrôles, Incidents, Conformité, KRIs, Rapports, Intégrations)
- Webhooks (sortants, entrants)
- Authentification et sécurité (JWT, API Key, OAuth 2.0)
- Documentation API (Swagger/OpenAPI)
- Exemples d'utilisation
- Limites et quotas
- Gestion des erreurs
- Tests et validation
- Monitoring et logs
- Roadmap d'intégration

**Intégrations prévues :**
- **Infogreffe** : Données entreprises, RCS, bilans
- **INSEE** : Données économiques, indices sectoriels
- **Dun & Bradstreet** : Scoring crédit, données financières
- **PowerBI** : Export de données, dashboards (limité pour Pro, illimité pour Enterprise)
- **APIs financières** : Données de marché, indicateurs économiques

---

### 5. Workflows Critiques
**Fichier :** `05_WORKFLOWS_CRITIQUES.md`

**Contenu :**
- Workflow principal : Identification → Évaluation → Traitement → Suivi → Rapport
- Workflow Incident : Incident → Analyse → Actions
- Workflow Conformité : Conformité → Évaluation → Remédiation
- Workflow KRI : KRI → Collecte → Alerte → Action
- Scénarios métiers (5 scénarios détaillés)
- Automatisations
- Intégrations avec workflows externes
- Métriques et KPIs
- Optimisations
- Documentation

**Scénarios métiers :**
1. TPE importe son bilan comptable
2. ETI évalue ses risques opérationnels
3. Cabinet de conseil génère un rapport d'audit
4. Direction risques suit les KRIs
5. Audit interne évalue la conformité ISO 31000

---

### 6. Scénarios Métiers
**Fichier :** `06_SCENARIOS_METIERS.md`

**Contenu :**
- Scénario 1 : TPE importe son bilan comptable (workflow détaillé)
- Scénario 2 : ETI évalue ses risques opérationnels (workflow détaillé)
- Scénario 3 : Cabinet de conseil génère un rapport d'audit (workflow détaillé)
- Scénario 4 : Direction risques suit les KRIs (workflow détaillé)
- Scénario 5 : Audit interne évalue la conformité ISO 31000 (workflow détaillé)
- Scénarios additionnels (import de données, rapports périodiques, intégration PowerBI)
- Métriques de succès
- Optimisations futures
- Documentation

---

### 7. Planning de Versions
**Fichier :** `07_PLANNING_VERSIONS.md`

**Contenu :**
- MVP (v0.1) : Version minimale fonctionnelle (3-4 mois)
- Version 1.0 (v1.0) : Fonctionnalités complètes (4-6 mois après MVP)
- Version 2.0 (v2.0) : Analytics avancés et IA (6-8 mois après v1.0)
- Version 3.0+ (v3.0+) : Expansion internationale et plateforme ouverte (6-8 mois après v2.0)
- Stratégie de déploiement (déploiement progressif, gestion des versions)
- Métriques de succès (technique, fonctionnel, business)
- Risques et mitigation
- Documentation
- Support et maintenance

**Versions prévues :**
- **MVP (v0.1)** : Registre des risques, évaluation, contrôles de base, import de bilans, extraction IA
- **v1.0** : Tous les modules de base, intégrations externes, rapports avancés, 2FA, PowerBI limité
- **v2.0** : Analytics avancés, IA prédictive, personnalisation, collaboration, mobile, PowerBI illimité
- **v3.0+** : Expansion internationale, plateforme ouverte, marketplace

---

### 8. Tarification
**Fichier :** `08_TARIFICATION.md`

**Contenu :**
- Plan Basic (49 €/mois) : Pour TPE/PME (1-10 utilisateurs)
- Plan Pro (149 €/mois) : Pour ETI (10-50 utilisateurs)
- Plan Enterprise (sur devis) : Pour grandes entreprises (50+ utilisateurs)
- Intégration PowerBI (limité pour Pro, illimité pour Enterprise)
- Options et add-ons (support avancé, formation, stockage, API calls, PowerBI)
- Tarification annuelle (réduction de 17% pour l'annuel)
- Période d'essai (14 jours gratuit)
- Facturation (mensuelle ou annuelle)
- Politique de remboursement (30 jours)
- Migration et mises à niveau (gratuit)
- Support et SLA (email pour Basic, email + chat pour Pro, dédié 24/7 pour Enterprise)
- Conformité et certification (RGPD pour Basic et Pro, RGPD + ISO 27001 + SOC 2 pour Enterprise)

**Plans de tarification :**
- **Basic (49 €/mois)** : 50 risques, 25 contrôles, 10 rapports/mois, pas de PowerBI
- **Pro (149 €/mois)** : 500 risques, 250 contrôles, 50 rapports/mois, PowerBI limité (5 datasets, 10 dashboards)
- **Enterprise (sur devis)** : Illimité, PowerBI illimité, support dédié 24/7, SLA garanti

---

## 🎯 Objectifs de la Plateforme

### Objectifs Principaux

1. **Gestion Complète des Risques** : Identifier, évaluer, traiter et suivre tous les types de risques (financiers, opérationnels, cyber, conformité, réputation, chaîne d'approvisionnement, ESG)

2. **Conformité aux Normes** : Alignement sur les normes ISO 31000, ISO 27005, ISO 22301, COSO ERM, COBIT, SOX, RGPD

3. **Intégrations Externes** : Intégration avec Infogreffe, INSEE, Dun & Bradstreet, PowerBI, APIs financières

4. **Extraction IA de Données** : Utilisation de l'IA (Groq, OCR, NLP) pour extraire automatiquement les données depuis documents PDF

5. **Analytics Avancés** : Analytics, dashboards interactifs, KRIs, alertes automatiques

6. **Rapports Automatiques** : Génération automatique de rapports (PDF, Excel, Word, PowerPoint) pour audit, CA, comité risques

7. **Sécurité & Gouvernance** : RBAC, 2FA, audit trail, chiffrement, conformité RGPD

8. **Interface Pro UI/UX** : Interface moderne, professionnelle, intuitive, avec palette de couleurs corporate

---

## 🏗️ Architecture Technique

### Stack Technologique

**Frontend :**
- Next.js 14+ (React, TypeScript)
- Tailwind CSS (styling)
- shadcn/ui (composants UI)
- Recharts/Chart.js (graphiques)
- React Query (gestion d'état)
- Zustand (state management)

**Backend :**
- FastAPI (Python)
- PostgreSQL (base de données)
- Redis (cache, sessions)
- Celery (tâches asynchrones)
- Firebase (authentification, real-time)
- Groq API (IA, extraction de données)

**Infrastructure :**
- Docker (containerisation)
- Kubernetes (orchestration)
- AWS/Azure (cloud)
- Nginx (reverse proxy)
- Let's Encrypt (SSL)

### Architecture Microservices

**Services principaux :**
- API Gateway (point d'entrée unique, routage, authentification)
- Risk Service (gestion des risques, évaluations, scoring)
- Control Service (gestion des contrôles, plans d'action)
- Incident Service (gestion des incidents, événements)
- Compliance Service (conformité, normes, audits)
- Integration Service (intégrations externes, APIs)
- Report Service (génération de rapports)
- Notification Service (notifications, alertes)
- Analytics Service (analytics, dashboards, KRIs)

---

## 📊 Modèle de Données

### Entités Principales

**Organisations :**
- Organizations (organisations)
- Users (utilisateurs)
- Roles (rôles)
- Permissions (permissions)

**Risques :**
- Risks (risques)
- RiskCategories (catégories de risques)
- RiskAssessments (évaluations de risques)
- RiskMatrices (matrices de risque)
- RiskScores (scores de risques)

**Contrôles :**
- Controls (contrôles)
- RiskControls (risques-contrôles)
- ActionPlans (plans d'action)
- ControlTests (tests de contrôles)

**KRIs :**
- KRIs (indicateurs clés de risque)
- KRIMetrics (métriques KRI)
- KRIAlerts (alertes KRI)
- Dashboards (tableaux de bord)
- DashboardWidgets (widgets de tableau de bord)

**Incidents :**
- Incidents (incidents)
- IncidentRisks (incidents-risques)
- RootCauseAnalyses (analyses de cause racine)
- CorrectiveActions (actions correctives)
- PreventiveActions (actions préventives)

**Conformité :**
- ComplianceFrameworks (cadres de conformité)
- ComplianceRequirements (exigences de conformité)
- ComplianceAssessments (évaluations de conformité)
- ComplianceGaps (écarts de conformité)
- ComplianceRemediations (plans de remédiation)
- ComplianceAudits (audits de conformité)

**Intégrations :**
- ExternalIntegrations (intégrations externes)
- APICredentials (identifiants API)
- DataSyncs (synchronisations de données)

**Rapports :**
- Reports (rapports)
- ReportTemplates (modèles de rapports)
- ReportSchedules (planifications de rapports)

**Sécurité :**
- AuditLogs (logs d'audit)
- SecurityPolicies (politiques de sécurité)

---

## 🎨 Interface Utilisateur

### Palette de Couleurs

**Couleurs Corporate :**
- **Bleu foncé** : `#003366` (Primary) - Navigation, headers, boutons principaux
- **Gris clair** : `#F5F7FA` (Background) - Fond de page, cartes
- **Blanc** : `#FFFFFF` (White) - Fond de contenu, cartes
- **Gris foncé** : `#2C3E50` (Text) - Texte principal
- **Gris moyen** : `#7F8C8D` (Text Secondary) - Texte secondaire

**Couleurs d'Accent :**
- **Vert** : `#00A859` (Success) - Succès, conformité, risques faibles
- **Orange** : `#FF9F1C` (Warning) - Avertissements, risques moyens
- **Rouge** : `#E74C3C` (Danger) - Erreurs, risques critiques
- **Bleu** : `#3498DB` (Info) - Informations, liens

**Couleurs pour les Risques :**
- **Risque faible** : `#00A859` (Vert) - Score 0-30
- **Risque moyen** : `#FF9F1C` (Orange) - Score 31-60
- **Risque élevé** : `#FF6B35` (Orange foncé) - Score 61-80
- **Risque critique** : `#E74C3C` (Rouge) - Score 81-100

### Typographie

**Polices :**
- **Primaire** : Inter (sans-serif) - Corps de texte, interfaces
- **Secondaire** : Roboto (sans-serif) - Titres, éléments de navigation

**Tailles :**
- **H1** : 32px (2rem) - Titres principaux
- **H2** : 24px (1.5rem) - Titres de section
- **H3** : 20px (1.25rem) - Titres de sous-section
- **Body** : 16px (1rem) - Texte principal
- **Small** : 14px (0.875rem) - Texte secondaire
- **Caption** : 12px (0.75rem) - Légendes, labels

---

## 🔌 Intégrations Externes

### Intégrations Prévues

**Phase 1 (MVP) :**
- Infogreffe (import de bilans et comptes de résultat)
- Extraction IA (Groq, OCR, NLP)

**Phase 2 (v1.0) :**
- INSEE (données économiques et sectorielles)
- Dun & Bradstreet (scoring crédit et données financières)
- PowerBI (export de données et dashboards - limité pour Pro, illimité pour Enterprise)
- Webhooks (notifications en temps réel)

**Phase 3 (v2.0) :**
- APIs financières (données de marché et indicateurs économiques)
- IA prédictive (analyse prédictive des risques)
- Intégrations tierces (systèmes GRC existants)

---

## 📈 Workflows Critiques

### Workflow Principal

**Identification → Évaluation → Traitement → Suivi → Rapport**

1. **Identification** : Création d'un risque dans le registre
2. **Évaluation** : Évaluation de la probabilité et de l'impact, calcul du niveau de risque
3. **Traitement** : Définition de contrôles et plans d'action
4. **Suivi** : Suivi de l'avancement, réévaluation du risque
5. **Rapport** : Génération de rapports pour audit, CA, comité risques

### Scénarios Métiers

1. **TPE importe son bilan comptable** : Import PDF → Extraction IA → Calcul de ratios → Scoring de risque → Actions recommandées
2. **ETI évalue ses risques opérationnels** : Création de risque → Évaluation → Contrôles → Plans d'action → Suivi
3. **Cabinet de conseil génère un rapport d'audit** : Configuration → Génération → Export → Distribution
4. **Direction risques suit les KRIs** : Définition de KRIs → Collecte de données → Alertes → Actions correctives
5. **Audit interne évalue la conformité ISO 31000** : Sélection du cadre → Évaluation → Écarts → Plans de remédiation

---

## 📅 Planning de Versions

### MVP (v0.1) - 3-4 mois

**Fonctionnalités :**
- Registre des risques
- Évaluation & scoring
- Contrôles de base
- Import de bilans
- Extraction IA
- Rapports de base (PDF, Excel)

### Version 1.0 (v1.0) - 4-6 mois après MVP

**Fonctionnalités :**
- Tous les modules de base
- Intégrations externes (Infogreffe, INSEE, Dun & Bradstreet)
- Rapports avancés (Word, PowerPoint)
- 2FA
- PowerBI (limité pour Pro, illimité pour Enterprise)
- Webhooks
- APIs REST complètes

### Version 2.0 (v2.0) - 6-8 mois après v1.0

**Fonctionnalités :**
- Analytics avancés
- IA prédictive
- Personnalisation
- Collaboration
- Mobile (iOS, Android)
- PowerBI (illimité pour Enterprise)
- Intégrations avancées

---

## 💰 Tarification

### Plan Basic - 49 €/mois

**Pour :** TPE/PME (1-10 utilisateurs)
**Fonctionnalités :** 50 risques, 25 contrôles, 10 rapports/mois
**PowerBI :** Non inclus
**Support :** Email (48h)

### Plan Pro - 149 €/mois

**Pour :** ETI (10-50 utilisateurs)
**Fonctionnalités :** 500 risques, 250 contrôles, 50 rapports/mois
**PowerBI :** Inclus (limité : 5 datasets, 10 dashboards, synchronisation quotidienne)
**Support :** Email + Chat (24h)

### Plan Enterprise - Sur devis

**Pour :** Grandes entreprises (50+ utilisateurs)
**Fonctionnalités :** Illimité
**PowerBI :** Inclus (illimité : datasets, dashboards, rapports, synchronisation temps réel)
**Support :** Dédié 24/7 (4h)
**SLA :** Disponibilité > 99.9%, réponse < 4h
**Conformité :** RGPD + ISO 27001 + SOC 2

---

## 🚀 Prochaines Étapes

### Étapes Immédiates

1. **Valider l'architecture** : Revoir et valider l'architecture fonctionnelle et technique
2. **Prototyper l'interface** : Créer des prototypes UI/UX pour validation
3. **Développer le MVP** : Commencer le développement du MVP (v0.1)
4. **Tester les intégrations** : Tester les intégrations externes (Infogreffe, INSEE, Dun & Bradstreet, PowerBI)
5. **Documenter les APIs** : Documenter les APIs REST (Swagger/OpenAPI)

### Étapes à Moyen Terme

1. **Développer v1.0** : Développer la version 1.0 avec tous les modules de base
2. **Intégrer PowerBI** : Intégrer PowerBI (limité pour Pro, illimité pour Enterprise)
3. **Tester et optimiser** : Tester et optimiser les performances et la sécurité
4. **Former les utilisateurs** : Former les utilisateurs sur l'utilisation de la plateforme
5. **Lancer en production** : Lancer la plateforme en production

### Étapes à Long Terme

1. **Développer v2.0** : Développer la version 2.0 avec analytics, IA et personnalisation
2. **Expansion internationale** : Expansion internationale (multi-langues, multi-devises)
3. **Plateforme ouverte** : Créer une plateforme ouverte (APIs publiques, SDK, marketplace)
4. **Community** : Créer une communauté d'utilisateurs et de développeurs
5. **Innovation continue** : Innovation continue basée sur les feedbacks utilisateurs

---

## 📞 Contact et Support

### Support

**Email :** support@example.com
**Chat :** Disponible dans l'application (Pro et Enterprise)
**Documentation :** https://docs.example.com
**FAQ :** https://faq.example.com
**Community :** https://community.example.com

### Contact Commercial

**Email :** sales@example.com
**Téléphone :** +33 X XX XX XX XX
**Démo :** https://demo.example.com
**Essai gratuit :** https://try.example.com (14 jours, sans carte bancaire)

---

## 📝 Licence

**Licence :** Propriétaire (tous droits réservés)
**Utilisation :** Réservée aux clients ayant souscrit un abonnement
**Modification :** Interdite sans autorisation écrite
**Distribution :** Interdite sans autorisation écrite

---

## 🔄 Mises à Jour

**Dernière mise à jour :** 2024-01-15
**Version :** 1.0.0
**Auteur :** Équipe de Développement
**Révision :** Architecture complète de la plateforme SaaS de gestion des risques

---

## 📚 Références

### Normes et Cadres

- **ISO 31000** : Management du risque
- **ISO 27005** : Risque sécurité de l'information
- **ISO 22301** : Continuité d'activités
- **COSO ERM** : Framework de gestion des risques
- **COBIT** : Gouvernance IT
- **SOX** : Transparence financière
- **RGPD** : Protection des données

### Outils Inspirants

- **MetricStream ERM** : Multi-dimensional risk assessments, dashboards, analytics
- **Qoris ERM** : Aligné ISO 31000 & COSO 2017, automations risques
- **Cura ERM** : Intégration workflows, reporting, library de risques
- **Opture Risk Management** : Modularité, rapports automatiques, conformité des modules

---

## ✅ Checklist de Développement

### MVP (v0.1)

- [ ] Architecture et base de données
- [ ] Module Registre des Risques
- [ ] Module Évaluation & Scoring
- [ ] Module Contrôles/Mesures de Maîtrise
- [ ] Import de documents PDF
- [ ] Extraction IA de données (Groq)
- [ ] Analyse automatique des bilans
- [ ] Génération de rapports (PDF, Excel)
- [ ] Interface UI/UX de base
- [ ] Authentification (email/mot de passe)
- [ ] Tests et optimisations
- [ ] Documentation utilisateur

### Version 1.0 (v1.0)

- [ ] Module KRIs & Dashboards
- [ ] Module Incident/Événement Management
- [ ] Module Conformité & Normes GRC
- [ ] Intégration Infogreffe
- [ ] Intégration INSEE
- [ ] Intégration Dun & Bradstreet
- [ ] Intégration PowerBI (limité pour Pro, illimité pour Enterprise)
- [ ] Rapports avancés (Word, PowerPoint)
- [ ] 2FA (TOTP, SMS)
- [ ] Webhooks
- [ ] APIs REST complètes
- [ ] Tests et optimisations
- [ ] Documentation utilisateur complète

### Version 2.0 (v2.0)

- [ ] Analytics avancés
- [ ] IA prédictive
- [ ] Personnalisation
- [ ] Collaboration
- [ ] Mobile (iOS, Android)
- [ ] Intégrations avancées
- [ ] Tests et optimisations
- [ ] Documentation utilisateur complète

---

## 🎉 Conclusion

Cette documentation présente l'architecture complète de la plateforme SaaS de gestion des risques, conçue pour être modulaire, scalable et conforme aux normes ISO 31000, ISO 27005, COSO ERM, COBIT, SOX, RGPD.

La plateforme offre :
- **Gestion complète des risques** : Identification, évaluation, traitement, suivi, rapport
- **Conformité aux normes** : Alignement sur les normes ISO 31000, ISO 27005, COSO ERM, COBIT, SOX, RGPD
- **Intégrations externes** : Infogreffe, INSEE, Dun & Bradstreet, PowerBI, APIs financières
- **Extraction IA de données** : Utilisation de l'IA (Groq, OCR, NLP) pour extraire automatiquement les données depuis documents PDF
- **Analytics avancés** : Analytics, dashboards interactifs, KRIs, alertes automatiques
- **Rapports automatiques** : Génération automatique de rapports (PDF, Excel, Word, PowerPoint) pour audit, CA, comité risques
- **Sécurité & Gouvernance** : RBAC, 2FA, audit trail, chiffrement, conformité RGPD
- **Interface Pro UI/UX** : Interface moderne, professionnelle, intuitive, avec palette de couleurs corporate

La plateforme est disponible en 3 plans :
- **Basic (49 €/mois)** : Pour TPE/PME (gestion de base des risques)
- **Pro (149 €/mois)** : Pour ETI (gestion complète avec intégrations et PowerBI limité)
- **Enterprise (sur devis)** : Pour grandes entreprises (gestion avancée avec personnalisation, PowerBI illimité et support dédié)

**Intégration PowerBI :**
- **Plan Basic** : Non inclus (export manuel)
- **Plan Pro** : Inclus (limité : 5 datasets, 10 dashboards, synchronisation quotidienne)
- **Plan Enterprise** : Inclus (illimité : datasets, dashboards, rapports, synchronisation temps réel)

---

**Bonne chance avec le développement de la plateforme ! 🚀**


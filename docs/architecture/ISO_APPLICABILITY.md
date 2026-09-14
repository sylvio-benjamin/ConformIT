# Applicabilité ISO (Niveau B)

Le moteur existant **n’est pas remplacé**. Cette page documente son usage pour sélectionner un petit ensemble de normes **avant** toute analyse de contenu.

```text
Organization Profile
        ↓
Applicability Rules   (extensibles, table globale)
        ↓
Candidate / Applicable frameworks
        ↓
iso_deliverables filtrés (hors withdrawn)
        ↓
Analyse existante (P0–P10, inchangée)
```

---

## Profil organisation (existant)

Champs déjà persistés dans `organization_profiles` :

`sector`, `size`, `country`, `criticality`, `processes_personal_data`, `hosting`, `listed_company`, `notes`

Critères envisagés plus tard (colonne ou `condition` JSONB, **pas** une liste figée dans le code) :

`activities`, `health_data`, `financial_data`, `critical_infrastructure`, `information_security`, `quality_management`, `environment`, `business_continuity`, `privacy`, `supplier_requirements`, `certification_target`, `contractual_requirements`

On **n’ajoute pas** une énorme liste de règles arbitraires. Une nouvelle règle = une ligne `applicability_rules`.

---

## Règles

Table globale `applicability_rules` (`code`, `framework_code`, `condition` JSONB, `reason`).  
Seed actuel : `iso31000`, `rgpd`, `iso27005`, `cobit`, `sox`, `coso_erm`.

`condition` vide = toujours vrai (socle ISO 31000).  
Plusieurs règles sur le même `framework_code` = **OU**.

`evaluate_profile` (inchangé) : une raison + `source_rule`.  
`evaluate_profile_detailed` (additif) : toutes les raisons matchées, auditable.

Exemple :

```text
ISO 27005
Applicable = YES
Reasons:
- Criticité élevée des activités
- Hébergement cloud / hybride
```

```text
RGPD
Applicable = NO
Reasons:
- Aucun critère d'applicabilité détecté
```

Pas d’IA boîte noire pour cette sélection.

---

## Score

Le champ `confidence` existant reste un poids fixe de règle (0.85 / 0.5).  
Il n’est **pas** un score opaque. L’explication utile est `reason` / `reasons` + `source_rule(s)`.

Modèle conceptuel si on formalise plus tard :

```text
standard | criterion | condition | weight | reason
```

Aujourd’hui : `framework_code` + `condition` + `reason` suffisent.

---

## Isolation

| Donnée | Portée |
|--------|--------|
| Catalogue `iso_deliverables` | Globale (comme `kb_controls`) |
| Profil, décisions, preuves | `organization_id` |

```text
Organisation A  ≠  Organisation B
```

`GET /organizations/me/applicable-standards` utilise uniquement l’orga du JWT.  
Aucune décision A n’est renvoyée à B.

---

## UI

Pas de nouvelle interface. Réutiliser `/conformite` :

```text
Profil organisation
       ↓
Frameworks potentiellement applicables
       ↓
Pourquoi ? (reason)
       ↓
Sélection / validation métier (override déjà prévu en base)
```

---

## Niveau C — plus tard, sous licence

Procédure **future** uniquement, après achat / contrat ISO ou organisme national :

1. Conserver le PDF hors git, hors `app.storage` public.
2. Extraire les exigences licenciées vers une table distincte (pas `iso_deliverables`).
3. Lier `framework_code` + `iso_id` d’édition.
4. Ne jamais vectoriser un PDF sans droit de reproduction documenté.

Tant que cette licence n’existe pas : **[BLOCKED — LICENCE / ACTION HUMAINE]**.

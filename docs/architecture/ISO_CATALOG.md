# Catalogue ISO (Niveau A)

Le catalogue est un **référentiel de métadonnées**. Il n’est pas le moteur d’analyse et n’est pas le texte des normes.

```text
26 000+ références
        ↓
catalogue (iso_deliverables)
        ↓
profil organisation
        ↓
petit ensemble pertinent
        ↓
analyse approfondie (existante, inchangée)
```

---

## Inspection dépôt (avant ajout)

### EXISTANT

* Profil : `organization_profiles` (secteur, taille, pays, criticité, données perso, hébergement, cotation)
* Règles globales : `applicability_rules` + `app.services.applicability`
* Décisions orga : `applicability_decisions` (unique `organization_id` + `framework_code`)
* KB titres : `kb_controls` (pas de texte ISO)
* API : `/api/v1/organizations/me/profile|applicability` ; `/api/v1/kb/controls`
* UI : `/grc/compliance` (profil + raisons)
* Alembic `0001`–`0006` ; Neon ; FastAPI ; JWT

### MANQUANT (avant cette mission)

* Table catalogue ISO officielle
* Import ODC-By reproductible
* Lien `reference` → `framework_code` (`ISO 27001:2022` → `iso27001`)
* Documentation sources / droits

### À AJOUTER (fait, additif)

* `iso_deliverables` (Alembic `0007_iso_catalog`)
* `app.services.iso_catalog` + `scripts/import_iso_catalog.py`
* `GET /api/v1/kb/iso-standards` (catalogue global)
* `GET /api/v1/organizations/me/applicable-standards` (filtré par l’orga courante)

### À NE PAS TOUCHER

* P0–P10, pipeline `/analyser/`, Next.js, JWT, Neon, `app.storage`
* `evaluate_profile` (contrats / tests existants)
* Firebase, Redis, Celery, Docker, monorepo
* Textes ISO, embeddings, scrapers

---

## Modèle (champs dérivés du CSV officiel)

```text
IsoDeliverable
├── iso_id                 ← id officiel
├── reference
├── title_en / title_fr
├── edition
├── publication_date
├── current_stage
├── withdrawn              ← dérivé de currentStage ≥ 95.00 ou 90.99
├── technical committee    ← ownerCommittee
├── ICS                    ← icsCode
├── replaces / replaced_by
├── languages
├── pages_en
├── scope_en               ← résumé open data, pas le PDF
├── framework_code         ← dérivé de reference (lien Niveau B)
├── official_source
└── metadata_source
```

Pas de `organization_id` : Knowledge Base globale, comme `kb_controls`.  
Pas de champ « exigences » / « clauses » : ce serait le Niveau C.

`withdrawal_date` n’existe pas dans le CSV : non ajouté.

---

## Trois niveaux

| Niveau | Contenu | Table / service | Droits |
|--------|---------|-----------------|--------|
| **A — Catalogue** | Métadonnées publiques ODC-By | `iso_deliverables` | Attribution ODC-By |
| **B — Applicabilité** | Pourquoi une norme est pertinente | profil + règles + décisions | Données client, isolées par orga |
| **C — Contenu normatif** | Texte / exigences détaillées | *non implémenté* | **[BLOCKED — LICENCE / ACTION HUMAINE]** |

Le catalogue **ne calcule rien**. `scope.en` n’est **pas** une exigence.  
Voir [EVALUATION_LAYERS.md](./EVALUATION_LAYERS.md).

---

## Import

```bash
# Fixture uniquement (recommandé d’abord)
python scripts/import_iso_catalog.py --source backend/tests/fixtures/iso_deliverables_sample.csv

# CSV officiel, dry-run, 20 lignes
python scripts/import_iso_catalog.py --official --limit 20

# Après validation staging — jamais à l’aveugle en production
python scripts/import_iso_catalog.py --source iso_deliverables_metadata.csv --apply
```

Idempotent par `iso_id`. Les normes retirées restent en base avec `withdrawn=true`.  
Le moteur d’analyse **n’utilise pas** le catalogue complet.

---

## API

* `GET /api/v1/kb/iso-standards` — JWT, catalogue global, pas de fuite orga
* `GET /api/v1/organizations/me/applicable-standards` — JWT, décisions + métadonnées de **cette** orga

Aucune nouvelle UI : `/conformite` (page GRC existante) affiche profil → décisions → raisons → métadonnées catalogue si importées.

---

## Limites

* `scope.en` n’est pas le texte de la norme.
* `framework_code` ne mappe que les références `ISO … <numéro>`.
* L’import production du fichier ~60 Mo n’est **pas** exécuté ici.
* Alembic `0007` n’est pas un feu vert Go-Live.

# Sources de données ISO

Ce document ne décrit **que** les sources officielles. Aucune API n’est inventée. Aucun scrape tiers.

---

## Portail officiel

| Élément | Valeur constatée |
|---------|------------------|
| Portail | [https://www.iso.org/open-data.html](https://www.iso.org/open-data.html) |
| Licence catalogue | [ODC-By 1.0](https://opendatacommons.org/licenses/by/1-0/) |
| Hébergement fichiers | Azure Blob `isopublicstorageprod.blob.core.windows.net/opendata/` |
| Jeu principal | `iso_deliverables_metadata` |

**Attribution requise (ODC-By) :**  
« Contains information from ISO Open Data, made available under the ODC Attribution License. »

Le portail ISO liste aussi :

* `iso_technical_committees` (mise à jour **hebdomadaire**)
* `iso_ics` (rare ; édition ICS 7, 2025)

Ces deux jeux **ne sont pas encore importés**. Leurs URL de fichier doivent être lues sur le portail, pas devinées.

---

## Fichier catalogue vérifié

Le portail annonce Parquet / JSONLines / CSV.

**Seul le CSV a été vérifié HTTP 200** (13 septembre 2026, `Content-Length` 59 759 190, `Last-Modified` 2026-09-09, `x-ms-meta-run_time` 2026-09-09T00:42:06) :

```text
https://isopublicstorageprod.blob.core.windows.net/opendata/_latest/iso_deliverables_metadata/csv/iso_deliverables_metadata.csv
```

Fréquence annoncée par ISO pour ce jeu : **quotidienne**.

Un chemin JSONL deviné (`…/jsonl/iso_deliverables_metadata.jsonl`) a renvoyé **404**.  
**Ne pas inventer l’URL JSONL/Parquet.** Utiliser le bouton de téléchargement du portail.

---

## En-tête CSV réellement observé

```text
id,deliverableType,supplementType,reference,title.en,title.fr,publicationDate,edition,icsCode,ownerCommittee,currentStage,replaces,replacedBy,languages,pages.en,scope.en
```

| Champ officiel | Usage ConformIT | Identifiant / statut |
|----------------|------------------|----------------------|
| `id` | `iso_id` PK | **Identifiant unique ISO** |
| `reference` | `ISO/IEC 27001:2022` | Conservation telle quelle |
| `title.en` / `title.fr` | Titres | Métadonnées |
| `edition` | Édition | |
| `publicationDate` | Date de publication | |
| `currentStage` | Statut (codes harmonisés) | `6060` publié ; `9599` retiré |
| `ownerCommittee` | Comité technique | |
| `icsCode` | Classification ICS | |
| `replaces` / `replacedBy` | Relations d’édition | |
| `languages` | Langues du livrable | |
| `pages.en` | Pagination EN | |
| `scope.en` | Résumé officiel court **inclus dans l’open data** | **Pas** le corps de la norme |
| `deliverableType` / `supplementType` | Type (IS, TR, Amd…) | |

**Non disponible dans ce CSV (ne pas inventer) :**

* date de retrait dédiée (on dérive `withdrawn` de `currentStage`)
* texte intégral, clauses, exigences
* prix, URL d’achat garantie
* mappings sectoriels d’applicabilité

---

## Ce qui n’est PAS une source Open Data

| Source | Rôle | Licence contenu |
|--------|------|-----------------|
| ISO Store / boutiques nationales | Achat des PDF | **[BLOCKED — LICENCE / ACTION HUMAINE]** |
| ISO Online Browsing Platform (OBP) | Consultation en ligne | Pas un droit de stockage SaaS |
| Copies pirates / scrapers | Interdit | Ne jamais utiliser |

---

## Import reproductible

```text
source officielle (CSV)
      ↓
scripts/import_iso_catalog.py
      ↓
validation / normalisation
      ↓
upsert par iso_id
      ↓
table iso_deliverables
```

Dry-run par défaut. `--official` télécharge le CSV métadonnées (~60 Mo), **jamais** les PDF.  
`--apply` uniquement après validation fixture → staging. **Pas d’import massif production dans cette mission.**

---

## Données non disponibles aujourd’hui

* URL JSONL/Parquet officielle non confirmée par HTTP
* Jeux comités / ICS non inspectés ligne à ligne
* Licence SaaS pour le **texte** des normes : **[BLOCKED — LICENCE / ACTION HUMAINE]**

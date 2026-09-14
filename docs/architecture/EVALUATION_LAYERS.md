# Contrat d’architecture de référence (figé, sans réinterprétation)

> **Le catalogue sait. L’applicabilité décide du périmètre. L’évaluation constate. Le scoring mesure.**

1. **Catalogue** → connaît les référentiels et leurs métadonnées.
2. **Applicabilité** → détermine le périmètre pertinent pour l’organisation et explique pourquoi.
3. **Évaluation** → constate des faits via des questions/conditions et produit des `RULE-*`.
4. **Scoring** → agrège les impacts par familles puis calcule le score global `/100`.

**Extraire ≠ évaluer ≠ scorer.**

```text
PDF → texte → normalisation → extractor du référentiel
 → faits typés + preuves → conditions → OUI / NON / INCONNU / valeur
 → RULE-* → findings → aggregate_from_rules()
```

L’IA n’est pas une autorité sémantique. Elle n’intervient qu’en fallback, si un fait attendu n’a pas pu être lu localement.

Nouveau référentiel = nouvel extracteur dans `EXTRACTORS`, même contrat de sortie, même moteur.

```text
EXTRACTORS
    ├── Kbis
    ├── Comptes
    └── ISO 27001 (plus tard, licence)
         ▼
      FactSet → Questions → RULE-* → Findings → aggregate_from_rules()
```

Frontières : Extractor (faits) · Question (condition) · Rule (impact) · Scoring (agrégat) · Mistral (fallback) · OCR (amont) · Applicabilité (périmètre) · Catalogue (description).

## Invariants

* `aggregate_from_rules` est **agnostique au référentiel**.
* Même mécanique de scoring pour Kbis, ISO 27001, RGPD, ISO 31000, etc.
* **Niveau C** apporte de nouvelles sources de règles ; il ne crée pas de moteur parallèle.
* `scope.en` est **strictement informatif** : jamais question, exigence, `RULE-*`, finding ou score.
* **P0–P10 sont fermés** : aucune modification du moteur de calcul.
* L’extension future porte sur les **référentiels, questions, conditions et règles**, pas sur la mécanique de scoring.
* Un mot trouvé n’est jamais directement une réponse.
* L’absence de preuve produit **INCONNU**, pas une supposition. INCONNU n’est pas une erreur.
* Lien : **référentiel → applicabilité → questions/faits → règles/findings → impacts → familles → score global**

Ajouter ISO 27001 demain **ne doit nécessiter aucune modification** de `aggregate_from_rules` aujourd’hui.

**On n’améliore pas le moteur en ajoutant de l’intelligence ; on l’étend en ajoutant des connaissances structurées.**

Nouveau document → nouvel `EXTRACTOR`. Nouvelle question → nouvelle condition. Nouveau cas → nouvelle `RULE-*`. **Le scoring ne bouge pas.**

**Un document ne produit pas une vérité complète ; il produit un ensemble de constats justifiables par ses preuves.**

Garanties : pas d’invention · pas de pénalité artificielle · pas de dérive du moteur.

Démonstrateurs additifs : Kbis, Comptes. ISO 27001 suivra le même agrégateur.

**Figé.** Contrainte de référence : **Connaissance ou moteur ?**

```text
Oui → EXTRACTOR → FactSet → condition → RULE-* → applicabilité si nécessaire
Non → exception architecturale → justification → tests
```

`aggregate_from_rules()` reste **invariant et agnostique**. La provenance du `RULE-*` est sans effet : seules **famille + impact** comptent.

`INCONNU` est une sortie valide ; il ne doit jamais être transformé artificiellement en constat. Tout constat reste justifiable par une preuve du document.

Toute évolution enrichit d’abord les connaissances, avant d’envisager de toucher au moteur.

Le type de document est un **contexte explicite** fourni en amont (`type_hint` utilisateur), pas une déduction du moteur. Il oriente l’EXTRACTOR et les questions, puis une vérification structurelle minimale (sans Mistral) accepte ou refuse le PDF. Le sélecteur réduit l’inconnu structurel ; il ne supprime pas l’inconnu documentaire (`INCONNU`).

Toute évolution répond à : **est-ce que j’ajoute une connaissance, ou est-ce que je modifie le moteur ?** La seconde est une exception. P0–P10 restent fermés.

Aucun nouveau document, aucune nouvelle question, aucune nouvelle norme ne doit modifier `aggregate_from_rules()`.

**attendu ≠ nécessaire.** Un système robuste distingue : fait démontré · explicitement absent · indéterminable · non applicable.

Les cas ambigus restent ambigus. Q16 (modification du siège) est le test philosophique : preuve absente → `INCONNU` → pas de conclusion → pas d’invention. Sur les comptes, Q6/Q13 (séries N-1) suivent la même discipline.

**Nouveau référentiel ≠ nouveau moteur.**  
**Nouveau référentiel = nouvelles sources de règles pour le moteur existant.**

P0–P10 restent fermés.

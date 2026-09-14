# Révocation clé Admin Firebase / GCP

**Statut :** [MANUAL]

Cet agent **n’a pas** révoqué de clé. Le runtime ConformIT n’utilise plus Firebase Admin.  
Le fichier `backend/app/firebase_key.json` n’est plus dans le code ; `.gitignore` contient `**/firebase_key.json`.

---

```text
[MANUAL]

1. Ouvrir le projet GCP historique (celui qui hébergeait le compte de service Firebase Admin).
2. Identifier la clé Admin Firebase historique (IAM → comptes de service → clés JSON).
3. Révoquer / désactiver la clé (et le compte de service s’il ne sert plus à rien).
4. Vérifier les autres copies :
   - CI (GitHub Actions secrets / variables)
   - hébergeur (env vars)
   - secrets managers
   - machines locales
   - anciens backups de repo
5. Vérifier qu’aucun runtime ConformIT ne l’utilise :
   - pas de firebase-admin dans requirements.txt
   - rg firebase_key / firebase-admin = 0 dans src/ et backend/app/
```

**Comment prouver que c’est fait :** capture ou note datée dans `GO_LIVE_EVIDENCE.md` section 10 (sans coller la clé). Tant que ce n’est pas fait : rester [MANUAL] / [BLOCKED], jamais [PASS].

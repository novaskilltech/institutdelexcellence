# Architecture Niveau 2 — Administration Web & Raccordement ChatGPT

## 1. Principes directeurs
- **Continuité avec le Niveau 1** : Le site public reste statique (rapide, indexable, hébergé sur Vercel) pour préserver le coût nul et la disponibilité maximale.
- **Zéro secret dans GitHub** : Toute clé API ou jeton GitHub/Supabase vit uniquement dans les variables d’environnement Vercel / Supabase Edge Functions.

## 2. Espace d’administration sécurisé (PC & Téléphone)

### Option recommandée : Admin Web léger + Supabase + GitHub Dispatch
| Composant | Rôle | Pourquoi ce choix |
|---|---|---|
| **Supabase Auth** | Authentification admin (email + mot de passe / MFA / Magic Link) | Évite de coder un système d’auth maison ; RBAC simple (1 compte éditeur/admin). |
| **Supabase Postgres** | Table `books` (brouillons, validés, ordre, métadonnées) + table `download_events` (comptage anonymisé sans PII) | Permet d’enregistrer des brouillons, réorganiser le catalogue et consulter les stats. |
| **Supabase Storage** | Bucket privé `drafts` (PDF + couvertures avant publication) | Upload direct depuis navigateur mobile ou PC. |
| **Vercel / Edge Function** | Route protégée `/api/publish` qui vérifie le JWT admin, dépose le PDF validé dans `nouveaux-livres/a-publier/` via l’API GitHub (`Contents API`), puis déclenche le workflow `publish.yml` | Réutilise 100 % du pipeline Niveau 1 (couvertures, OG 1200×630, sitemap, déploiement Vercel). |

### Alternative ultra-simple (sans base de données)
- **Decap CMS / Pages CMS** branché sur GitHub OAuth : interface web responsive pour éditer `livres.json` et uploader un PDF directement sur GitHub depuis un téléphone, sans serveur ni base de données (mais sans brouillons privés hors Git ni statistiques de téléchargement).

## 3. Intégration avec ChatGPT (NOVASKILL EDITION 2)

### Contraintes techniques réelles
- ChatGPT **ne peut pas** écrire directement sur votre disque dur Windows (`D:\Projects\...`).
- La « Bibliothèque » interne de ChatGPT **n’expose pas** d’API publique permettant à un script externe d’aller y chercher vos PDF automatiquement.

### Deux passerelles réellement fonctionnelles
1. **Passerelle A — Custom GPT avec Action (1 clic depuis ChatGPT)** :
   - Vous créez un GPT dédié « Éditeur Institut de l’Excellence ».
   - Une **Action** (OpenAPI) appelle votre endpoint sécurisé (Supabase Edge Function ou API Vercel protégée par clé Bearer) avec les métadonnées validées (`titre`, `accroche`, `description`, `categorie_id`, `collection`) et le lien de téléchargement du PDF généré, ou envoie le `.meta.json` prêt à l’emploi.
2. **Passerelle B — Dépôt cloud synchronisé (PC & Téléphone)** :
   - Vous téléchargez le PDF depuis ChatGPT (sur téléphone ou PC) dans un dossier synchronisé (OneDrive / Google Drive) relié à `nouveaux-livres/brouillons/` (pour relecture) puis vous le déplacez dans `nouveaux-livres/a-publier/` une fois validé.

## 4. Plan de développement progressif & Estimation des coûts

| Phase | Contenu | Coût récurrent estimé |
|---|---|---|
| **Niveau 1 (Actuel)** | Dossier `nouveaux-livres/` + Git + GitHub Actions + Vercel Hobby | **0 €/mois** (GitHub Free : 2 000 min Actions/mois ; Vercel Hobby gratuit pour usage non commercial) |
| **Niveau 2A (Admin & Stats)** | Supabase Free Tier (500 Mo DB, 1 Go Storage, 50 000 MAU) + route `/api/publish` | **0 €/mois** au démarrage (puis ~25 $/mois Supabase Pro si > 1 Go de PDF ou besoin de sauvegardes quotidiennes automatiques) |
| **Niveau 2B (Action ChatGPT)** | Endpoint OpenAPI pour recevoir les métadonnées depuis votre GPT | **0 €/mois** (inclus dans Vercel / Supabase) |
| **Nom de domaine** | Ex. `.fr` ou `.org` (optionnel) | **~10–15 €/an** |

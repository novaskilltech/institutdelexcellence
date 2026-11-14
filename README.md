# Institut de l’Excellence — Site officiel de la maison d’édition

Une bibliothèque statique en français, **gratuite pour les lecteurs**, prête pour un hébergement sur Vercel, Netlify ou tout hébergement statique. Elle est sans compte utilisateur, sans base de données, sans transaction et sans publicité.

## Contenu initial

Cinq ouvrages et leurs vrais PDF, avec couvertures extraites des fichiers. Chaque livre dispose de sa page individuelle, d’un résumé, du nombre de pages, d’un bouton de lecture, d’un lien de téléchargement et d’un bouton de partage.

## Utilisation

- Ouvrir `index.html` pour prévisualiser la page sur ordinateur ; les liens vers les PDF fonctionnent hors ligne.
- Pour publier sur Vercel : importer ce dossier complet dans un projet statique (framework « Other »), sans commande de compilation. **Il faut déposer tout le dossier, y compris `pdfs/`**, et pas seulement le fichier HTML.
- Lorsqu’une URL de publication est connue, installer Python, `pymupdf` et `pillow` puis exécuter :

```bash
pip install pymupdf pillow
python build.py --site-url https://votre-domaine.fr
```

Cette commande génère toutes les pages, les métadonnées `og:image` et `og:url` avec des URL absolues pour les partages, ainsi que le `sitemap.xml`. Redéployer ensuite les fichiers mis à jour.

## Ajouter un livre

1. Copier le PDF dans le dossier `pdfs/`, par exemple `pdfs/mon-livre.pdf`.
2. Ajouter une entrée dans `livres.json` avec un `slug` unique, un titre, une description, une collection, une catégorie, `categorie_id`, `pages`, `date` et `pdf`. Les catégories proposées sont `histoires`, `priere`, `education`, `coran`, `fiqh` (adapter la liste des filtres dans `build.py` si besoin).
3. Exécuter `python build.py --site-url https://votre-domaine.fr` puis redéployer. La couverture est extraite de la première page du PDF (si aucune miniature n’existe déjà). Une image de partage 1200 × 630 px est également générée.

## Important

- Le site est **statique** : il n’a pas encore d’espace administrateur sécurisé pour ajouter des ouvrages directement depuis le téléphone. L’ajout se fait pour l’instant en modifiant le catalogue et en redéployant le site.
- Lecture gratuite ne veut **pas** dire abandon des droits d’auteur. Les PDF conservent leurs mentions de droits.
- Les métadonnées OpenGraph par livre fonctionneront après la configuration du domaine public dans `build.py`.
- Aucun contact ou domaine n’a été inventé. Ils pourront être ajoutés quand ils seront choisis.
- Les polices Google Fonts sont optionnelles : le site fonctionne avec les polices de remplacement sans connexion.

## Dépôt GitHub

Dépôt cible : **https://github.com/novaskilltech/institutdelexcellence** (branche `main`).

Pour importer tous les fichiers sans terminal, ouvrir le dépôt dans GitHub, cliquer sur « uploading an existing file » (ou « Add file » → « Upload files »), puis glisser **le contenu extrait** de cette archive : `index.html`, `livres.json`, `assets/`, `livres/`, `pdfs/`, etc. Vérifier que l'arborescence des sous-dossiers est respectée et valider avec « Commit changes ».

Avec Git installé :
- **Windows PowerShell** : depuis le dossier extrait, exécuter `./scripts/publier-github.ps1` (une connexion GitHub peut être demandée).
- **macOS/Linux** : depuis le dossier extrait, exécuter `sh scripts/publier-github.sh`.

Les ouvrages PDF sont stockés dans le dépôt, non via Git LFS : chaque fichier est inférieur à la limite standard de GitHub. Ne pas publier de clés API ni de données personnelles dans ce dépôt public.

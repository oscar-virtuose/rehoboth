# Rehoboth Skills Academy — site dynamique

Site Flask qui reprend le site statique d'origine. Le contenu est dans
`content/site.json`, les demandes d'inscription sont enregistrées dans SQLite
et consultables dans une administration protégée.

## Structure

| Chemin | Rôle |
|---|---|
| `app.py` | Routes, formulaire, administration, sitemap, robots |
| `content/site.json` | Tout le texte éditable : coordonnées, formations, formules, FAQ, pages |
| `templates/` | Gabarits Jinja (`base.html` contient l'en-tête, le pied et le SEO) |
| `static/` | Feuille de style, icônes, aperçu de partage, tuteur de frappe |
| `data/inscriptions.db` | Base SQLite créée automatiquement au premier lancement |

## Lancer en local

```bash
pip install -r requirements.txt
ADMIN_PASSWORD="choisissez-un-mot-de-passe" python app.py
```

Puis ouvrir http://localhost:5000.

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `SITE_URL` | `http://localhost:5000` | Adresse publique (balises `og:image`, sitemap, canonical) |
| `ADMIN_PASSWORD` | vide | Mot de passe de `/admin`. Si vide, l'administration est désactivée |
| `ADMIN_USER` | `admin` | Identifiant de `/admin` |
| `SECRET_KEY` | aléatoire | Clé des sessions (jeton CSRF). **À fixer en production**, sinon chaque processus gunicorn a sa propre clé |
| `HTTPS` | `0` | Mettre `1` derrière HTTPS pour activer le cookie de session sécurisé |
| `DATABASE` | `data/inscriptions.db` | Chemin de la base SQLite |
| `SMTP_HOST` | `smtp.gmail.com` | Serveur SMTP utilisé pour envoyer les demandes à l’Académie |
| `SMTP_PORT` | `587` | Port SMTP |
| `SMTP_USER` | vide | Identifiant du compte d’envoi |
| `SMTP_PASSWORD` | vide | Mot de passe d’application SMTP ; ne pas le stocker dans le code |
| `SMTP_SENDER` | valeur de `SMTP_USER` | Adresse expéditrice facultative |
| `SMTP_USE_SSL` | `0` | Mettre `1` pour une connexion SMTP SSL directe (généralement port 465) |

L’envoi des demandes nécessite ces paramètres SMTP. Pour Gmail, utiliser
`smtp.gmail.com`, le port `587`, et un mot de passe d’application. Sans
configuration SMTP valide, la demande n’est pas enregistrée et un message
d’erreur explicite est affiché.

Sous PowerShell, définir les identifiants avant de lancer l’application :

```powershell
$env:SMTP_USER = "rehobothskillsacademy@gmail.com"
$env:SMTP_PASSWORD = "votre-mot-de-passe-d-application"
python app.py
```

## Mettre en production

```bash
SITE_URL=https://votre-domaine HTTPS=1 SECRET_KEY=... ADMIN_PASSWORD=... gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

Placer le service derrière un proxy HTTPS (Nginx, Caddy, ou l'hébergeur) et
sauvegarder régulièrement le fichier `data/inscriptions.db`.

## Modifier le contenu

Éditer `content/site.json`. Le site relit le fichier automatiquement à la
prochaine requête, sans redémarrage. Les champs entre crochets
(horaires, durée de conservation) sont à compléter avant la mise en ligne.

Pour ajouter une formation, ajouter un objet dans `formations` avec un `slug`
unique. Elle apparaît dans la page Formations, dans le formulaire et dans
`/api/formations`. Mettre `"accueil": true` pour l'afficher sur l'accueil.

## Parcours d'inscription

1. Le visiteur remplit `/contact#inscription`. Une formation peut être
   présélectionnée par l'URL, par exemple `/contact?formation=access`.
2. Le serveur valide les champs et enregistre la demande avec un jeton aléatoire.
3. Le visiteur est redirigé vers `/merci/<jeton>`, qui propose le message
   WhatsApp prêt à envoyer. Le jeton empêche de consulter les demandes des autres.
4. Un champ piège (`website`) filtre une partie des robots.

## Administration

- `/admin` : liste des demandes, filtre par statut, changement de statut.
- `/admin/export.csv` : export CSV (séparateur `;`, compatible Excel).
- Authentification HTTP Basic et jeton CSRF sur chaque changement de statut. Utiliser HTTPS en production.

## Points à traiter avant la mise en ligne

- Limiter le nombre d'envois du formulaire (par exemple avec Nginx `limit_req`)
  pour éviter le spam.
- Les changements de statut de l'administration sont protégés par jeton CSRF.
  Le formulaire d'inscription public n'en a pas besoin, car il n'agit pas sur des données existantes.
- Le code du tuteur de frappe (`static/tuteur-frappe.html`) reste autonome et
  n'a pas été modifié. Son code PIN n'est pas une protection réelle (voir l'analyse précédente).
- Le lien Facebook pointe encore vers une recherche : remplacer `contact.facebook` dans `site.json`.

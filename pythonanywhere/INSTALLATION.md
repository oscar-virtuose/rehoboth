# Installation et mise à jour sur PythonAnywhere

Ce guide remplace la méthode « téléverser un zip ». Après l'installation, le travail quotidien se fait dans VS Code : tu modifies, tu envoies sur GitHub, puis tu lances une commande sur PythonAnywhere.

Remplace partout `NOM_UTILISATEUR` par ton nom d'utilisateur PythonAnywhere (pour toi, `syziph`).

---

## Partie 1 : préparer GitHub (depuis VS Code)

1. Sur github.com, créer un dépôt **privé** nommé `rehoboth`.
2. Dans VS Code, ouvrir le dossier du projet, puis dans le terminal :

```bash
git init
git add .
git commit -m "Version initiale du site"
git branch -M main
git remote add origin https://github.com/TON_COMPTE/rehoboth.git
git push -u origin main
```

Le fichier `.gitignore` empêche d'envoyer `data/`, les sauvegardes et les secrets. Vérifie avant le premier `push` avec `git status` que `data/` n'apparaît pas.

---

## Partie 2 : installer sur PythonAnywhere (une seule fois)

Ouvrir une **console Bash** sur PythonAnywhere.

### 2.1 Conserver la base actuelle

Le site tourne déjà depuis un zip. Sa base d'inscriptions est précieuse : on la met de côté avant de passer à Git.

```bash
cd ~
mv rehoboth rehoboth-zip-ancien
```

### 2.2 Récupérer le dépôt

```bash
git clone https://github.com/TON_COMPTE/rehoboth.git rehoboth
cp -r ~/rehoboth-zip-ancien/data ~/rehoboth/data
```

Si le dépôt est privé, GitHub demande une authentification. La solution la plus sûre est une **clé de déploiement** (SSH) ; une alternative plus simple est un jeton d'accès personnel GitHub, à utiliser dans l'URL de clonage. Dans les deux cas, ne le colle jamais dans un fichier du dépôt.

### 2.3 Créer l'environnement Python

```bash
mkvirtualenv --python=/usr/bin/python3.14 rehoboth   # ou 3.12 si 3.14 n'est pas proposé
pip install -r ~/rehoboth/requirements.txt
```

Choisis la version disponible avec `ls /usr/bin/python3*` : 3.12 ou 3.14 conviennent. Vérifie ensuite que l'environnement fonctionne avec `python --version` et `python tests/test_site.py`.

### 2.4 Créer le fichier de configuration (secrets)

```bash
cp ~/rehoboth/pythonanywhere/rehoboth.env.modele ~/rehoboth.env
nano ~/rehoboth.env
chmod 600 ~/rehoboth.env
```

Remplace les valeurs : `NOM_UTILISATEUR`, `ADMIN_PASSWORD`, `PA_TOKEN` et `SECRET_KEY`.

Pour générer la clé secrète :

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Pour obtenir le jeton API : onglet **Account** → section **API token** → *Create a new API token*.

Ce fichier reste sur le serveur. Il n'est pas dans Git, donc il ne peut pas être publié par erreur.

### 2.5 Configurer l'application web

Onglet **Web** :

1. Si l'application existe déjà, la laisser en place. Sinon : *Add a new web app* → *Manual configuration* → choisir la même version Python que l'environnement virtuel (3.14 ou 3.12).
2. **Virtualenv** : `/home/NOM_UTILISATEUR/.virtualenvs/rehoboth`.
3. **Code** : *Source code* → `/home/NOM_UTILISATEUR/rehoboth`.
4. **WSGI configuration file** : ouvrir le lien, remplacer tout le contenu par celui de `pythonanywhere/wsgi_pythonanywhere.py`, puis remplacer `NOM_UTILISATEUR` par ton nom.
5. **Static files** : URL `/static/` → répertoire `/home/NOM_UTILISATEUR/rehoboth/static`.

Enregistrer, puis cliquer sur **Reload**.

### 2.6 Vérifier

Ouvrir `https://NOM_UTILISATEUR.pythonanywhere.com` puis `/admin`. Les anciennes inscriptions doivent être présentes. Une fois la vérification faite, `~/rehoboth-zip-ancien` peut être supprimé.

---

## Partie 3 : travailler au quotidien depuis VS Code

### Modifier et publier

1. Modifier les fichiers dans VS Code.
2. Tester en local :
   ```bash
   python tests/test_site.py
   ```
3. Envoyer sur GitHub, depuis le panneau *Source Control* ou le terminal :
   ```bash
   git add .
   git commit -m "Description courte de la modification"
   git push
   ```

### Mettre en ligne

Dans la console Bash de PythonAnywhere :

```bash
bash ~/rehoboth/scripts/mise_a_jour_pythonanywhere.sh
```

Le script :

1. sauvegarde la base dans `~/sauvegardes/` ;
2. récupère la dernière version depuis GitHub ;
3. installe les dépendances si elles ont changé ;
4. lance les tests ;
5. recharge le site.

Si les tests échouent, le script revient à la version précédente et ne recharge rien : le site reste en ligne tel qu'il était.

---

## Points de vigilance

- **Ne jamais modifier les fichiers directement sur PythonAnywhere.** Toute modification doit passer par GitHub, sinon le script de mise à jour l'écrasera (`git reset --hard`).
- **Les données ne sont jamais écrasées** : `data/` et `rehoboth.env` sont ignorés par Git.
- **Le fichier WSGI ne contient plus de secrets** : il lit `~/rehoboth.env`. Si tu modifies un mot de passe, change-le dans ce fichier, puis relance le script ou clique sur **Reload**.
- **Branche** : le script travaille sur la branche `main`. Garde-la comme branche de production.
- **Jeton API** : il permet de recharger le site. Ne le partage pas, et régénère-le si tu soupçonnes une fuite.

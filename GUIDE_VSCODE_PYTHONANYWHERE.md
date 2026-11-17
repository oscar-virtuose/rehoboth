# Guide complet : VS Code, Python et PythonAnywhere

Ce guide t'accompagne de l'installation des outils jusqu'à la mise en ligne d'une modification. Il suit l'ordre exact des opérations. Tu n'as besoin d'aucune connaissance avancée : chaque commande est donnée, et une section dédiée traite les erreurs les plus fréquentes.

Dans tout le guide, remplace :
- `TON_COMPTE` par ton nom d'utilisateur GitHub ;
- `syziph` par ton nom d'utilisateur PythonAnywhere.

---

## Partie 0 : ce dont tu as besoin

**Comptes (gratuits)**
- Un compte **GitHub** : github.com
- Un compte **PythonAnywhere** : pythonanywhere.com (le site y est déjà hébergé)

**Logiciels à installer sur ton ordinateur**
- **VS Code** : code.visualstudio.com
- **Python 3.14** (ou 3.12) : python.org/downloads
- **Git** : git-scm.com

**Vue d'ensemble du travail**

```
Ton ordinateur (VS Code)  ──push──▶  GitHub  ──clone/pull──▶  PythonAnywhere (le site en ligne)
```

Tu modifies et testes sur ton ordinateur, tu envoies les modifications sur GitHub, puis PythonAnywhere récupère la version à jour. Les données (inscriptions) ne passent jamais par GitHub.

---

## Partie 1 : installer les outils

### 1.1 Python

1. Télécharger Python 3.14 sur python.org/downloads (3.12 convient aussi).
2. **Windows** : pendant l'installation, cocher **« Add python.exe to PATH »** avant de cliquer sur *Install Now*. C'est l'erreur la plus fréquente si tu oublies cette case.
3. Vérifier dans un terminal :

```bash
python --version
```

Le résultat doit afficher `Python 3.14.x` (ou `3.12.x`). Sur macOS ou Linux, la commande peut être `python3` : utilise-la partout à la place de `python`.

### 1.2 Git

1. Installer Git depuis git-scm.com (les options par défaut conviennent).
2. Vérifier :

```bash
git --version
```

3. Configurer ton identité, une seule fois. Remplace les valeurs par les tiennes :

```bash
git config --global user.name "Oscar"
git config --global user.email "ton-email@exemple.com"
```

### 1.3 VS Code

1. Installer VS Code depuis code.visualstudio.com.
2. Ouvrir VS Code, puis aller dans l'onglet **Extensions** (icône à quatre carrés, à gauche).
3. Installer :
   - **Python** (éditeur Microsoft), indispensable ;
   - **GitHub Pull Requests** (facultatif, mais utile pour se connecter à GitHub depuis VS Code).

---

## Partie 2 : ouvrir le projet dans VS Code et choisir Python

### 2.1 Ouvrir le dossier

1. Décompresser `rehoboth-site-dynamique.zip`.
2. Dans VS Code : **Fichier → Ouvrir le dossier**, puis sélectionner le dossier `rehoboth`.

### 2.2 Créer un environnement Python local

Un environnement isolé évite les conflits entre projets. Dans le terminal intégré de VS Code (**Terminal → Nouveau terminal**) :

**Windows :**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux :**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Quand l'environnement est actif, son nom `(.venv)` apparaît au début de la ligne du terminal.

### 2.3 Installer les dépendances

Toujours dans le terminal, avec `(.venv)` actif :

```bash
pip install -r requirements.txt
```

### 2.4 Indiquer à VS Code d'utiliser cet environnement

1. Appuyer sur **Ctrl+Maj+P** (ou **Cmd+Maj+P** sur macOS).
2. Taper `Python: Select Interpreter`.
3. Choisir l'entrée qui contient `.venv`.

Dans le coin inférieur droit, le nom de la version Python doit maintenant indiquer `.venv`.

### 2.5 Vérifier que tout fonctionne

```bash
python tests/test_site.py
```

Le message final doit être : `=== TOUS LES TESTS SONT PASSÉS ===`.

Pour lancer le site en local :

```bash
python app.py
```

Puis ouvrir http://localhost:5000 dans le navigateur. Pour arrêter le serveur, appuyer sur **Ctrl+C**.

---

## Partie 3 : créer le dépôt GitHub

Le dépôt GitHub contient le code du site. Il ne contient jamais les données ni les mots de passe, grâce au fichier `.gitignore`.

### 3.1 Créer le dépôt sur GitHub

1. Connecte-toi sur github.com, puis clique sur **New** (ou le bouton **+** en haut à droite → *New repository*).
2. Nom : `rehoboth`.
3. Choisir **Private** (privé).
4. **Ne coche pas** « Add a README » ni « .gitignore » : le projet en contient déjà.
5. Cliquer sur **Create repository**.

### 3.2 Se connecter à GitHub depuis VS Code

GitHub n'accepte plus les mots de passe dans Git : il faut une connexion par navigateur ou un jeton.

Méthode la plus simple : installe l'extension **GitHub Pull Requests**, puis clique sur l'icône de compte en bas à gauche de VS Code et choisis **Sign in with GitHub**. Suis les indications dans le navigateur.

Si cela ne fonctionne pas, crée un **jeton d'accès personnel** : sur GitHub, *Settings → Developer settings → Personal access tokens*, avec la permission `repo`. Utilise ce jeton à la place du mot de passe lorsque Git le demande. Ne le note jamais dans un fichier du projet.

### 3.3 Envoyer le projet

Dans le terminal de VS Code, à la racine du projet :

```bash
git init
git add .
git commit -m "Version initiale du site"
git branch -M main
git remote add origin https://github.com/TON_COMPTE/rehoboth.git
git push -u origin main
```

**Avant le `push`**, vérifie avec `git status` (ou `git ls-files`) que les fichiers suivants **n'apparaissent pas** :
- `data/` et tout fichier `.db` ;
- `rehoboth.env` ;
- le dossier `.venv/`.

Si l'un d'eux apparaît, c'est que le `.gitignore` n'est pas au bon endroit : ne fais pas le `push`, et demande de l'aide avant de continuer.

---

## Partie 4 : connecter PythonAnywhere à GitHub

PythonAnywhere récupère le code depuis GitHub. Pour un dépôt privé, il faut une clé de déploiement : c'est une clé SSH qui donne un accès en lecture seule à ce seul dépôt.

### 4.1 Créer la clé sur PythonAnywhere

Ouvrir une **console Bash** (onglet *Consoles* → *Bash*), puis :

```bash
ssh-keygen -t ed25519 -C "pythonanywhere-rehoboth" -f ~/.ssh/cle_rehoboth -N ""
cat ~/.ssh/cle_rehoboth.pub
```

Copie toute la ligne affichée (elle commence par `ssh-ed25519`).

### 4.2 Ajouter la clé à GitHub

1. Sur GitHub, ouvrir le dépôt `rehoboth` → **Settings** → **Deploy keys** → **Add deploy key**.
2. Titre : `PythonAnywhere`. Colle la ligne copiée.
3. **Ne coche pas** « Allow write access ». La lecture suffit.
4. Cliquer sur **Add key**.

### 4.3 Configurer la clé et récupérer le code

Toujours dans la console Bash de PythonAnywhere :

```bash
cat >> ~/.ssh/config <<'EOF'
Host github.com
  IdentityFile ~/.ssh/cle_rehoboth
  StrictHostKeyChecking accept-new
EOF
chmod 600 ~/.ssh/config
```

Puis, en mettant de côté l'ancienne version du site (pour garder la base d'inscriptions) :

```bash
cd ~
mv rehoboth rehoboth-zip-ancien
git clone git@github.com:TON_COMPTE/rehoboth.git rehoboth
cp -r ~/rehoboth-zip-ancien/data ~/rehoboth/data
```

Vérifie que `~/rehoboth/data/inscriptions.db` existe : c'est ta base actuelle.

---

## Partie 5 : configurer le site sur PythonAnywhere

Cette partie ne se fait qu'une fois. Elle reprend le détail de `pythonanywhere/INSTALLATION.md`.

### 5.1 Environnement Python

```bash
mkvirtualenv --python=/usr/bin/python3.14 rehoboth   # ou python3.12 si 3.14 n'est pas proposé
pip install -r ~/rehoboth/requirements.txt
```

### 5.2 Fichier de secrets

```bash
cp ~/rehoboth/pythonanywhere/rehoboth.env.modele ~/rehoboth.env
nano ~/rehoboth.env
chmod 600 ~/rehoboth.env
```

Dans `nano`, remplace les valeurs (`ADMIN_PASSWORD`, `SECRET_KEY`, `PA_TOKEN`, etc.). Pour enregistrer : **Ctrl+O**, puis **Entrée**, puis **Ctrl+X**.

Pour la clé secrète :

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Pour le jeton API : onglet **Account** → **API token** → *Create a new API token*.

### 5.3 Application web

Onglet **Web** :

1. Virtualenv : `/home/syziph/.virtualenvs/rehoboth`
2. Code : `/home/syziph/rehoboth`
3. WSGI configuration file : remplacer tout le contenu par celui de `~/rehoboth/pythonanywhere/wsgi_pythonanywhere.py`, en remplaçant `NOM_UTILISATEUR` par `syziph`.
4. Static files : URL `/static/` → `/home/syziph/rehoboth/static`
5. Cliquer sur **Reload**.

### 5.4 Vérifier

Ouvrir https://syziph.pythonanywhere.com et `/admin`. Les anciennes inscriptions doivent être présentes. Une fois cela confirmé, tu peux supprimer `~/rehoboth-zip-ancien`.

---

## Partie 6 : la mise à jour, étape par étape

C'est la procédure à suivre à chaque modification. Elle ne prend que quelques minutes.

### Étape 1 : modifier sur ton ordinateur

Fais tes changements dans VS Code. Ne modifie jamais les fichiers directement sur PythonAnywhere : ces changements seraient écrasés à la mise à jour suivante.

### Étape 2 : tester en local

```bash
python tests/test_site.py
```

Si un test échoue, ne continue pas : corrige d'abord. Le message indique la règle concernée.

### Étape 3 : envoyer sur GitHub

**Depuis l'interface VS Code** (recommandé pour débuter) :
1. Ouvrir l'onglet **Contrôle de code source** (icône à trois points reliés, à gauche).
2. Passer la souris sur chaque fichier modifié et cliquer sur **+** pour l'ajouter (*Stage*).
3. Écrire un message court dans la zone en haut, par exemple `Corrige le titre de la page d'accueil`.
4. Cliquer sur **Commit**.
5. Cliquer sur **Sync Changes** (ou **Push**).

**Ou depuis le terminal** :

```bash
git add .
git commit -m "Corrige le titre de la page d'accueil"
git push
```

Un bon message de commit décrit ce qui a changé. Il servira si tu dois revenir en arrière.

### Étape 4 : mettre en ligne sur PythonAnywhere

Ouvrir une **console Bash** sur PythonAnywhere, puis :

```bash
bash ~/rehoboth/scripts/mise_a_jour_pythonanywhere.sh
```

Le script effectue dans l'ordre :

1. **Sauvegarde** de la base dans `~/sauvegardes/`.
2. **Récupération** de la dernière version depuis GitHub.
3. **Installation** des dépendances, si elles ont changé.
4. **Tests** sur le serveur.
5. **Rechargement** du site.

Si les tests échouent, le script revient automatiquement à la version précédente : le site reste en ligne tel qu'il était.

### Étape 5 : vérifier

Ouvrir le site et contrôler :
- [ ] la page d'accueil s'affiche ;
- [ ] la modification est visible ;
- [ ] `/admin` ouvre avec le mot de passe, et les inscriptions sont toujours là ;
- [ ] onglet **Web** → **Error log** : aucune erreur récente.

### Revenir en arrière

Si la mise à jour pose problème, reprends la version précédente depuis VS Code :

```bash
git log --oneline
git revert HEAD
git push
```

Puis relance `bash ~/rehoboth/scripts/mise_a_jour_pythonanywhere.sh`.

`git revert` crée une nouvelle version qui annule la précédente. Ne jamais utiliser `git reset --hard` ou `git push --force` sur la branche `main` : cela peut effacer l'historique.

---

## Partie 7 : erreurs fréquentes

| Message ou symptôme | Cause | Solution |
|---|---|---|
| `python n'est pas reconnu` | Python n'est pas dans le PATH | Réinstaller Python en cochant *Add to PATH*, ou utiliser `py` |
| `(.venv)` absent du terminal | L'environnement n'est pas activé | Relancer `.venv\Scripts\activate` (Windows) ou `source .venv/bin/activate` |
| VS Code ne trouve pas les modules | Mauvais interpréteur | Ctrl+Maj+P → `Python: Select Interpreter` → choisir `.venv` |
| `git push` refusé (*rejected*) | Une version plus récente existe sur GitHub | Lancer `git pull`, puis `git push` |
| `Permission denied (publickey)` sur PythonAnywhere | La clé de déploiement n'est pas ajoutée à GitHub | Refaire la partie 4.2 et vérifier que la clé est bien la même |
| `git pull` refuse à cause de fichiers modifiés | Une modification a été faite directement sur le serveur | Ne rien écraser : copier le fichier, puis demander de l'aide. Ne plus modifier sur le serveur |
| Les tests échouent après une modification | Une règle du site n'est plus respectée | Lire la ligne d'erreur ; la correction se fait en local |
| Erreur 500 sur le site | Erreur dans le code ou la configuration | Onglet **Web** → **Error log**, lire la dernière ligne |
| Le script affiche `Fichier de configuration absent` | `~/rehoboth.env` n'existe pas | Refaire la partie 5.2 |
| `401` lors de l'appel de rechargement | Le jeton API est faux ou expiré | Créer un nouveau jeton, et le mettre à jour dans `~/rehoboth.env` |

---

## Checklist de la mise à jour

**Sur ton ordinateur**
- [ ] Modification faite et vérifiée
- [ ] `python tests/test_site.py` réussi
- [ ] Commit avec un message clair
- [ ] `push` effectué sur GitHub

**Sur PythonAnywhere**
- [ ] `bash ~/rehoboth/scripts/mise_a_jour_pythonanywhere.sh` terminé sans erreur
- [ ] Site vérifié dans le navigateur
- [ ] `/admin` : inscriptions présentes
- [ ] Error log propre

---

## Ce qu'il faut retenir

1. Tu modifies **toujours** sur ton ordinateur, jamais sur le serveur.
2. Les tests passent **avant** chaque envoi.
3. Les données (`data/`) et les secrets (`rehoboth.env`) ne sont **jamais** dans GitHub.
4. En cas de doute, la sauvegarde automatique et `git revert` permettent de revenir en arrière.

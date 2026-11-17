# Guide de mise à jour du site Rehoboth

Ce guide décrit comment publier une modification sans casser le site ni perdre les inscriptions.
Il suppose un hébergement sur PythonAnywhere (voir la mise en ligne décrite précédemment).

Règle d'or : **une modification n'est publiée qu'après avoir passé les tests, et une sauvegarde existe toujours avant de publier.**

---

## 1. Ce qui peut casser le site, par niveau de risque

| Type de modification | Exemples | Risque | Précautions |
|---|---|---|---|
| **Contenu** | Texte, prix, horaires, formation ajoutée dans `content/site.json` | Faible | Vérifier que le JSON est valide (test automatique) |
| **Présentation** | Gabarits `templates/*.html`, feuilles de style `static/*.css` | Moyen | Tester les pages modifiées dans un navigateur |
| **Code** | `app.py`, scripts | Élevé | Tests automatiques obligatoires, relecture |
| **Base de données** | Nouvelle colonne, changement de table | Critique | Migration écrite à l'avance, sauvegarde vérifiée |
| **Tuteur de frappe** | `static/tuteur-frappe.html` | Moyen | Ne jamais changer les noms des clés enregistrées dans le navigateur (voir section 6) |

Plus le changement est risqué, plus il faut tester avant de publier.

---

## 2. Avant de commencer : sauvegarder

Sauvegarder est la première étape, même pour une petite modification.

1. **Exporter les inscriptions** : dans `/admin`, cliquer sur **Exporter en CSV** et garder le fichier hors du serveur.
2. **Télécharger la base** : onglet **Files** de PythonAnywhere, dossier `rehoboth/data/`, télécharger `inscriptions.db`.
3. **Noter la version en cours** : garder le zip publié précédemment, sous un nom daté (ex. `rehoboth-2026-11-15.zip`).

Le script de déploiement crée aussi une copie datée de la base dans `sauvegardes/`, mais une copie hors du serveur reste indispensable.

---

## 3. Procédure pas à pas

### Étape A : modifier en local

1. Décompresser le zip de la version actuelle dans un dossier de travail.
2. Faire les modifications.
3. Vérifier le JSON si tu as touché au contenu :
   ```bash
   python -m json.tool content/site.json > /dev/null && echo "JSON valide"
   ```

### Étape B : tester en local

Depuis le dossier du projet :

```bash
pip install -r requirements.txt
python tests/test_site.py
```

Le test doit se terminer par `=== TOUS LES TESTS SONT PASSÉS ===`. Il crée une base temporaire et ne touche jamais aux inscriptions réelles.

Si un test échoue, **ne publie pas**. Le message indique la page ou la règle concernée.

Ensuite, lancer le site localement et parcourir les pages modifiées :

```bash
ADMIN_PASSWORD="test" python app.py
```

Puis ouvrir http://localhost:5000 et vérifier :

- la page d'accueil et le menu ;
- la page des formations, si elle a changé ;
- le formulaire de contact, en envoyant une demande de test ;
- la page `/admin`, avec le mot de passe de test.

### Étape C : préparer le paquet

Créer un nouveau zip du dossier modifié, en excluant `data/` et `__pycache__/` :

```bash
zip -r rehoboth-nouveau.zip rehoboth -x "rehoboth/data/*" "*/__pycache__/*"
```

Le dossier `data/` ne doit jamais partir dans le paquet : la base réelle est déjà sur le serveur.

### Étape D : déployer sur PythonAnywhere

Le déploiement se fait sans arrêt de service, en deux dossiers :

1. Onglet **Files** : téléverser `rehoboth-nouveau.zip` dans `/home/ton-nom/`.
2. Console **Bash** :
   ```bash
   cd /home/ton-nom
   unzip rehoboth-nouveau.zip -d rehoboth-nouveau
   workon rehoboth
   pip install -r rehoboth-nouveau/rehoboth/requirements.txt
   cd rehoboth-nouveau/rehoboth
   bash scripts/deployer_pythonanywhere.sh /home/ton-nom/rehoboth-nouveau/rehoboth
   ```
   Adapter les chemins à ton nom d'utilisateur. Le script :
   - sauvegarde la base actuelle dans `sauvegardes/` ;
   - lance les tests sur la nouvelle version ;
   - copie la base réelle dans la nouvelle version ;
   - échange les deux dossiers.

   Si les tests échouent, le script s'arrête sans rien modifier sur le site.

3. Onglet **Web** : cliquer sur **Reload**.

**Important** : le fichier WSGI (qui contient les mots de passe) se trouve hors du projet. Le script ne le modifie pas, donc il n'a pas besoin d'être refait à chaque mise à jour.

### Étape E : vérifier en production

Une fois le Reload terminé, contrôler :

- [ ] `https://ton-nom.pythonanywhere.com` s'affiche ;
- [ ] les pages modifiées sont correctes ;
- [ ] `/admin` s'ouvre avec le mot de passe, et les anciennes inscriptions sont toujours là ;
- [ ] onglet **Web** → **Error log** : aucune erreur récente ;
- [ ] le tuteur de frappe s'ouvre et un exercice démarre.

Pour tester le formulaire en production, envoie une demande avec un nom explicite comme « TEST - à supprimer ». Dans `/admin`, passe-la au statut **clos** pour qu'elle ne reste pas dans la liste active.

---

## 4. En cas de problème : retour arrière

Si le site ne fonctionne plus après la mise à jour, revenir à la version précédente prend moins d'une minute :

```bash
cd /home/ton-nom
bash rehoboth/scripts/retour_arriere_pythonanywhere.sh
```

Le script se lance depuis la version active : après le déploiement, le dossier `rehoboth-nouveau` n'existe plus.

Puis cliquer sur **Reload** dans l'onglet **Web**.

Le retour arrière conserve les inscriptions reçues depuis la mise à jour. La version défaillante est gardée dans `rehoboth-defaillant/` pour analyse.

Ce script ne remplace pas une sauvegarde : si la base est corrompue, restaure `sauvegardes/data-AAAAMMJJ-HHMMSS/`.

---

## 5. Changements particuliers

### Ajouter une formation
Ajouter un bloc dans la liste `formations` de `content/site.json`, avec un `slug` unique. Elle apparaît automatiquement sur la page Formations, dans le formulaire et dans `/api/formations`. Aucun changement de code n'est nécessaire.

### Ajouter un champ au formulaire d'inscription
C'est une modification de base de données. Ne jamais supprimer ou renommer une colonne existante. Ajouter la colonne sans supprimer les anciennes données, par exemple dans `initialiser_base()` de `app.py` :

```python
colonnes = [c["name"] for c in connexion().execute("PRAGMA table_info(inscriptions)")]
if "source" not in colonnes:
    connexion().execute("ALTER TABLE inscriptions ADD COLUMN source TEXT DEFAULT ''")
    connexion().commit()
```

Ce code ne s'exécute qu'une fois : il vérifie si la colonne existe déjà. Ajouter un test dans `tests/test_site.py` pour la nouvelle colonne.

### Changer le mot de passe administrateur
Modifier `ADMIN_PASSWORD` dans le fichier WSGI (onglet **Web**, lien du fichier WSGI), puis cliquer sur **Reload**. Ne pas oublier de le noter dans un gestionnaire de mots de passe.

### Changer la clé secrète (`SECRET_KEY`)
Cela invalide les sessions en cours : l'administrateur doit se reconnecter. Les données ne sont pas touchées. Modifier la valeur dans le fichier WSGI, puis Reload.

### Changer les coordonnées ou le numéro WhatsApp
Modifier uniquement `contact` dans `content/site.json`. Le numéro WhatsApp est utilisé pour tous les liens et le message d'inscription : vérifier qu'il contient uniquement les chiffres, indicatif pays compris (ex. `2250103730014`).

---

## 6. Ne jamais casser le tuteur de frappe pour les apprenants

La progression des apprenants est enregistrée dans le navigateur de chaque ordinateur, sous des noms de clés précis. Si ces noms changent, les apprenants perdent leur progression sans prévenir.

Avant de modifier `static/tuteur-frappe.html` :

- ne pas renommer les clés utilisées avec `ls.get` et `ls.set` (par exemple `rhb_reglages_v1`) ;
- ne pas changer la structure des entrées d'historique (`P.__h`, `P.__k`, `P.__att`) sans écrire une conversion pour les anciennes données ;
- tester avec un profil existant créé avant la modification, puis vérifier qu'il retrouve ses résultats.

---

## 7. Diagnostic des erreurs courantes

| Symptôme | Cause probable | Action |
|---|---|---|
| Page d’erreur (erreur 500) | Erreur dans le code ou la configuration | Onglet **Web** → **Error log** : la dernière ligne indique le fichier et la ligne |
| `ModuleNotFoundError` | Une bibliothèque manque dans l'environnement | Relancer `pip install -r requirements.txt` dans l'environnement virtuel |
| Site vide ou page sans style | Fichiers statiques mal configurés | Vérifier la section **Static files** : `/static/` pointe vers `.../rehoboth/static` |
| Formulaire qui ne s'enregistre pas | Base inaccessible ou chemin erroné | Vérifier la variable `DATABASE` dans le fichier WSGI |
| Erreur après un changement de `content/site.json` | JSON invalide (virgule en trop, guillemet oublié) | `python -m json.tool content/site.json` pour localiser l'erreur |
| `/admin` affiche une erreur 404 | Variable `ADMIN_PASSWORD` absente ou vide | Vérifier le fichier WSGI |

---

## 8. Bonnes pratiques

- **Une seule modification à la fois** : cela permet de savoir ce qui a provoqué un problème.
- **Éviter les mises à jour le vendredi soir** : si quelque chose casse, il faut pouvoir le corriger.
- **Garder l'historique** : nommer chaque zip avec sa date et une courte description.
- **Figer les versions des bibliothèques** : une fois le site stable, créer un fichier de versions exactes avec `pip freeze > requirements-lock.txt`. Il garantit que l'environnement de production reste identique à celui testé.
- **Tester le retour arrière au moins une fois** : il est plus simple de l'utiliser en sachant qu'il fonctionne.

---

## Checklist de publication

**Avant**
- [ ] Inscriptions exportées en CSV et base téléchargée
- [ ] Modification faite et relue
- [ ] `python tests/test_site.py` réussi
- [ ] Pages modifiées vérifiées en local

**Pendant**
- [ ] Zip créé sans `data/`
- [ ] Script `deployer_pythonanywhere.sh` terminé sans erreur
- [ ] Reload effectué dans l'onglet Web

**Après**
- [ ] Site accessible en production
- [ ] `/admin` : anciennes inscriptions présentes
- [ ] Error log vide ou sans erreur récente
- [ ] Tuteur de frappe fonctionnel
- [ ] Zip de la nouvelle version archivé

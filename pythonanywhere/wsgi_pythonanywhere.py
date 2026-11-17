"""Fichier WSGI de PythonAnywhere.

À copier tel quel dans le fichier WSGI de l'onglet Web (en remplaçant NOM_UTILISATEUR).
Les secrets ne sont jamais dans le dépôt : ils sont lus depuis ~/rehoboth.env, sur le serveur uniquement.
"""
import os
import sys
from pathlib import Path

NOM_UTILISATEUR = "NOM_UTILISATEUR"          # <- à remplacer, ex. "syziph"
PROJET = Path(f"/home/{NOM_UTILISATEUR}/rehoboth")
FICHIER_ENV = Path(f"/home/{NOM_UTILISATEUR}/rehoboth.env")

if str(PROJET) not in sys.path:
    sys.path.insert(0, str(PROJET))

# Chargement des variables d'environnement (format KEY=valeur, une par ligne)
if FICHIER_ENV.exists():
    for ligne in FICHIER_ENV.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"'))

from app import app as application  # noqa: E402

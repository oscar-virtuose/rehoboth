#!/bin/bash
# Mise à jour du site sur PythonAnywhere depuis GitHub.
#
# Usage, dans la console Bash du serveur :
#     bash ~/rehoboth/scripts/mise_a_jour_pythonanywhere.sh
#
# Déroulement : sauvegarde de la base, récupération de la dernière version,
# installation des dépendances, tests, puis rechargement du site.
# Si les tests échouent, la version précédente est restaurée et rien n'est rechargé.
set -euo pipefail

NOM="$(whoami)"
PROJET="/home/${NOM}/rehoboth"
ENV_FILE="/home/${NOM}/rehoboth.env"
VENV="/home/${NOM}/.virtualenvs/rehoboth"
SAUVEGARDES="/home/${NOM}/sauvegardes"
HORODATAGE="$(date +%Y%m%d-%H%M%S)"

[ -f "$ENV_FILE" ] || { echo "Fichier de configuration absent : $ENV_FILE"; exit 1; }
set -a; source "$ENV_FILE"; set +a
: "${PA_TOKEN:?PA_TOKEN manquant dans $ENV_FILE}"
: "${PA_DOMAINE:?PA_DOMAINE manquant dans $ENV_FILE}"

cd "$PROJET"

echo "1/5 Sauvegarde de la base"
mkdir -p "$SAUVEGARDES"
cp -r data "$SAUVEGARDES/data-$HORODATAGE"

echo "2/5 Récupération de la dernière version depuis GitHub"
ANCIENNE_VERSION="$(git rev-parse HEAD)"
git fetch origin
git pull --ff-only origin main

echo "3/5 Installation des dépendances"
"$VENV/bin/pip" install -q -r requirements.txt

echo "4/5 Tests"
if ! "$VENV/bin/python" tests/test_site.py > /tmp/tests-pa.log 2>&1; then
  echo "ÉCHEC des tests : retour à la version précédente."
  git reset --hard "$ANCIENNE_VERSION"
  tail -20 /tmp/tests-pa.log
  exit 1
fi

echo "5/5 Rechargement du site"
curl -fsS -X POST \
  -H "Authorization: Token ${PA_TOKEN}" \
  "https://www.pythonanywhere.com/api/v0/user/${PA_USER:-$NOM}/webapps/${PA_DOMAINE}/reload/" \
  && echo "Site rechargé : https://${PA_DOMAINE}"

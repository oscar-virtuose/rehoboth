#!/bin/bash
# Déploiement sans perte de données sur PythonAnywhere.
# À lancer dans la console Bash, depuis le dossier où se trouve la nouvelle version.
#
#   bash scripts/deployer_pythonanywhere.sh /home/ton-nom/rehoboth-nouveau
#
# Le script : sauvegarde la base, lance les tests, copie la base dans la nouvelle
# version, puis échange les dossiers. L'ancienne version reste disponible pour un retour arrière.
set -euo pipefail

NOM_UTILISATEUR="${NOM_UTILISATEUR:-ton-nom}"
NOUVEAU="${1:?Indiquez le dossier de la nouvelle version}"
ACTUEL="/home/${NOM_UTILISATEUR}/rehoboth"
PRECEDENT="/home/${NOM_UTILISATEUR}/rehoboth-precedent"
SAUVEGARDES="/home/${NOM_UTILISATEUR}/sauvegardes"
HORODATAGE="$(date +%Y%m%d-%H%M%S)"

echo "1/5 Sauvegarde de la base actuelle"
mkdir -p "$SAUVEGARDES"
cp -r "$ACTUEL/data" "$SAUVEGARDES/data-$HORODATAGE"

echo "2/5 Tests de la nouvelle version (base temporaire, aucune donnée réelle touchée)"
cd "$NOUVEAU"
python tests/test_site.py > /tmp/tests-deploiement.log 2>&1 || {
  echo "ÉCHEC des tests. Déploiement annulé. Détail : /tmp/tests-deploiement.log"
  tail -20 /tmp/tests-deploiement.log
  exit 1
}

echo "3/5 Reprise de la base réelle dans la nouvelle version"
rm -rf "$NOUVEAU/data"
cp -r "$ACTUEL/data" "$NOUVEAU/data"

echo "4/5 Échange des dossiers (l'ancienne version est gardée dans $PRECEDENT)"
rm -rf "$PRECEDENT"
mv "$ACTUEL" "$PRECEDENT"
mv "$NOUVEAU" "$ACTUEL"

echo "5/5 Terminé. Ouvrez l'onglet Web et cliquez sur Reload, puis vérifiez le site."
echo "Retour arrière si besoin : bash scripts/retour_arriere_pythonanywhere.sh"

#!/bin/bash
# Retour à la version précédente, en conservant les inscriptions reçues depuis la mise à jour.
set -euo pipefail

NOM_UTILISATEUR="${NOM_UTILISATEUR:-ton-nom}"
ACTUEL="/home/${NOM_UTILISATEUR}/rehoboth"
PRECEDENT="/home/${NOM_UTILISATEUR}/rehoboth-precedent"
MORTE="/home/${NOM_UTILISATEUR}/rehoboth-defaillant"

[ -d "$PRECEDENT" ] || { echo "Aucune version précédente trouvée."; exit 1; }

echo "1/3 Copie des inscriptions récentes vers l'ancienne version"
rm -rf "$PRECEDENT/data"
cp -r "$ACTUEL/data" "$PRECEDENT/data"

echo "2/3 Échange : la version défaillante est mise de côté"
rm -rf "$MORTE"
mv "$ACTUEL" "$MORTE"
mv "$PRECEDENT" "$ACTUEL"

echo "3/3 Terminé. Ouvrez l'onglet Web et cliquez sur Reload."

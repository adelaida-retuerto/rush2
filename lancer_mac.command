#!/bin/bash
# Lanceur Mac : double-clic = mise à jour du classeur du mois, puis ouverture dans Excel.
# 1. se place dans le dossier du projet ; 2. trouve Python (conda « rush2 », sinon .venv) ;
# 3. lance main.py --offline ; 4. ouvre le classeur le plus récent de deliverables/.

# Le double-clic ouvre le Terminal dans le dossier personnel : on revient dans le dossier de ce fichier
cd "$(dirname "$0")" || exit 1

attendre() {
    echo
    read -r -p "Appuyez sur Entrée pour fermer cette fenêtre..."
}

# --- 1. Python de l'environnement conda « rush2 » --------------------------------------------
# Un double-clic ne charge pas conda : on cherche le dossier de l'environnement aux emplacements habituels
PYTHON=""
BASES=""
if command -v conda >/dev/null 2>&1; then
    BASES="$(conda info --base 2>/dev/null)"
fi
BASES="$BASES $HOME/miniconda3 $HOME/anaconda3 $HOME/opt/miniconda3 $HOME/opt/anaconda3 \
/opt/miniconda3 /opt/anaconda3 /opt/homebrew/Caskroom/miniconda/base /usr/local/Caskroom/miniconda/base"
for base in $BASES; do
    if [ -x "$base/envs/rush2/bin/python" ]; then
        PYTHON="$base/envs/rush2/bin/python"
        break
    fi
done

# --- 2. Sinon, le Python du dossier .venv ------------------------------------------------------
if [ -z "$PYTHON" ] && [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
fi

if [ -z "$PYTHON" ]; then
    echo "Aucun environnement Python trouvé (ni conda « rush2 », ni dossier .venv)."
    echo "Suivre la partie « Installation » du README, puis relancer."
    attendre
    exit 1
fi
echo "Python utilisé : $PYTHON"
echo

# --- 3. Mise à jour du classeur ----------------------------------------------------------------
if ! "$PYTHON" main.py --offline; then
    echo
    echo "ERREUR : la mise à jour a échoué (message ci-dessus). Aucun classeur n'a été ouvert."
    attendre
    exit 1
fi

# --- 4. Ouverture du classeur le plus récent ---------------------------------------------------
CLASSEUR="$(ls -t deliverables/analyse_ventes_*.xlsx 2>/dev/null | head -n 1)"
if [ -n "$CLASSEUR" ]; then
    echo
    echo "Ouverture de $CLASSEUR"
    open "$CLASSEUR"
else
    echo "Aucun classeur trouvé dans deliverables/."
fi
attendre

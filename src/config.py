"""Constantes du projet : chemins, noms des groupes ATC et couleurs.

Tout le code importe ce fichier, pour qu'une modification se fasse à un seul endroit.
"""

from pathlib import Path

# --- Chemins -----------------------------------------------------------------
# On part de l'emplacement de ce fichier (src/config.py) et on remonte d'un
# niveau pour trouver la racine du repo. Ainsi le code marche quel que soit
# l'ordinateur ou le dossier où le repo a été cloné.
RACINE = Path(__file__).resolve().parent.parent

DOSSIER_DATA = RACINE / "data"
DOSSIER_OUTPUT = RACINE / "output"
DOSSIER_DECKS = RACINE / "decks"
DOSSIER_NOTE = RACINE / "note"

# Les 4 exports du client (même nom chaque mois)
FICHIER_HORAIRE = DOSSIER_DATA / "Pharma_Ventes_Hourly.csv"
FICHIER_JOURNALIER = DOSSIER_DATA / "Pharma_Ventes_Daily.csv"
FICHIER_HEBDOMADAIRE = DOSSIER_DATA / "Pharma_Ventes_Weekly.csv"
FICHIER_MENSUEL = DOSSIER_DATA / "Pharma_Ventes_Monthly.csv"

# --- Groupes de médicaments (code ATC -> nom lisible) ------------------------
ATC = {
    "M01AB": "AINS, diclofénac",
    "M01AE": "AINS, ibuprofène",
    "N02BA": "Aspirine",
    "N02BE": "Paracétamol",
    "N05B": "Anxiolytiques",
    "N05C": "Hypnotiques, somnifères",
    "R03": "Asthme, voies respiratoires",
    "R06": "Antihistaminiques",
}

# Liste des codes, dans l'ordre des colonnes des exports
CODES_ATC = list(ATC.keys())

# --- Couleurs ----------------------------------------------------------------
# Une couleur par groupe ATC (familles proches = teintes proches)
COULEURS_ATC = {
    "M01AB": "#D98E3F",
    "M01AE": "#A9652A",
    "N02BA": "#D46A5A",
    "N02BE": "#9E3F35",
    "N05B": "#8B7EC4",
    "N05C": "#5A4C94",
    "R03": "#3E86B2",
    "R06": "#86B9D8",
}

# Couleurs de base de la charte
SAPIN = "#1F3D3A"
SAUGE = "#2F6F6A"
CREME = "#F7F4EE"
BRUME = "#EEF4F2"
ENCRE = "#2B2B2B"
GRIS = "#7A8A87"
AMBRE = "#E0A526"  # réservé aux alertes

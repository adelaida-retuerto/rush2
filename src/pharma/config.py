"""Constantes du projet : chemins, noms des groupes ATC et couleurs.

Tout le code importe ce fichier, pour qu'une modification se fasse à un seul endroit.
"""

from pathlib import Path

# --- Chemins -----------------------------------------------------------------
# On part de l'emplacement de ce fichier (src/config.py) et on remonte d'un
# niveau pour trouver la racine du repo. Ainsi le code marche quel que soit
# l'ordinateur ou le dossier où le repo a été cloné.

ROOT = Path(__file__).resolve().parents[2]

# --- Dossiers --------------------------------------------------------------------------------
RAW_DIR = ROOT / "data" / "raw"                      # 4 exports du client, jamais modifiés (versionné)
EXTERNAL_DIR = ROOT / "data" / "external"            # donnée publique grippe (versionné)
PROCESSED_DIR = ROOT / "data" / "processed"          # tables propres (généré, non versionné)
QUALITY_REPORT_DIR = ROOT / "reports" / "quality"    # rapports de contrôle (généré, non versionné)
OUTPUT_DIR = ROOT / "deliverables"                      # classeurs livrés au client (versionné)

# --- Classeur client : modèle fixe + un fichier daté par mois ------------------------------
TEMPLATE_PATH = ROOT / "templates" / "workbook_template.xlsx"
OUTPUT_NAME = "analyse_ventes_{mois}.xlsx"           # {mois} = dernier mois complet, ex. 2019-09
ARCHIVE_SUBDIR = "archive"                           # deliverables/archive/ : classeurs des mois précédents

# --- Exports du logiciel de caisse (le client renvoie les mêmes chaque mois) ---------------
EXPORTS = {
    "hourly": "Pharma_Ventes_Hourly.csv",
    "daily": "Pharma_Ventes_Daily.csv",
    "weekly": "Pharma_Ventes_Weekly.csv",
    "monthly": "Pharma_Ventes_Monthly.csv",
}

# --- Les 8 groupes ATC, avec un libellé lisible pour le client --------------------------------
GROUPS = {
    "M01AB": "Anti-inflammatoires (dérivés acide acétique, ex. diclofénac)",
    "M01AE": "Anti-inflammatoires (dérivés acide propionique, ex. ibuprofène)",
    "N02BA": "Antalgiques (acide salicylique, ex. aspirine)",
    "N02BE": "Antalgiques (anilides, ex. paracétamol)",
    "N05B": "Anxiolytiques",
    "N05C": "Hypnotiques et sédatifs",
    "R03": "Médicaments de l'asthme et de la BPCO",
    "R06": "Antihistaminiques (allergies)",
}
GROUP_CODES = list(GROUPS)
SENSITIVE_GROUPS = ["N05B", "N05C"]  # anxiété / sommeil : données de santé sensibles
UNIT_LABEL = "quantités (unité du logiciel de caisse, non documentée)"


# Liste des codes, dans l'ordre des colonnes des exports
CODES_ATC = list(GROUPS.keys())

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

# --- Contrôles qualité ---------------------------------------------------------------------
RECONCILIATION_TOLERANCE = 1e-6  # écart toléré entre deux exports (arrondis flottants)
OUTLIER_WINDOW_DAYS = 29         # fenêtre glissante (jours) pour la médiane robuste
OUTLIER_Z = 6.0                  # seuil de z-score robuste pour signaler un pic
OUTLIER_MIN_QTY = 10             # on ne signale pas un « pic » sous ce volume journalier

# --- Prévision -----------------------------------------------------------------------------
BACKTEST_MONTHS = 24             # nb de mois testés en origine glissante
MIN_TRAIN_MONTHS = 36            # historique minimal pour entraîner un modèle
SKILL_THRESHOLD = 0.10           # gain minimal (10 %) sur la meilleure référence naïve

# --- Donnée externe : Réseau Sentinelles, syndromes grippaux, France ------------------------
SENTIWEB_URL = "https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv"
SENTIWEB_CACHE = EXTERNAL_DIR / "sentiweb_syndromes_grippaux_france.csv"
EPIDEMIC_PERCENTILE = 0.85       # semaines au-dessus de ce quantile = « forte circulation »

# --- Confidentialité -----------------------------------------------------------------------
SMALL_COUNT_THRESHOLD = 3        # un comptage sous ce seuil est à risque de ré-identification

# --- Mise en page du classeur (tailles fixes des zones du modèle) ----------------------------
HOURS = list(range(24))          # profils horaires sur 24 h : taille fixe quelles que soient les données
CHART_WINDOW_MONTHS = 60         # graphique mensuel : 60 derniers mois
CHART_WINDOW_WEEKS = 156         # graphique grippe : 3 dernières années
TOOL_DETAIL_ROWS = 92            # outil : lignes du détail dans le temps


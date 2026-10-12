"""Paramètres centraux du projet : chemins, groupes ATC, seuils.

Tout ce qui peut changer d'une mission à l'autre est ici, et nulle part ailleurs.
Fichier commun aux trois blocs : toute modification passe par une pull request relue par l'équipe.
"""
from pathlib import Path

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

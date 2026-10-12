"""Styles du classeur : couleurs, polices, bordures et formats de nombres.   [Ihman]

Traduit la charte graphique (Charte_graphique_Rush2.pdf) pour openpyxl.
Tout le code du classeur importe ce fichier :  from . import styles as S
Si on change une couleur ici, elle change partout.
"""
from __future__ import annotations

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

# --- Couleurs de base de la charte --------------------------------------------------------
# openpyxl écrit les couleurs sans le « # » : "1F3D3A" et non "#1F3D3A"
SAPIN = "1F3D3A"   # titres, en-têtes de tableau
SAUGE = "2F6F6A"   # sous-titres, petits accents
CREME = "F7F4EE"   # fonds
BRUME = "EEF4F2"   # encadrés, zones de chiffres clés
ENCRE = "2B2B2B"   # texte courant (jamais du noir pur)
GRIS = "7A8A87"    # sources, notes, axes
AMBRE = "E0A526"   # UNIQUEMENT pour signaler une alerte

# --- Une couleur fixe par groupe ATC (charte, page 3) ---------------------------------------
# Les groupes d'une même famille partagent une teinte.
COULEURS_ATC = {
    "M01AB": "D98E3F",  # anti-inflammatoires
    "M01AE": "A9652A",
    "N02BA": "D46A5A",  # antalgiques
    "N02BE": "9E3F35",
    "N05B": "8B7EC4",   # psycholeptiques
    "N05C": "5A4C94",
    "R03": "3E86B2",    # respiratoire
    "R06": "86B9D8",
}

# Couleurs d'accent utilisées dans les graphiques et les cartes de chaleur des feuilles.
# Le nom C_CORAL est gardé pour le code existant (sheets_data.py) ; la charte n'a pas de
# corail, on prend la sauge, couleur d'accent de la charte.
C_ACCENT = SAUGE
C_CORAL = SAUGE

# --- Polices : Playfair Display pour les titres, Lato pour tout le reste ---------------------
# Si la police n'est pas installée sur le poste, Excel en affiche une autre : rien ne casse.
POLICE_TITRE = "Playfair Display"
POLICE_TEXTE = "Lato"

TITLE = Font(name=POLICE_TITRE, size=18, bold=True, color=SAPIN)   # titre d'une feuille
H2 = Font(name=POLICE_TITRE, size=13, bold=True, color=SAPIN)      # titre d'un tableau
HEAD = Font(name=POLICE_TEXTE, size=10, bold=True, color="FFFFFF")  # en-tête de tableau, blanc sur sapin
BODY = Font(name=POLICE_TEXTE, size=10, color=ENCRE)               # cellules de données
NOTE = Font(name=POLICE_TEXTE, size=9, italic=True, color=GRIS)     # sources et notes
ALERT = Font(name=POLICE_TEXTE, size=10, bold=True, color=AMBRE)    # point de vigilance

# --- Remplissage, bordures, alignements -------------------------------------------------------
HEAD_FILL = PatternFill(fill_type="solid", start_color=SAPIN, end_color=SAPIN)  # en-têtes sapin

_TRAIT = Side(style="thin", color="D9DEDC")  # trait fin et clair : la charte veut des grilles discrètes
BOX = Border(left=_TRAIT, right=_TRAIT, top=_TRAIT, bottom=_TRAIT)

HEAD_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
WRAP = Alignment(vertical="top", wrap_text=True)  # texte long : retour à la ligne dans la cellule

# Style Excel de tableau de base, sobre ; nos propres en-têtes et bordures passent par-dessus
TABLE_STYLE = "TableStyleLight1"

# --- Formats de nombres -----------------------------------------------------------------------
# Excel affiche ces formats selon la langue du poste : en français, 1 315,0 et 4,6 %.
FMT_QTY = "#,##0.0"      # quantités (décimales possibles : l'unité du logiciel n'est pas documentée)
FMT_PCT = "0.0%"         # pourcentages (la valeur 0,046 s'affiche 4,6 %)
FMT_DATE = "dd/mm/yyyy"  # dates
FMT_TEXT = "@"           # texte, même s'il ressemble à un nombre (ex. « 2019-09 »)
FMT_IDX = "0.00"         # indices (1,13 = 13 % au-dessus de la moyenne)
FMT_STAT = "0.000"       # corrélations, R², coefficients
FMT_P = "0.0000"         # p-valeurs
FMT_INT = "0"            # nombres entiers sans séparateur (années, heures, comptages)
FMT_GENERAL = "General"  # laisse Excel décider (textes)


def guess_format(entete: str) -> str:
    """Devine le format d'une colonne d'après son titre, quand le code ne l'a pas précisé.

    Les règles vont de la plus précise à la plus générale : la première qui correspond gagne.
    L'ordre compte : « Fourchette basse (80 %) » contient « % » mais est une quantité,
    « Moyenne par jour » contient « jour » mais est un nombre.
    """
    e = entete.lower()
    if "p-valeur" in e:
        return FMT_P
    if any(mot in e for mot in ("fourchette", "prévision", "mae ", "par jour", "niveau moyen",
                                "équivalent en jours", "erreur absolue")):
        return FMT_QTY
    if "mase" in e:
        return FMT_IDX
    if "%" in e or e.startswith("part") or "évolution" in e or "gain du modèle" in e:
        return FMT_PCT
    if e in ("date", "semaine", "fin_semaine", "debut_semaine", "mois testé") or e.startswith("date"):
        return FMT_DATE
    if any(mot in e for mot in ("corrélation", "r²", "coef", "z robuste")):
        return FMT_STAT
    if any(mot in e for mot in ("indice", "/ autres", "amplitude")):
        return FMT_IDX
    if e in ("année", "heure") or e.startswith(("cellules", "dont", "mois où")):
        return FMT_INT
    if e in ("jour", "mois", "niveau", "période") or any(mot in e for mot in (
            "groupe", "libellé", "nature", "causalité", "verdict", "méthode", "contrôle", "décision",
            "détail", "statut", "source", "message", "thème", "définition", "exemple", "conclure",
            "mois le plus", "mois prévu", "lien significatif", "sensible", "référence naïve")):
        return FMT_GENERAL
    return FMT_QTY  # par défaut : une quantité vendue

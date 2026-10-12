"""Feuilles État_des_données, Stats_Calendrier, Confidentialité.   [Adelaida]

build(wb) : dessine les feuilles dans le modèle (lancé une fois, par scripts/build_template.py).
fill(wb, t) : remplit les tableaux et cellules nommées chaque mois (lancé par main.py).
"""
from __future__ import annotations

from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter

from .. import config
from ..analysis.profiles import HOUR_LABELS
from . import tables as X
from . import styles as S

G = config.GROUP_CODES
SHEETS = ["Stats_Calendrier", "Confidentialité", "État_des_données"]
TABLES = ["T_Sources", "T_Journal", "T_Ecarts", "T_Pics", "T_Jours", "T_Heures", "T_Affluence",
          "T_Petits_Comptages", "T_Conformite"]
NAMES = ["txt_run_info"]

H_SOURCES = ["Source", "Usage", "Statut"]
H_JOURNAL = ["Contrôle", "Export", "Statut", "Détail", "Décision"]
H_ECARTS = ["Export", "Période", "Groupe", "Valeur export", "Valeur recalculée (horaire)", "Écart", "Écart %"]
H_PICS = ["Date", "Groupe", "Quantité", "Médiane 29 j", "z robuste", "Décision"]
H_JOURS = ["Jour", *G, "Total"]
H_HEURES = ["Heure", *G, "Total"]
H_AFFLUENCE = ["Jour", *HOUR_LABELS]
H_COMPTAGES = ["Niveau", "Groupe", "Sensible (art. 9 RGPD)", "Cellules avec vente",
               f"Dont ≤ {config.SMALL_COUNT_THRESHOLD} unités", f"Part ≤ {config.SMALL_COUNT_THRESHOLD} unités",
               "Médiane des cellules non nulles"]
H_CONFORMITE = ["Étape", "Contenu"]


def _sheet(wb, name, color):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = color
    ws.column_dimensions["A"].width = 2
    return ws


def build(wb) -> None:
    # ------------------------------------------------------------------ Stats_Calendrier
    ws = _sheet(wb, "Stats_Calendrier", S.C_ACCENT)
    X.title(ws, "Quand vient la clientèle ? Jours, heures, affluence")
    X.note(ws, "B3", "Jours complets uniquement. Indice 1,10 = +10 % par rapport à la moyenne.")
    X.widths(ws, {"B": 12, **{get_column_letter(c): 9 for c in range(3, 27)}})
    head, nxt = X.add_table(ws, "T_Jours", 5, 2, H_JOURS, capacity=7, heading="Indice jour de semaine",
                            formats={h: S.FMT_IDX for h in H_JOURS[1:]})
    ws.conditional_formatting.add(f"C{head + 1}:K{head + 7}", ColorScaleRule(
        start_type="num", start_value=0.5, start_color="5B8DB8", mid_type="num", mid_value=1,
        mid_color="FFFFFF", end_type="num", end_value=1.3, end_color=S.C_CORAL))
    ch = BarChart()
    ch.title, ch.height, ch.width, ch.legend = "Indice jour de semaine (tous groupes)", 7, 14, None
    ch.add_data(Reference(ws, min_col=11, min_row=head, max_row=head + 7), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=2, min_row=head + 1, max_row=head + 7))
    ch.series[0].graphicalProperties.solidFill = S.C_ACCENT
    ws.add_chart(ch, f"M{head}")

    head, nxt = X.add_table(ws, "T_Heures", nxt + 6, 2, H_HEURES, capacity=24, heading="Part des ventes par heure",
                            formats={h: S.FMT_PCT for h in H_HEURES[1:]})
    ch = BarChart()
    ch.title, ch.height, ch.width, ch.legend = "Part des ventes par heure (tous groupes)", 8, 16, None
    ch.add_data(Reference(ws, min_col=11, min_row=head, max_row=head + 24), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=2, min_row=head + 1, max_row=head + 24))
    ch.series[0].graphicalProperties.solidFill = S.C_ACCENT
    ws.add_chart(ch, f"M{head}")

    head, nxt = X.add_table(ws, "T_Affluence", nxt, 2, H_AFFLUENCE, capacity=7,
                            heading="Affluence : ventes moyennes par jour et par heure (tous groupes)",
                            formats={h: S.FMT_QTY for h in H_AFFLUENCE[1:]})
    ws.conditional_formatting.add(f"C{head + 1}:Z{head + 7}", ColorScaleRule(
        start_type="min", start_color="FFFFFF", end_type="max", end_color=S.C_CORAL))

    # ------------------------------------------------------------------ Confidentialité
    ws = _sheet(wb, "Confidentialité", "6D597A")
    X.title(ws, "Partage des données : risque de ré-identification par niveau de détail")
    X.note(ws, "B3", f"Une cellule de {config.SMALL_COUNT_THRESHOLD} unités ou moins correspond très probablement "
                     "à une ou deux personnes : quelqu'un qui connaît la pharmacie peut relier la vente à un patient.")
    X.widths(ws, {"B": 18, "C": 70, "D": 20, "E": 16, "F": 16, "G": 16, "H": 18})
    head, nxt = X.add_table(ws, "T_Petits_Comptages", 5, 2, H_COMPTAGES, capacity=32)
    ws.conditional_formatting.add(f"G{head + 1}:G{head + 32}", ColorScaleRule(
        start_type="num", start_value=0, start_color="FFFFFF", end_type="num", end_value=1, end_color="C0392B"))
    X.add_table(ws, "T_Conformite", nxt, 2, H_CONFORMITE, capacity=9, wrap=True,
                heading="Du constat à la décision : fait, règle, conséquence, actions",
                comment="Détail dans la note PDF, partie 2. Références juridiques à faire valider par un juriste.")

    # ------------------------------------------------------------------ État_des_données
    ws = _sheet(wb, "État_des_données", "264653")
    X.title(ws, "État des données : sources, contrôles, corrections")
    X.name_cell(wb, "txt_run_info", ws, "B3", "", S.NOTE)
    ws["B4"] = "Attention : l'export mensuel du logiciel est faux ; ne pas l'utiliser pour piloter les achats."
    ws["B4"].font = S.ALERT
    X.widths(ws, {"B": 34, "C": 14, "D": 12, "E": 70, "F": 55, "G": 3, "H": 12, "I": 12, "J": 10, "K": 14,
                  "L": 16, "M": 12, "N": 10, "O": 3, "P": 12, "Q": 10, "R": 12, "S": 13, "T": 11, "U": 40})
    head, nxt = X.add_table(ws, "T_Sources", 6, 2, H_SOURCES, capacity=5, heading="Quel export pour quel usage")
    ws.column_dimensions["C"].width = 14
    # Les trois tableaux qui grandissent sont côte à côte, en bas : ils ne peuvent écraser aucune autre zone.
    X.add_table(ws, "T_Journal", nxt + 3, 2, H_JOURNAL, heading="Journal des contrôles", wrap=True)
    X.add_table(ws, "T_Ecarts", nxt + 3, 8, H_ECARTS, heading="Écarts entre exports et horaire",
                formats={"Valeur export": S.FMT_QTY, "Valeur recalculée (horaire)": S.FMT_QTY,
                         "Écart": S.FMT_QTY, "Écart %": S.FMT_PCT, "Période": S.FMT_TEXT})
    X.add_table(ws, "T_Pics", nxt + 3, 16, H_PICS, heading="Pics signalés (conservés)",
                formats={"Date": S.FMT_DATE, "Quantité": S.FMT_QTY, "Médiane 29 j": S.FMT_QTY, "z robuste": "0.0"})


def fill(wb, c, t) -> dict[str, int]:
    rows = {
        "T_Sources": X.fill_table(wb, "T_Sources", c.sources),
        "T_Journal": X.fill_table(wb, "T_Journal", c.journal),
        "T_Ecarts": X.fill_table(wb, "T_Ecarts", c.discrepancies),
        "T_Pics": X.fill_table(wb, "T_Pics", c.outliers),
        "T_Jours": X.fill_table(wb, "T_Jours", t["weekday"]),
        "T_Heures": X.fill_table(wb, "T_Heures", t["hourly"]),
        "T_Affluence": X.fill_table(wb, "T_Affluence", t["heatmap"]),
        "T_Petits_Comptages": X.fill_table(wb, "T_Petits_Comptages", t["privacy"]),
        "T_Conformite": X.fill_table(wb, "T_Conformite", t["compliance"]),
    }
    X.set_named(wb, "txt_run_info", t["run_info"])
    return rows

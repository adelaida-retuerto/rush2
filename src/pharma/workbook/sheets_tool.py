"""Outil de consultation des ventes pour le pharmacien (feuille Outil).   [Ihman]

L'outil est construit dans le modèle par build(wb), SANS MACROS : le pharmacien choisit les groupes
(Oui/Non) et une période, et des formules SOMME.SI.ENS additionnent les ventes des tableaux
T_Jour (une ligne par jour) et T_Heure (une ligne par heure).
fill(wb, c, t) remplit chaque mois ces deux tableaux et propose une période par défaut.
"""
from __future__ import annotations

import pandas as pd
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

from .. import config
from . import styles as S
from . import tables as X

G = config.GROUP_CODES
TABLES = ["T_Jour", "T_Heure"]
NAMES = ["periode_debut", "periode_fin", "note_outil"]
SHEETS = ["Outil", "Données_Jour", "Données_Heure"]
H_JOUR = ["Date", *G, "Total", "Jour"]
H_HEURE = ["Date", "Heure", *G]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _data_sheet(wb, name, table, headers):
    ws = wb.create_sheet(name)
    ws.sheet_properties.tabColor = S.GRIS
    X.add_table(ws, table, 1, 1, headers, formats={"Date": S.FMT_DATE, "Heure": "0", "Jour": S.FMT_TEXT})
    ws.freeze_panes = "B2"
    ws.column_dimensions["A"].width = 12


def build(wb) -> None:
    """Dessine la feuille Outil (sans macro : formules SOMME.SI.ENS sur T_Jour et T_Heure) et les feuilles de données."""
    ws = wb.create_sheet("Outil")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = S.SAUGE
    X.widths(ws, {"A": 2, "B": 12, "C": 52, "D": 14, "E": 14, "F": 14, "G": 14, "H": 14, "I": 12,
                  "J": 12, "K": 12, "L": 12, "M": 3})
    sel = {g: f"$D${7 + i}" for i, g in enumerate(G)}
    rng = "T_Jour[Date],\">=\"&$G$6,T_Jour[Date],\"<=\"&$G$7"
    rng_n1 = "T_Jour[Date],\">=\"&EDATE($G$6,-12),T_Jour[Date],\"<=\"&EDATE($G$7,-12)"

    X.title(ws, "Outil de consultation des ventes")
    ws["B3"] = ("Mode d'emploi : 1) choisissez Oui/Non pour chaque groupe (cellules jaunes) ; 2) choisissez une date "
                "de début et de fin : calendrier au double-clic dans Excel pour le web, sinon tapez JJ/MM/AAAA "
                "(un seul jour : même date deux fois). Tous les résultats se mettent à jour.")
    ws["B3"].font, ws["B3"].alignment = S.NOTE, Alignment(wrap_text=True)
    ws.merge_cells("B3:L3")
    ws.row_dimensions[3].height = 28

    # --- 1. Groupes
    X.h2(ws, "B5", "1. Groupes de médicaments")
    for j, h in enumerate(["Code ATC", "Libellé", "Inclure ?"]):
        c = ws.cell(6, 2 + j, h)
        c.font, c.fill, c.border = S.HEAD, S.HEAD_FILL, S.BOX
    dv_yes = DataValidation(type="list", formula1='"Oui,Non"', allow_blank=False,
                            error="Choisissez Oui ou Non", errorTitle="Valeur non valide")
    ws.add_data_validation(dv_yes)
    for i, g in enumerate(G):
        r = 7 + i
        ws.cell(r, 2, g).font = S.BOLD
        ws.cell(r, 3, config.GROUPS[g]).font = S.BODY
        c = ws.cell(r, 4, "Oui")
        c.fill, c.font, c.alignment = S.INPUT_FILL, S.BOLD, Alignment(horizontal="center")
        dv_yes.add(c)
        for k in range(2, 5):
            ws.cell(r, k).border = S.BOX
    ws["B15"], ws["B15"].font = "Groupes inclus :", S.NOTE
    ws["D15"], ws["D15"].font = '=COUNTIF($D$7:$D$14,"Oui")&" / 8"', S.BOLD

    # --- 2. Période : deux cellules nommées que le code met à jour (dernier mois complet par défaut)
    X.h2(ws, "F5", "2. Période")
    ws["F6"], ws["F7"] = "Date de début", "Date de fin"
    X.name_cell(wb, "periode_debut", ws, "G6")
    X.name_cell(wb, "periode_fin", ws, "G7")
    for a in ["G6", "G7"]:
        ws[a].fill, ws[a].font, ws[a].number_format, ws[a].border = S.INPUT_FILL, S.BOLD, S.FMT_DATE, S.BOX
    for a in ["F6", "F7"]:
        ws[a].font, ws[a].border = S.BODY, S.BOX
    for a, lab, f, fmt in [("8", "Nombre de jours", "=MAX(0,$G$7-$G$6+1)", S.FMT_INT),
                           ("9", "Contrôle", '=IF($G$7<$G$6,"Fin avant début !",IF(OR($G$6<$G$10,$G$7>$G$11),'
                                             '"Hors données","OK"))', None),
                           ("10", "Données du", "=MIN(T_Jour[Date])", S.FMT_DATE),
                           ("11", "au", "=MAX(T_Jour[Date])", S.FMT_DATE)]:
        ws[f"F{a}"], ws[f"F{a}"].font = lab, S.BODY
        ws[f"G{a}"], ws[f"G{a}"].font = f, S.BOLD
        if fmt:
            ws[f"G{a}"].number_format = fmt
    # Cellules au format date + validation « Date comprise entre » (Données > Validation des données) :
    # Excel pour le web ouvre un calendrier au double-clic ; sur Excel bureau, on tape JJ/MM/AAAA.
    dv_date = DataValidation(type="date", operator="between", formula1="$G$10", formula2="$G$11",
                             showInputMessage=True, promptTitle="Choisir une date",
                             prompt="Excel pour le web : double-cliquez pour ouvrir le calendrier. "
                                    "Excel sur ordinateur : tapez la date au format JJ/MM/AAAA. "
                                    "Dates autorisées : entre « Données du » et « au » (ci-dessous).",
                             error="Date en dehors des données disponibles (voir « Données du » et « au »).",
                             errorTitle="Date hors des données")
    ws.add_data_validation(dv_date)
    dv_date.add("G6")
    dv_date.add("G7")
    X.name_cell(wb, "note_outil", ws, "F12", "", S.NOTE)
    ws.conditional_formatting.add("G9", CellIsRule(operator="notEqual", formula=['"OK"'],
                                                   font=Font(color=S.AMBRE, bold=True)))

    # --- 3. Ventes sur la période
    r0 = 17
    X.h2(ws, f"B{r0}", "3. Ventes sur la période")
    heads = ["Code ATC", "Libellé", "Quantité", "Moyenne / jour", "Même période N-1", "Évolution", "Part de la sélection"]
    for j, h in enumerate(heads):
        c = ws.cell(r0 + 1, 2 + j, h)
        c.font, c.fill, c.border, c.alignment = S.HEAD, S.HEAD_FILL, S.BOX, S.HEAD_ALIGN
    ws.row_dimensions[r0 + 1].height = 30
    first, last = r0 + 2, r0 + 1 + len(G)
    tr = last + 1
    fmts = [None, None, S.FMT_QTY, S.FMT_QTY, S.FMT_QTY, S.FMT_PCT, S.FMT_PCT]
    for i, g in enumerate(G):
        r = first + i
        ws.cell(r, 2, g).font = S.BOLD
        ws.cell(r, 3, config.GROUPS[g]).font = S.BODY
        ws.cell(r, 4, f'=IF({sel[g]}="Oui",SUMIFS(T_Jour[{g}],{rng}),"")')
        ws.cell(r, 5, f'=IF(OR(D{r}="",$G$8=0),"",D{r}/$G$8)')
        ws.cell(r, 6, f'=IF({sel[g]}="Oui",SUMIFS(T_Jour[{g}],{rng_n1}),"")')
        ws.cell(r, 7, f'=IF(OR(D{r}="",F{r}="",F{r}=0),"",D{r}/F{r}-1)')
        ws.cell(r, 8, f'=IF(OR(D{r}="",$D${tr}=0),"",D{r}/$D${tr})')
        for k, fmt in zip(range(2, 9), fmts):
            ws.cell(r, k).border = S.BOX
            if k > 3:
                ws.cell(r, k).font = S.BODY
            if fmt:
                ws.cell(r, k).number_format = fmt
    for k, v in zip(range(2, 9), ["Total", "Groupes sélectionnés", f"=SUM(D{first}:D{last})",
                                  f'=IF($G$8=0,"",D{tr}/$G$8)', f"=SUM(F{first}:F{last})",
                                  f'=IF(F{tr}=0,"",D{tr}/F{tr}-1)', f'=IF(D{tr}=0,"",1)']):
        c = ws.cell(tr, k, v)
        c.font, c.fill, c.border = S.BOLD, S.LIGHT_FILL, S.BOX
        if fmts[k - 2]:
            c.number_format = fmts[k - 2]
    ws.cell(tr + 1, 2, "Quantités telles qu'enregistrées par la caisse (unité non documentée). "
                       "N-1 = mêmes dates un an plus tôt ; vide si hors historique.").font = S.NOTE
    ws.conditional_formatting.add(f"G{first}:G{tr}", CellIsRule(operator="lessThan", formula=["0"],
                                                                 font=Font(color=S.AMBRE)))
    ws.conditional_formatting.add(f"G{first}:G{tr}", CellIsRule(operator="greaterThan", formula=["0"],
                                                                 font=Font(color=S.SAUGE)))

    # --- 4. Répartition par heure (24 heures, taille fixe)
    hr0 = tr + 4
    X.h2(ws, f"B{hr0}", "4. Répartition par heure (groupes sélectionnés)")
    for j, h in enumerate(["Heure", "Quantité", "Moyenne / jour", "Part"]):
        c = ws.cell(hr0 + 1, 2 + j, h)
        c.font, c.fill, c.border = S.HEAD, S.HEAD_FILL, S.BOX
    h_first = hr0 + 2
    h_last = h_first + len(config.HOURS) - 1
    for i, hour in enumerate(config.HOURS):
        r = h_first + i
        ws.cell(r, 2, f"{hour:02d}h").font = S.BOLD
        terms = "+".join(f'IF({sel[g]}="Oui",SUMIFS(T_Heure[{g}],T_Heure[Date],">="&$G$6,'
                         f'T_Heure[Date],"<="&$G$7,T_Heure[Heure],{hour}),0)' for g in G)
        ws.cell(r, 3, f"={terms}").number_format = S.FMT_QTY
        ws.cell(r, 4, f'=IF($G$8=0,"",C{r}/$G$8)').number_format = S.FMT_QTY
        ws.cell(r, 5, f'=IF(SUM($C${h_first}:$C${h_last})=0,"",C{r}/SUM($C${h_first}:$C${h_last}))').number_format = S.FMT_PCT
        for k in range(2, 6):
            ws.cell(r, k).border = S.BOX
            if k > 2:
                ws.cell(r, k).font = S.BODY
    ws.conditional_formatting.add(f"E{h_first}:E{h_last}", ColorScaleRule(
        start_type="min", start_color="FFFFFF", end_type="max", end_color=S.SAUGE))
    ch = BarChart()
    ch.title, ch.y_axis.title, ch.legend = "Ventes par heure (sélection)", "Quantité", None
    ch.add_data(Reference(ws, min_col=3, min_row=hr0 + 1, max_row=h_last), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=2, min_row=h_first, max_row=h_last))
    ch.height, ch.width = 8, 16
    ch.series[0].graphicalProperties.solidFill = S.SAUGE
    ws.add_chart(ch, f"G{hr0 + 1}")

    # --- 5. Détail dans le temps (jour, semaine ou mois selon la longueur de la période)
    dr0 = h_last + 3
    n_rows = config.TOOL_DETAIL_ROWS
    X.h2(ws, f"B{dr0}", "5. Détail dans le temps (groupes sélectionnés)")
    ws.cell(dr0, 6, "Pas de temps :").font = S.BODY
    ws.cell(dr0, 7, f'=IF($G$8<={n_rows},"Jour",IF($G$8<={n_rows}*7,"Semaine","Mois"))').font = S.BOLD
    ws.cell(dr0 + 1, 2, f"Jour si la période fait {n_rows} jours ou moins, semaine (lundi-dimanche) jusqu'à "
                        f"{n_rows} semaines, mois au-delà.").font = S.NOTE
    head_row = dr0 + 2
    for j, h in enumerate(["Début", "Fin", *G, "Total"]):
        c = ws.cell(head_row, 2 + j, h)
        c.font, c.fill, c.border = S.HEAD, S.HEAD_FILL, S.BOX
    for i in range(n_rows):
        r = head_row + 1 + i
        start = "$G$6" if i == 0 else f'IF(OR(C{r - 1}="",C{r - 1}>=$G$7),"",C{r - 1}+1)'
        ws.cell(r, 2, f"={start}").number_format = S.FMT_DATE
        ws.cell(r, 3, f'=IF(B{r}="","",MIN($G$7,IF($G$7-$G$6+1<={n_rows},B{r},'
                      f'IF($G$7-$G$6+1<={n_rows}*7,B{r}+6-WEEKDAY(B{r},3),EOMONTH(B{r},0)))))').number_format = S.FMT_DATE
        for j, g in enumerate(G):
            c = ws.cell(r, 4 + j, f'=IF(OR($B{r}="",{sel[g]}<>"Oui"),"",'
                                  f'SUMIFS(T_Jour[{g}],T_Jour[Date],">="&$B{r},T_Jour[Date],"<="&$C{r}))')
            c.number_format = S.FMT_QTY
        ws.cell(r, 12, f'=IF($B{r}="","",SUM(D{r}:K{r}))').number_format = S.FMT_QTY
        for k in range(2, 13):
            ws.cell(r, k).border = S.BOX
            ws.cell(r, k).font = S.BOLD if k == 12 else S.BODY
    last_detail = head_row + n_rows
    ws.cell(last_detail + 1, 2, "Lignes vides : la période est entièrement couverte.").font = S.NOTE
    sc = BarChart()
    sc.type, sc.grouping, sc.overlap, sc.gapWidth = "col", "stacked", 100, 40
    sc.title, sc.height, sc.width, sc.y_axis.title = "Ventes des groupes sélectionnés (par groupe)", 9, 24, "Quantité"
    sc.add_data(Reference(ws, min_col=4, max_col=11, min_row=head_row, max_row=last_detail), titles_from_data=True)
    sc.set_categories(Reference(ws, min_col=2, min_row=head_row + 1, max_row=last_detail))
    sc.x_axis.number_format = "dd/mm/yy"
    for s, colr in zip(sc.series, S.PALETTE):
        s.graphicalProperties.solidFill = colr
        s.graphicalProperties.line.solidFill = colr
    ws.add_chart(sc, f"N{head_row}")
    ws.freeze_panes = "A5"

    _data_sheet(wb, "Données_Jour", "T_Jour", H_JOUR)
    _data_sheet(wb, "Données_Heure", "T_Heure", H_HEURE)


def table_jour(c) -> pd.DataFrame:
    """Une ligne par jour complet : date, ventes des 8 groupes, total, nom du jour."""
    jours = c.daily[G].round(2)
    jours.insert(0, "Date", jours.index)
    jours["Total"] = jours[G].sum(axis=1).round(2)
    jours["Jour"] = [JOURS_SEMAINE[d] for d in jours.index.dayofweek]  # dayofweek : 0 = lundi
    return jours.reset_index(drop=True)


def table_heure(c) -> pd.DataFrame:
    """Une ligne par heure des jours complets : date (le jour seul), heure de 0 à 23, ventes des 8 groupes.

    La date est gardée SANS l'heure : les formules comparent Date à la période choisie
    (« entre le 01/09 et le 30/09 ») ; avec l'heure, le dernier jour serait exclu.
    """
    heures = c.hourly[G]
    jours = heures.index.normalize()          # normalize() remet chaque horodatage à minuit : le jour seul
    heures = heures[jours.isin(c.daily.index)].round(2)  # seulement les jours complets, comme T_Jour
    heures.insert(0, "Date", heures.index.normalize())
    heures.insert(1, "Heure", heures.index.hour)
    return heures.reset_index(drop=True)


def periode_par_defaut(c) -> tuple[pd.Timestamp, pd.Timestamp]:
    """À l'ouverture, l'outil affiche le dernier mois complet (ex. du 01/09/2019 au 30/09/2019)."""
    fin = c.last_complete_month                   # dernier jour du mois, ex. 2019-09-30
    debut = fin - pd.offsets.MonthBegin(1)         # premier jour du même mois, ex. 2019-09-01
    return debut, fin


def fill(wb, c, t) -> dict[str, int]:
    """Remplit les données de l'outil et sa période par défaut ; renvoie le nombre de lignes écrites."""
    lignes = {
        "T_Jour": X.fill_table(wb, "T_Jour", table_jour(c)),
        "T_Heure": X.fill_table(wb, "T_Heure", table_heure(c)),
    }
    debut, fin = periode_par_defaut(c)
    X.set_named(wb, "periode_debut", debut)
    X.set_named(wb, "periode_fin", fin)
    X.set_named(wb, "note_outil", t["tool_note"])  # ex. « Dernier jour exporté : 08/10/2019, incomplet... »
    return lignes

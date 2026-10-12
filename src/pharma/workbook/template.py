"""Construction du modèle Excel (templates/workbook_template.xlsx).   [Adelaida : assemblage]

Lancé une seule fois, puis à chaque évolution volontaire de la mise en page :
    python scripts/build_template.py
Le modèle est versionné dans Git. Il peut ensuite être retouché à la main dans Excel (couleurs,
textes, graphiques), à condition de garder les tableaux et cellules nommés : `verify` le contrôle.
Pendant la mise à jour mensuelle, le modèle n'est jamais modifié.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

import importlib

from .. import config

SHEET_ORDER = ["Synthèse", "Cadrage", "Outil", "Stats_Groupes", "Stats_Calendrier", "Stats_Mensuel",
               "Environnement", "Prévision", "Confidentialité", "État_des_données", "Données_Jour", "Données_Heure"]
# Modules de feuilles de chaque flux (importés seulement quand on en a besoin)
# Modules de feuilles de chaque bloc : forecast (Jeanne), sales (Iman), data (Adelaida)
FLUX_MODULES = {"forecast": ["sheets_summary"], "sales": ["sheets_tool", "sheets_sales"], "data": ["sheets_data"]}
ALL_FLUX = ["forecast", "sales", "data"]


def modules(flux: list[str] = ALL_FLUX) -> list:
    return [importlib.import_module(f"{__package__}.{m}") for f in flux for m in FLUX_MODULES[f]]


def contract(flux: list[str] = ALL_FLUX) -> tuple[list[str], list[str]]:
    """Toutes les zones (tableaux, cellules nommées) que le code a le droit de remplir."""
    mods = modules(flux)
    return ([t for m in mods for t in m.TABLES], [n for m in mods for n in m.NAMES])


def build_template(path: Path = config.TEMPLATE_PATH, flux: list[str] = ALL_FLUX) -> Path:
    """Modèle complet (flux = les trois) ou partiel (aperçu d'un seul flux)."""
    wb = Workbook()
    wb.remove(wb.active)
    for m in modules(flux):
        if m.__name__.endswith("sheets_summary"):
            from ..analysis import forecast
            m.build(wb, forecast.summary_columns())
        else:
            m.build(wb)
    wb._sheets = [wb[n] for n in SHEET_ORDER if n in wb.sheetnames]
    wb.active = 0
    for ws in wb.worksheets:
        ws.sheet_view.zoomScale = 90
    wb.calculation.fullCalcOnLoad = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path

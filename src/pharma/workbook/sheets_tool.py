"""Outil de consultation des ventes pour le pharmacien (feuille Outil).   [Ihman]

L'outil est déjà construit dans le modèle, SANS MACROS : le pharmacien choisit les groupes
(Oui/Non) et une période, et des formules SOMME.SI.ENS additionnent les ventes des tableaux
T_Jour (une ligne par jour) et T_Heure (une ligne par heure).
fill(wb, c, t) remplit chaque mois ces deux tableaux et propose une période par défaut.
"""
from __future__ import annotations

import pandas as pd

from .. import config
from . import tables as X

G = config.GROUP_CODES
TABLES = ["T_Jour", "T_Heure"]
NAMES = ["periode_debut", "periode_fin", "note_outil"]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def build(wb) -> None:
    """Dessin de la feuille Outil dans le modèle : pas encore porté dans ce module (voir sheets_sales.build)."""
    raise NotImplementedError("sheets_tool.build : mise en page à reprendre depuis le modèle actuel")


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

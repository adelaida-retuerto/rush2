"""Nettoyage de l'export horaire (Pharma_Ventes_Hourly.csv), la source de référence.   [Adelaida]

C'est le niveau le plus fin : jour, semaine et mois sont recalculés à partir de lui.
Ce module dit quels jours sont complets ; les autres modules s'en servent pour exclure
les semaines et les mois incomplets.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import checks
from .checks import G


@dataclass
class HourlyResult:
    hourly: pd.DataFrame          # ventes horaires, sans doublon
    daily_all: pd.DataFrame       # ventes par jour recalculées, y compris jours partiels
    complete_day: pd.Series       # True si le jour est complet (sert à exclure semaines et mois incomplets)
    meta: dict = field(default_factory=dict)


def clean_hourly(export: pd.DataFrame, derived: pd.DataFrame | None, rows: list) -> HourlyResult:
    checks.scope(rows, "hourly", export)
    h = checks.duplicates_and_negatives(rows, "hourly", export)
    checks.derived_columns(rows, "hourly", derived)

    # Contrôle 5 : continuité. Une heure absente de l'export = heure manquante (hors 1er et dernier jour)
    full = pd.date_range(h.index.min().floor("D"), h.index.max().floor("D") + pd.Timedelta(hours=23), freq="h")
    missing = full.difference(h.index)
    first_day, last_day = h.index.min().floor("D"), h.index.max().floor("D")
    inner_missing = missing[(missing.floor("D") != first_day) & (missing.floor("D") != last_day)]
    checks.log(rows, "Heures manquantes (hors 1er et dernier jour)", "hourly", len(inner_missing) == 0,
               f"{len(inner_missing)} heure(s) manquante(s)", "Aucune action" if len(inner_missing) == 0
               else "Jours concernés exclus des statistiques journalières")

    # Contrôle 7 : premier et dernier jour (l'export peut commencer ou finir en cours de journée)
    first_hour, last_hour = h.index.min().hour, h.index.max().hour
    hour_share = h[G].sum(axis=1).groupby(h.index.hour).sum()
    share_before = float(hour_share[hour_share.index < first_hour].sum() / hour_share.sum())
    checks.log(rows, "Premier jour", "hourly", True,
               f"Export commence le {first_day:%d/%m/%Y} à {first_hour:02d}h ; les heures avant {first_hour}h "
               f"pèsent {share_before:.1%} des ventes habituelles", "Jour conservé (perte négligeable)")
    sales_after = float(hour_share[hour_share.index > last_hour].sum() / hour_share.sum())
    last_day_partial = sales_after > 0.01
    checks.log(rows, "Dernier jour", "hourly", not last_day_partial,
               f"Export s'arrête le {last_day:%d/%m/%Y} à {last_hour:02d}h ; les heures suivantes pèsent "
               f"{sales_after:.1%} des ventes habituelles",
               "Jour partiel : exclu des statistiques" if last_day_partial else "Jour conservé")

    # Unité : le logiciel ne la documente pas (consigne S1)
    frac = (h[G] % 1 != 0).sum()
    checks.log(rows, "Quantités non entières", "hourly", True,
               "Cellules décimales par groupe : " + ", ".join(f"{g}={int(frac[g])}" for g in G),
               "Unité non documentée : on parle de 'quantités', jamais de boîtes ni d'euros")

    # Jours recalculés et jours complets
    daily_all = h[G].resample("D").sum()
    complete_day = pd.Series(True, index=daily_all.index)
    if last_day_partial:
        complete_day[last_day] = False
    for d in set(inner_missing.floor("D")):
        complete_day[d] = False

    return HourlyResult(hourly=h[G], daily_all=daily_all, complete_day=complete_day,
                        meta={"first_day": first_day, "last_day": last_day, "last_day_partial": last_day_partial,
                              "first_hour": first_hour, "last_hour": last_hour})

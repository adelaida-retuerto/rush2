"""Profils de fréquentation : jours de semaine, heures, carte d'affluence.   [Adelaida]

Les tables ont une forme fixe (7 jours, 24 heures) quelles que soient les données, pour que
le modèle Excel n'ait jamais à changer de taille.
"""
from __future__ import annotations

import pandas as pd

from .. import config
from ..cleaning.run import CleanData

G = config.GROUP_CODES
WEEKDAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
HOUR_LABELS = [f"{h:02d}h" for h in config.HOURS]


def _complete_hours(c: CleanData) -> pd.DataFrame:
    h = c.hourly
    return h[h.index.normalize().isin(c.daily.index)]


def weekday_index(c: CleanData) -> pd.DataFrame:
    """Indice jour de semaine : moyenne du jour / moyenne globale (7 lignes)."""
    d = c.daily
    idx = d[G].groupby(d.index.dayofweek).mean() / d[G].mean()
    idx["Total"] = d[G].sum(axis=1).groupby(d.index.dayofweek).mean() / d[G].sum(axis=1).mean()
    idx = idx.reindex(range(7))
    idx.index = WEEKDAYS_FR
    idx.index.name = "Jour"
    return idx.reset_index()


def hourly_share(c: CleanData) -> pd.DataFrame:
    """Part des ventes par heure, sur 24 heures (24 lignes, 0 la nuit)."""
    h = _complete_hours(c)
    by_hour = h[G].groupby(h.index.hour).sum().reindex(config.HOURS, fill_value=0)
    by_hour["Total"] = by_hour[G].sum(axis=1)
    share = by_hour / by_hour.sum()
    share.index = HOUR_LABELS
    share.index.name = "Heure"
    return share.reset_index()


def weekday_hour_heatmap(c: CleanData) -> pd.DataFrame:
    """Ventes moyennes par jour de semaine et par heure, tous groupes (7 lignes x 24 heures)."""
    h = _complete_hours(c)
    tot = h[G].sum(axis=1)
    piv = tot.groupby([h.index.dayofweek, h.index.hour]).mean().unstack()
    piv = piv.reindex(index=range(7), columns=config.HOURS).fillna(0.0)
    piv.index = WEEKDAYS_FR
    piv.columns = HOUR_LABELS
    piv.index.name = "Jour"
    return piv.reset_index()

"""Contrôles communs aux 4 exports (socle partagé, créé au lancement du projet).

Chaque module d'export (hourly, daily, weekly, monthly) appelle ces fonctions, pour que le
journal des contrôles soit homogène : mêmes noms de contrôles, mêmes colonnes, mêmes décisions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config

G = config.GROUP_CODES
WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
JOURNAL_COLUMNS = ["Contrôle", "Export", "Statut", "Détail", "Décision"]
DISCREPANCY_COLUMNS = ["Export", "Période", "Groupe", "Valeur export", "Valeur recalculée (horaire)",
                       "Écart", "Écart %"]


def log(rows: list, check: str, export: str, ok: bool, detail: str, decision: str) -> None:
    """Ajoute une ligne au journal des contrôles."""
    rows.append({"Contrôle": check, "Export": export, "Statut": "OK" if ok else "ANOMALIE",
                 "Détail": detail, "Décision": decision})


def reference_daily(hourly: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Ventes journalières recalculées depuis l'horaire brut, tous les jours comptés complets.

    Sert à travailler seule : chacune peut comparer son export à l'horaire sans attendre
    le nettoyage complet de l'horaire (cleaning/hourly.py), qui affine ensuite les jours complets.
    """
    daily_all = hourly[G].resample("D").sum()
    return daily_all, pd.Series(True, index=daily_all.index)


def scope(rows: list, level: str, df: pd.DataFrame) -> None:
    """Contrôle 1 : périmètre (nombre de lignes, première et dernière date)."""
    log(rows, "Périmètre", level, True,
        f"{len(df)} lignes, du {df.index.min():%d/%m/%Y} au {df.index.max():%d/%m/%Y}", "Information")


def duplicates_and_negatives(rows: list, level: str, df: pd.DataFrame) -> pd.DataFrame:
    """Contrôles 2 à 4 : doublons de date, valeurs manquantes, valeurs négatives. Renvoie l'export sans doublon."""
    n_dup = int(df.index.duplicated().sum())
    log(rows, "Doublons de date", level, n_dup == 0, f"{n_dup} date(s) en double",
        "Aucune action" if n_dup == 0 else "Doublons supprimés (première occurrence gardée)")
    n_na = int(df[G].isna().sum().sum())
    log(rows, "Valeurs manquantes", level, n_na == 0, f"{n_na} valeur(s) manquante(s)",
        "Aucune action" if n_na == 0 else "À faire confirmer par le client")
    n_neg = int((df[G] < 0).sum().sum())
    log(rows, "Valeurs négatives", level, n_neg == 0, f"{n_neg} valeur(s) négative(s)",
        "Aucune action" if n_neg == 0 else "À faire confirmer par le client (retours ?)")
    return df[~df.index.duplicated()]


def derived_columns(rows: list, level: str, derived: pd.DataFrame | None) -> None:
    """Contrôle 6 : colonnes ajoutées par le logiciel (Year, Month, Weekday Name, Hour) cohérentes avec la date.

    Elles ne servent jamais à l'analyse (on recalcule tout depuis la date) ; une incohérence
    révélerait un export corrompu.
    """
    if derived is None or derived.empty:
        return
    idx = derived.index
    checks = []
    if "Year" in derived:
        checks.append(("Year", int((derived["Year"] != idx.year).sum())))
    if "Month" in derived:
        checks.append(("Month", int((derived["Month"] != idx.month).sum())))
    if "Weekday Name" in derived:
        expected = pd.Index([WEEKDAYS_EN[d] for d in idx.dayofweek])
        checks.append(("Weekday Name", int((derived["Weekday Name"].values != expected).sum())))
    if "Hour" in derived and level == "hourly":
        checks.append(("Hour", int((derived["Hour"] != idx.hour).sum())))
    n_bad = sum(n for _, n in checks)
    detail = ", ".join(f"{c} : {n} incohérence(s)" for c, n in checks) or "aucune colonne vérifiable"
    log(rows, "Colonnes dérivées cohérentes avec la date", level, n_bad == 0, detail,
        "Colonnes ignorées : toujours recalculées depuis la date")


def compare(export_df: pd.DataFrame, rebuilt: pd.DataFrame, level: str, label_fmt: str) -> pd.DataFrame:
    """Contrôle 9 : compare un export avec la même période recalculée depuis l'horaire."""
    joined = export_df[G].join(rebuilt[G], how="outer", lsuffix="_export", rsuffix="_recalc")
    records = []
    for g in G:
        e, r = joined[f"{g}_export"], joined[f"{g}_recalc"]
        bad = (e - r).abs() > config.RECONCILIATION_TOLERANCE
        bad |= e.isna() ^ r.isna()
        for ts in joined.index[bad]:
            ev, rv = e.get(ts), r.get(ts)
            records.append({
                "Export": level, "Période": ts.strftime(label_fmt), "Groupe": g,
                "Valeur export": None if pd.isna(ev) else round(float(ev), 3),
                "Valeur recalculée (horaire)": None if pd.isna(rv) else round(float(rv), 3),
                "Écart": None if pd.isna(ev) or pd.isna(rv) else round(float(ev - rv), 3),
                "Écart %": None if pd.isna(ev) or pd.isna(rv) or rv == 0 else round(float((ev - rv) / rv), 4),
            })
    return pd.DataFrame(records, columns=DISCREPANCY_COLUMNS)


def log_reconciliation(rows: list, level: str, export_df: pd.DataFrame, disc: pd.DataFrame, detail: str | None = None):
    n_periods = disc["Période"].nunique() if len(disc) else 0
    detail = detail or f"{n_periods} période(s) en écart sur {len(export_df)} ({len(disc)} cellule(s))"
    decision = ("Concorde : export validé" if not len(disc) else
                "Export écarté : toutes les statistiques sont recalculées depuis l'horaire")
    log(rows, "Réconciliation avec l'horaire", level, len(disc) == 0, detail, decision)


def flag_outliers(daily: pd.DataFrame) -> pd.DataFrame:
    """Contrôle 8 : pics journaliers (z-score robuste sur médiane glissante). Signalés, jamais supprimés."""
    rows = []
    w = config.OUTLIER_WINDOW_DAYS
    for g in G:
        x = daily[g]
        med = x.rolling(w, center=True, min_periods=w // 3).median()
        mad = (x - med).abs().rolling(w, center=True, min_periods=w // 3).median()
        z = (x - med) / (1.4826 * mad.replace(0, np.nan))
        mask = (z > config.OUTLIER_Z) & (x >= config.OUTLIER_MIN_QTY)
        for ts in x.index[mask]:
            rows.append({"Date": ts.date(), "Groupe": g, "Quantité": round(float(x[ts]), 2),
                         "Médiane 29 j": round(float(med[ts]), 2), "z robuste": round(float(z[ts]), 1),
                         "Décision": "Conservé (pas de preuve d'erreur), signalé"})
    cols = ["Date", "Groupe", "Quantité", "Médiane 29 j", "z robuste", "Décision"]
    return pd.DataFrame(rows, columns=cols).sort_values(["Date", "Groupe"]).reset_index(drop=True)

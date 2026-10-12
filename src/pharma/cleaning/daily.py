"""Nettoyage de l'export journalier (Pharma_Ventes_Daily.csv).   [Ihman]

Même modèle que hourly.py : on lance les contrôles communs (checks.py), puis les
contrôles propres au journalier, et chaque résultat est écrit dans le journal commun.
La référence reste l'horaire : le journalier est validé s'il concorde avec lui.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import checks
from .hourly import HourlyResult

# Dans l'export, la colonne Hour d'un jour = la somme des heures présentes ce jour-là.
# Un jour complet a les 24 heures : 0 + 1 + ... + 23 = 276.
HOUR_JOUR_COMPLET = sum(range(24))


@dataclass
class DailyResult:
    daily: pd.DataFrame              # ventes par jour, sans doublon (une ligne par jour, 8 groupes)
    jours_incomplets: pd.DataFrame   # jours où la colonne Hour n'est pas 276, avec sa valeur
    ecarts: pd.DataFrame             # cases qui ne concordent pas avec l'horaire (vide si tout va bien)


def reperer_jours_incomplets(derived: pd.DataFrame) -> pd.DataFrame:
    """Repère les jours auxquels il manque des heures, grâce à la colonne Hour.

    Exemple : 248 = 8 + 9 + ... + 23 (le jour commence à 8h),
    190 = 0 + 1 + ... + 19 (le jour s'arrête à 19h).
    Renvoie ces jours avec leur valeur de Hour : un tableau vide si tous sont complets.
    """
    incomplets = derived["Hour"] != HOUR_JOUR_COMPLET
    return derived.loc[incomplets, ["Hour"]]


def clean_daily(export: pd.DataFrame, derived: pd.DataFrame, rows: list,
                horaire: HourlyResult) -> DailyResult:
    """Contrôle l'export journalier et écrit chaque résultat dans le journal (rows).

    export   : ventes lues par loading.load_export("daily")
    derived  : colonnes Year, Month, Hour, Weekday Name, lues par loading.load_derived_columns("daily")
    horaire  : résultat de hourly.clean_hourly, qui sert de référence
    """
    # Contrôles communs : périmètre, doublons, manquants, négatifs, Year/Month/Weekday Name
    checks.scope(rows, "daily", export)
    journalier = checks.duplicates_and_negatives(rows, "daily", export)
    checks.derived_columns(rows, "daily", derived)

    # Contrôle propre au journalier : la colonne Hour révèle les jours incomplets
    incomplets = reperer_jours_incomplets(derived)
    detail = ", ".join(f"{jour:%d/%m/%Y} (Hour = {h})" for jour, h in incomplets["Hour"].items())
    checks.log(rows, "Jours incomplets (colonne Hour ≠ 276)", "daily", len(incomplets) == 0,
               detail or "Tous les jours sont complets",
               "Information : c'est l'horaire qui décide quels jours sont exclus des statistiques")

    # Réconciliation : chaque jour doit égaler la somme de ses heures dans l'horaire
    ecarts = checks.compare(journalier, horaire.daily_all, "daily", "%d/%m/%Y")
    checks.log_reconciliation(rows, "daily", journalier, ecarts)

    return DailyResult(daily=journalier, jours_incomplets=incomplets, ecarts=ecarts)


# Test : depuis le dossier src, lancer   python -m pharma.cleaning.daily
if __name__ == "__main__":
    from . import hourly, loading

    journal = []
    horaire = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    resultat = clean_daily(loading.load_export("daily"), loading.load_derived_columns("daily"), journal, horaire)

    # On n'affiche que les lignes du journal qui concernent le journalier
    lignes_daily = pd.DataFrame(journal)
    print(lignes_daily[lignes_daily["Export"] == "daily"][["Contrôle", "Statut", "Détail"]].to_string(index=False))

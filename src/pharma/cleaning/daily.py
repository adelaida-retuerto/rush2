"""Nettoyage de l'export journalier (Pharma_Ventes_Daily.csv).   [Ihman]

Contrat (docs/data_contract.md) :
    clean_daily(export, derived, daily_all, complete_day, rows) -> (daily, ecarts)

L'horaire est la référence : l'export journalier sert de contrôle. Les ventes renvoyées
sont les jours COMPLETS recalculés depuis l'horaire. Chaque contrôle écrit sa ligne dans
le journal commun (rows).
"""
from __future__ import annotations

import pandas as pd

from .. import atc
from . import checks
from .checks import G

# Dans l'export, la colonne Hour d'un jour = la somme des heures présentes ce jour-là.
# Un jour complet a les 24 heures : 0 + 1 + ... + 23 = 276.
HOUR_JOUR_COMPLET = sum(range(24))


def reperer_jours_incomplets(derived: pd.DataFrame) -> pd.DataFrame:
    """Repère les jours auxquels il manque des heures, grâce à la colonne Hour.

    Exemple : 248 = 8 + 9 + ... + 23 (le jour commence à 8h),
    190 = 0 + 1 + ... + 19 (le jour s'arrête à 19h).
    Renvoie ces jours avec leur valeur de Hour : un tableau vide si tous sont complets.
    """
    incomplets = derived["Hour"] != HOUR_JOUR_COMPLET
    return derived.loc[incomplets, ["Hour"]]


def signaler_codes_non_suivis(rows: list, niveau: str, derived: pd.DataFrame | None) -> None:
    """Écrit dans le journal les colonnes de l'export qui sont des codes ATC non suivis, avec leur famille.

    loading.py ne garde que les 8 groupes de config.GROUPS : une colonne en plus (nouveau code ATC
    ajouté par le logiciel de caisse) arrive dans les colonnes « dérivées ». On la signale pour
    qu'elle soit ajoutée à config.GROUPS (et au modèle Excel) au lieu de passer inaperçue.
    """
    colonnes = [] if derived is None else list(derived.columns)
    nouveaux = atc.codes_non_suivis(colonnes)
    checks.log(rows, "Nouveaux codes ATC dans l'export", niveau, len(nouveaux) == 0,
               ", ".join(f"{code} ({atc.famille(code)})" for code in nouveaux) or "Aucun : les 8 groupes suivis",
               "Aucune action" if not nouveaux else "À ajouter dans config.GROUPS et le modèle Excel pour les analyser")


def clean_daily(export: pd.DataFrame, derived: pd.DataFrame | None, daily_all: pd.DataFrame,
                complete_day: pd.Series, rows: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Contrôle l'export journalier et renvoie (jours complets recalculés depuis l'horaire, écarts).

    export       : ventes lues par loading.load_export("daily")
    derived      : colonnes Year, Month, Hour, Weekday Name (loading.load_derived_columns("daily"))
    daily_all    : ventes par jour recalculées depuis l'horaire (tous les jours)
    complete_day : True si le jour est complet selon l'horaire
    rows         : le journal commun, où chaque contrôle ajoute sa ligne
    """
    # Contrôles 1 à 4 : périmètre, doublons, manquants, négatifs
    checks.scope(rows, "daily", export)
    journalier = checks.duplicates_and_negatives(rows, "daily", export)

    # Contrôle 5 : aucun jour ne doit manquer entre le premier et le dernier
    tous_les_jours = pd.date_range(journalier.index.min(), journalier.index.max(), freq="D")
    manquants = tous_les_jours.difference(journalier.index)
    checks.log(rows, "Jours manquants dans la suite", "daily", len(manquants) == 0,
               f"{len(manquants)} jour(s) manquant(s)",
               "Aucune action" if len(manquants) == 0 else "Jours recalculés depuis l'horaire")

    # Contrôle 6 : Year, Month, Weekday Name cohérents avec la date
    checks.derived_columns(rows, "daily", derived)

    # Nouveau code ATC dans l'export ? (colonnes hors des 8 groupes suivis, rangées dans leur famille)
    signaler_codes_non_suivis(rows, "daily", derived)

    # Contrôle propre au journalier : la colonne Hour révèle les jours incomplets
    if derived is not None and "Hour" in derived:
        incomplets = reperer_jours_incomplets(derived)
        detail = ", ".join(f"{jour:%d/%m/%Y} (Hour = {h})" for jour, h in incomplets["Hour"].items())
        checks.log(rows, "Jours incomplets selon la colonne Hour (≠ 276)", "daily", len(incomplets) == 0,
                   detail or "Tous les jours sont complets",
                   "Information : l'horaire décide quels jours sont exclus (contrôle suivant)")

    # Contrôle 7 : les jours incomplets selon l'horaire sont exclus des ventes propres
    exclus = complete_day[~complete_day].index
    checks.log(rows, "Jours incomplets exclus", "daily", len(exclus) == 0,
               ", ".join(f"{jour:%d/%m/%Y}" for jour in exclus) or "Aucun",
               "Exclus des statistiques journalières" if len(exclus) else "Aucune action")

    # Contrôle 9 : chaque jour de l'export doit égaler la somme de ses heures
    ecarts = checks.compare(journalier, daily_all, "daily", "%d/%m/%Y")
    checks.log_reconciliation(rows, "daily", journalier, ecarts)

    # Ventes propres : les jours complets, recalculés depuis l'horaire
    jours_complets = complete_day[complete_day].index
    daily = daily_all.loc[jours_complets, G]
    return daily, ecarts


# Test : depuis le dossier src, lancer   python -m pharma.cleaning.daily
if __name__ == "__main__":
    from . import hourly, loading

    journal = []
    horaire = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    daily, ecarts = clean_daily(loading.load_export("daily"), loading.load_derived_columns("daily"),
                                horaire.daily_all, horaire.complete_day, journal)

    # On n'affiche que les lignes du journal qui concernent le journalier
    lignes = pd.DataFrame(journal)
    print(lignes[lignes["Export"] == "daily"][["Contrôle", "Statut", "Détail"]].to_string(index=False))
    print(f"\nVentes propres : {len(daily)} jours complets, du {daily.index.min():%d/%m/%Y} au {daily.index.max():%d/%m/%Y}")

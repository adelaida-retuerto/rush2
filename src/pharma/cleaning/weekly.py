"""Nettoyage de l'export hebdomadaire (Pharma_Ventes_Weekly.csv).   [Ihman]

Contrat (docs/data_contract.md) :
    clean_weekly(export, derived, daily_all, complete_day, rows) -> (weekly, ecarts)

L'horaire est la référence : l'export hebdomadaire sert de contrôle. Les ventes renvoyées
sont les semaines COMPLÈTES (lundi -> dimanche, datées du dimanche) recalculées depuis
l'horaire. Chaque contrôle écrit sa ligne dans le journal commun (rows).
"""
from __future__ import annotations

import pandas as pd

from . import checks
from .checks import G
from .daily import signaler_codes_non_suivis


def verifier_dimanches(hebdomadaire: pd.DataFrame) -> pd.DataFrame:
    """Renvoie les semaines qui ne sont pas datées d'un dimanche : un tableau vide si tout va bien."""
    # dayofweek numérote les jours de 0 (lundi) à 6 (dimanche)
    pas_dimanche = hebdomadaire.index.dayofweek != 6
    return hebdomadaire[pas_dimanche]


def verifier_ecarts(hebdomadaire: pd.DataFrame) -> pd.DataFrame:
    """Renvoie les semaines dont l'écart avec la précédente n'est pas de 7 jours, avec cet écart.

    Plus de 7 jours : une semaine manque. Moins : deux lignes se chevauchent.
    """
    dates = hebdomadaire.index.to_series()
    # diff() calcule, pour chaque date, le temps écoulé depuis la date précédente
    ecarts_en_jours = dates.diff().dt.days
    # La première semaine n'a pas de précédente (écart vide) : on ne la compte pas
    anormal = ecarts_en_jours.notna() & (ecarts_en_jours != 7)
    return ecarts_en_jours[anormal].to_frame("ecart_en_jours")


def clean_weekly(export: pd.DataFrame, derived: pd.DataFrame | None, daily_all: pd.DataFrame,
                 complete_day: pd.Series, rows: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Contrôle l'export hebdomadaire et renvoie (semaines complètes recalculées depuis l'horaire, écarts).

    export       : ventes lues par loading.load_export("weekly")
    derived      : colonnes ajoutées par le logiciel (aucune pour l'hebdomadaire)
    daily_all    : ventes par jour recalculées depuis l'horaire (tous les jours)
    complete_day : True si le jour est complet selon l'horaire
    rows         : le journal commun, où chaque contrôle ajoute sa ligne
    """
    # Contrôles 1 à 4 : périmètre, doublons, manquants, négatifs
    checks.scope(rows, "weekly", export)
    hebdomadaire = checks.duplicates_and_negatives(rows, "weekly", export)

    # Contrôle propre à l'hebdomadaire : chaque semaine est datée de son dernier jour, le dimanche
    pas_dimanche = verifier_dimanches(hebdomadaire)
    checks.log(rows, "Semaines datées d'un dimanche", "weekly", len(pas_dimanche) == 0,
               f"{len(pas_dimanche)} semaine(s) ne finissant pas un dimanche",
               "Aucune action" if len(pas_dimanche) == 0 else "Semaines recalculées depuis l'horaire")

    # Contrôle 5 : aucune semaine ne doit manquer (7 jours entre deux semaines)
    ecarts_dates = verifier_ecarts(hebdomadaire)
    checks.log(rows, "Semaines manquantes dans la suite", "weekly", len(ecarts_dates) == 0,
               f"{len(ecarts_dates)} écart(s) différent(s) de 7 jours",
               "Aucune action" if len(ecarts_dates) == 0 else "Semaines recalculées depuis l'horaire")

    # Contrôle 6 : colonnes dérivées (aucune dans l'hebdomadaire : rien n'est écrit)
    checks.derived_columns(rows, "weekly", derived)

    # Nouveau code ATC dans l'export ? (même contrôle que daily.py)
    signaler_codes_non_suivis(rows, "weekly", derived)

    # Contrôle 9 : on additionne les jours de l'horaire par semaine finissant le dimanche (W-SUN)
    semaines_recalculees = daily_all.resample("W-SUN").sum()
    ecarts = checks.compare(hebdomadaire, semaines_recalculees, "weekly", "%d/%m/%Y")
    checks.log_reconciliation(rows, "weekly", hebdomadaire, ecarts)

    # Contrôle 7 : une semaine est complète si ses 7 jours sont complets selon l'horaire
    jours_complets = complete_day.resample("W-SUN").sum()
    semaine_complete = jours_complets == 7
    incompletes = jours_complets[~semaine_complete]
    checks.log(rows, "Semaines incomplètes exclues", "weekly", len(incompletes) == 0,
               ", ".join(f"semaine au {s:%d/%m/%Y} ({n} jour(s) complet(s))" for s, n in incompletes.items()) or "Aucune",
               "Exclues des statistiques hebdomadaires" if len(incompletes) else "Aucune action")

    # Ventes propres : les semaines complètes, recalculées depuis l'horaire
    weekly = semaines_recalculees.loc[semaine_complete[semaine_complete].index, G]
    return weekly, ecarts


# Test : depuis le dossier src, lancer   python -m pharma.cleaning.weekly
if __name__ == "__main__":
    from . import hourly, loading

    journal = []
    horaire = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    weekly, ecarts = clean_weekly(loading.load_export("weekly"), loading.load_derived_columns("weekly"),
                                  horaire.daily_all, horaire.complete_day, journal)

    # On n'affiche que les lignes du journal qui concernent l'hebdomadaire
    lignes = pd.DataFrame(journal)
    print(lignes[lignes["Export"] == "weekly"][["Contrôle", "Statut", "Détail"]].to_string(index=False))
    print(f"\nVentes propres : {len(weekly)} semaines complètes, du {weekly.index.min():%d/%m/%Y} au {weekly.index.max():%d/%m/%Y}")

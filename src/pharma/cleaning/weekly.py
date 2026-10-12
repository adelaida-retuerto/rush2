"""Nettoyage de l'export hebdomadaire (Pharma_Ventes_Weekly.csv).   [Ihman]

Même modèle que hourly.py : contrôles communs (checks.py), puis contrôles propres
à l'hebdomadaire, chaque résultat étant écrit dans le journal commun.
La référence reste l'horaire : chaque semaine doit égaler la somme de ses jours.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import checks
from .hourly import HourlyResult


@dataclass
class WeeklyResult:
    weekly: pd.DataFrame                # ventes par semaine (datée du dimanche), sans doublon
    semaine_complete: pd.Series         # True si la semaine a ses 7 jours complets
    semaines_incompletes: pd.DataFrame  # semaines de moins de 7 jours complets, avec leur nombre
    ecarts: pd.DataFrame                # cases qui ne concordent pas avec l'horaire (vide si tout va bien)


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


def clean_weekly(export: pd.DataFrame, derived: pd.DataFrame, rows: list,
                 horaire: HourlyResult) -> WeeklyResult:
    """Contrôle l'export hebdomadaire et écrit chaque résultat dans le journal (rows).

    export   : ventes lues par loading.load_export("weekly")
    derived  : colonnes ajoutées par le logiciel (aucune pour l'hebdomadaire, le contrôle passe alors)
    horaire  : résultat de hourly.clean_hourly, qui sert de référence
    """
    # Contrôles communs : périmètre, doublons, manquants, négatifs, colonnes dérivées
    checks.scope(rows, "weekly", export)
    hebdomadaire = checks.duplicates_and_negatives(rows, "weekly", export)
    checks.derived_columns(rows, "weekly", derived)

    # Contrôles propres à l'hebdomadaire : dates des semaines
    pas_dimanche = verifier_dimanches(hebdomadaire)
    checks.log(rows, "Semaines datées d'un dimanche", "weekly", len(pas_dimanche) == 0,
               f"{len(pas_dimanche)} semaine(s) ne finissant pas un dimanche",
               "Aucune action" if len(pas_dimanche) == 0 else "Découpage des semaines à faire confirmer par le client")

    ecarts_dates = verifier_ecarts(hebdomadaire)
    checks.log(rows, "7 jours entre deux semaines", "weekly", len(ecarts_dates) == 0,
               f"{len(ecarts_dates)} écart(s) différent(s) de 7 jours",
               "Aucune action" if len(ecarts_dates) == 0 else "Semaines manquantes : recalculées depuis l'horaire")

    # Réconciliation : on additionne les jours de l'horaire par semaine finissant le dimanche (W-SUN)
    semaines_recalculees = horaire.daily_all.resample("W-SUN").sum()
    ecarts = checks.compare(hebdomadaire, semaines_recalculees, "weekly", "%d/%m/%Y")
    checks.log_reconciliation(rows, "weekly", hebdomadaire, ecarts)

    # Semaines incomplètes : moins de 7 jours complets selon l'horaire (complete_day)
    jours_complets = horaire.complete_day.resample("W-SUN").sum()
    semaine_complete = jours_complets == 7
    incompletes = jours_complets[~semaine_complete].to_frame("jours_complets")
    detail = ", ".join(f"semaine au {s:%d/%m/%Y} ({n} jour(s))" for s, n in incompletes["jours_complets"].items())
    checks.log(rows, "Semaines incomplètes", "weekly", len(incompletes) == 0,
               detail or "Toutes les semaines sont complètes",
               "Signalées, exclues des statistiques hebdomadaires")

    return WeeklyResult(weekly=hebdomadaire, semaine_complete=semaine_complete,
                        semaines_incompletes=incompletes, ecarts=ecarts)


# Test : depuis le dossier src, lancer   python -m pharma.cleaning.weekly
if __name__ == "__main__":
    from . import hourly, loading

    journal = []
    horaire = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    resultat = clean_weekly(loading.load_export("weekly"), loading.load_derived_columns("weekly"), journal, horaire)

    # On n'affiche que les lignes du journal qui concernent l'hebdomadaire
    lignes_weekly = pd.DataFrame(journal)
    print(lignes_weekly[lignes_weekly["Export"] == "weekly"][["Contrôle", "Statut", "Détail"]].to_string(index=False))

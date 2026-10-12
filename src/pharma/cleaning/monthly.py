"""Nettoyage mensuel : contrôle de l'export et recalcul depuis l'horaire."""

from __future__ import annotations

import pandas as pd

from . import checks
from .checks import G


def clean_monthly(
    export: pd.DataFrame,
    derived: pd.DataFrame | None,
    daily_all: pd.DataFrame,
    complete_day: pd.Series,
    rows: list
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renvoie les mois complets recalculés et les écarts avec l'export."""

    checks.scope(rows, "monthly", export)
    mensuel = checks.duplicates_and_negatives(rows, "monthly", export)

    # Vérifier que les dates correspondent au dernier jour du mois
    mauvaises_dates = ~mensuel.index.is_month_end
    checks.log(
        rows, "Dates de fin de mois", "monthly",
        not mauvaises_dates.any(),
        f"{int(mauvaises_dates.sum())} date(s) hors fin de mois",
        "Mois recalculés depuis l'horaire"
    )

    # Vérifier la continuité des mois et leur unicité
    periodes = mensuel.index.to_period("M")
    calendrier = pd.period_range(periodes.min(), periodes.max(), freq="M")
    manquants = calendrier.difference(periodes)
    doublons = int(periodes.duplicated().sum())

    checks.log(
        rows, "Mois manquants ou répétés", "monthly",
        len(manquants) == 0 and doublons == 0,
        f"{len(manquants)} mois absent(s), {doublons} mois répété(s)",
        "Mois recalculés depuis l'horaire"
    )

    checks.derived_columns(rows, "monthly", derived)

    # Recalculer les ventes, dates placées en fin de mois
    mois_recalcules = daily_all[G].resample("ME").sum()

    ecarts = checks.compare(
        mensuel, mois_recalcules, "monthly", "%Y-%m"
    )
    checks.log_reconciliation(rows, "monthly", mensuel, ecarts)

    # Un mois est complet si tous ses jours sont complets
    jours_complets = complete_day.reindex(
        daily_all.index, fill_value=False
    ).fillna(False).astype(bool).resample("ME").sum()

    complet = jours_complets == jours_complets.index.days_in_month
    incomplets = jours_complets.loc[~complet]

    checks.log(
        rows, "Mois incomplets exclus", "monthly",
        len(incomplets) == 0,
        ", ".join(
            f"{date:%Y-%m} ({int(nombre)} jour(s) complet(s))"
            for date, nombre in incomplets.items()
        ) or "Aucun",
        "Exclus de la prévision" if len(incomplets) else "Aucune action"
    )

    monthly = mois_recalcules.loc[
        complet[complet].index, G
    ].copy()

    return monthly, ecarts
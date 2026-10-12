"""Statistiques descriptives des ventes (feuille Stats_Groupes et Stats_Mensuel).   [Ihman]

Appelé par pipeline.py, avec c = résultat du nettoyage (CleanData) :
    group_volumes(c)     -> T_Groupes        poids de chaque groupe
    seasonality_index(c) -> T_Saisonnalite   indice de saison par mois
    peak_months(c)       -> T_Mois_Forts     mois le plus fort et le plus faible
    year_to_date(c)      -> T_Cumul          cumul de l'année en cours face à l'année précédente
    yearly(c)            -> T_Annees         totaux par année complète
    monthly_table(c)     -> T_Mensuel        ventes mois par mois

On n'utilise que des périodes COMPLÈTES : c.daily (jours complets) et c.monthly (mois complets).
"""
from __future__ import annotations

import pandas as pd

from .. import config

G = config.GROUP_CODES
NOMS_MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
             "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


def group_volumes(c) -> pd.DataFrame:
    """Poids de chaque groupe sur toute la période : total, part du volume, moyenne et médiane par jour."""
    jours = c.daily[G]
    totaux = jours.sum()
    return pd.DataFrame({
        "Groupe": G,
        "Libellé": [config.GROUPS[g] for g in G],
        "Total période": totaux.values.round(1),
        "Part du volume": (totaux / totaux.sum()).values.round(4),  # fraction : Excel l'affiche en %
        "Moyenne par jour": jours.mean().values.round(2),
        # La médiane (la valeur du milieu) résiste aux pics : utile pour les groupes irréguliers
        "Médiane par jour": jours.median().values.round(2),
    })


def annees_completes(c) -> pd.DataFrame:
    """Les mois des années où les 12 mois sont complets (2014 à 2018 aujourd'hui)."""
    mois = c.monthly[G]
    nb_mois = mois.groupby(mois.index.year).size()
    completes = nb_mois[nb_mois == 12].index
    return mois[mois.index.year.isin(completes)]


def seasonality_index(c) -> pd.DataFrame:
    """Indice de saison : ventes moyennes de chaque mois de l'année / moyenne de tous les mois.

    1,00 = un mois habituel ; 1,50 = 50 % au-dessus ; 0,70 = 30 % en dessous.
    Calculé sur les années complètes, pour que chaque mois de l'année compte autant de fois.
    """
    mois = annees_completes(c)
    moyenne_par_mois = mois.groupby(mois.index.month).mean()  # 12 lignes : janvier... décembre
    indice = (moyenne_par_mois / mois.mean()).round(3)
    indice.insert(0, "Mois", [NOMS_MOIS[m - 1] for m in indice.index])
    return indice.reset_index(drop=True)


def peak_months(c) -> pd.DataFrame:
    """Pour chaque groupe : son mois le plus fort, le plus faible, et l'écart entre les deux."""
    indice = seasonality_index(c).set_index("Mois")
    lignes = []
    for g in G:
        fort, faible = indice[g].idxmax(), indice[g].idxmin()  # idxmax = le mois où l'indice est le plus haut
        lignes.append({
            "Groupe": g,
            "Mois le plus fort": fort,
            "Indice max": indice.loc[fort, g],
            "Mois le plus faible": faible,
            "Indice min": indice.loc[faible, g],
            # 3,0 = le mois fort vend 3 fois plus que le mois faible
            "Amplitude max sur min": round(indice.loc[fort, g] / indice.loc[faible, g], 2),
        })
    return pd.DataFrame(lignes)


def year_to_date(c) -> pd.DataFrame:
    """Cumul de l'année en cours (janvier -> dernier mois complet) face à la même période un an plus tôt.

    Comparer à la même période évite de comparer 9 mois de 2019 à 12 mois de 2018.
    """
    fin = c.last_complete_month
    mois = c.monthly[G]
    cette_annee = mois[(mois.index.year == fin.year) & (mois.index.month <= fin.month)].sum()
    annee_avant = mois[(mois.index.year == fin.year - 1) & (mois.index.month <= fin.month)].sum()
    cumul = pd.DataFrame({
        "Groupe": G,
        "Cumul année en cours": cette_annee.values.round(1),
        "Cumul année précédente": annee_avant.values.round(1),
        "Évolution": (cette_annee / annee_avant - 1).values.round(4),  # fraction : +0,05 = +5 %
    })
    # Pour le titre du tableau (txt_cumul_titre) : « janvier à septembre 2019 face à 2018 »
    cumul.attrs["periode"] = f"janvier à {NOMS_MOIS[fin.month - 1].lower()} {fin.year} face à {fin.year - 1}"
    return cumul


def yearly(c) -> pd.DataFrame:
    """Total des ventes par année complète, par groupe (l'année en cours est dans year_to_date)."""
    mois = annees_completes(c)
    annees = mois.groupby(mois.index.year).sum().round(1)
    annees["Total"] = annees[G].sum(axis=1).round(1)
    annees.insert(0, "Année", annees.index)
    return annees.reset_index(drop=True)


def monthly_table(c) -> pd.DataFrame:
    """Ventes mois par mois (mois complets), par groupe, avec le total."""
    mois = c.monthly[G].round(1)
    mois["Total"] = mois[G].sum(axis=1).round(1)
    mois.insert(0, "Mois", mois.index.strftime("%Y-%m"))  # texte « 2019-09 », comme le contrat
    return mois.reset_index(drop=True)


# Test : depuis le dossier src, lancer   python -m pharma.analysis.descriptive
if __name__ == "__main__":
    from types import SimpleNamespace

    from ..cleaning import hourly, loading
    from ..cleaning.daily import clean_daily

    # En attendant run.py (qui a besoin de monthly.py), on construit c comme le décrit le contrat :
    # jours complets, et mois complets recalculés depuis l'horaire.
    journal = []
    h = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    daily, _ = clean_daily(loading.load_export("daily"), loading.load_derived_columns("daily"),
                           h.daily_all, h.complete_day, journal)
    jours_complets = h.complete_day.resample("ME").sum()
    mois_complets = jours_complets[jours_complets == jours_complets.index.days_in_month].index
    monthly = h.daily_all.resample("ME").sum().loc[mois_complets]
    c = SimpleNamespace(daily=daily, monthly=monthly, last_complete_month=monthly.index.max())

    for nom, tableau in [("T_Groupes", group_volumes(c)), ("T_Saisonnalite", seasonality_index(c)),
                         ("T_Mois_Forts", peak_months(c)), ("T_Cumul", year_to_date(c)),
                         ("T_Annees", yearly(c)), ("T_Mensuel", monthly_table(c).tail(3))]:
        print(f"\n{nom}")
        print(tableau.to_string(index=False))
    print("\nTitre du cumul :", year_to_date(c).attrs["periode"])

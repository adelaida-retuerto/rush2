"""Tests du nettoyage de l'export hebdomadaire (src/pharma/cleaning/weekly.py).   [Ihman]

Lancer depuis la racine du projet :  python -m pytest tests/test_cleaning_weekly.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from pharma import config  # noqa: E402
from pharma.cleaning.weekly import clean_weekly  # noqa: E402

G = config.GROUP_CODES


def donnees_hebdomadaires():
    """3 semaines complètes (lundi 01/01/2018 -> dimanche 21/01/2018) : (export, daily_all, complete_day)."""
    jours = pd.date_range("2018-01-01", "2018-01-21", freq="D", name="date")
    daily_all = pd.DataFrame({g: 1.0 for g in G}, index=jours)   # 1 vente par jour et par groupe
    complete_day = pd.Series(True, index=jours)
    dimanches = pd.DatetimeIndex(["2018-01-07", "2018-01-14", "2018-01-21"], name="date")
    export = pd.DataFrame({g: 7.0 for g in G}, index=dimanches)  # 7 jours x 1 = 7 par semaine
    return export, daily_all, complete_day


def anomalies(journal):
    return [ligne["Contrôle"] for ligne in journal if ligne["Statut"] == "ANOMALIE"]


def test_export_propre_aucune_anomalie():
    export, daily_all, complete_day = donnees_hebdomadaires()
    journal = []
    weekly, ecarts = clean_weekly(export, None, daily_all, complete_day, journal)
    assert anomalies(journal) == []
    assert ecarts.empty
    assert len(weekly) == 3
    assert (weekly[G] == 7).all().all()                         # recalculé depuis les jours


def test_semaine_pas_datee_dun_dimanche():
    export, daily_all, complete_day = donnees_hebdomadaires()
    export = export.rename(index={pd.Timestamp("2018-01-14"): pd.Timestamp("2018-01-15")})  # un lundi
    journal = []
    clean_weekly(export, None, daily_all, complete_day, journal)
    assert "Semaines datées d'un dimanche" in anomalies(journal)


def test_semaine_manquante_detectee():
    export, daily_all, complete_day = donnees_hebdomadaires()
    journal = []
    clean_weekly(export.drop(pd.Timestamp("2018-01-14")), None, daily_all, complete_day, journal)
    assert "Semaines manquantes dans la suite" in anomalies(journal)


def test_ecart_avec_horaire_detecte():
    export, daily_all, complete_day = donnees_hebdomadaires()
    export.loc["2018-01-14", "N02BE"] = 10.0                   # au lieu de 7
    journal = []
    _, ecarts = clean_weekly(export, None, daily_all, complete_day, journal)
    assert len(ecarts) == 1
    assert ecarts.iloc[0]["Groupe"] == "N02BE"
    assert ecarts.iloc[0]["Écart"] == 3


def test_semaine_incomplete_exclue():
    export, daily_all, complete_day = donnees_hebdomadaires()
    complete_day[pd.Timestamp("2018-01-17")] = False            # un jour incomplet dans la 3e semaine
    journal = []
    weekly, _ = clean_weekly(export, None, daily_all, complete_day, journal)
    assert "Semaines incomplètes exclues" in anomalies(journal)
    assert pd.Timestamp("2018-01-21") not in weekly.index
    assert len(weekly) == 2


def test_vrais_exports():
    """Sur les exports du client : 300 semaines complètes, la première et la dernière exclues."""
    from pharma.cleaning import hourly, loading
    journal = []
    h = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    weekly, ecarts = clean_weekly(loading.load_export("weekly"), None, h.daily_all, h.complete_day, journal)
    assert len(weekly) == 300
    assert weekly.index.min() == pd.Timestamp("2014-01-12")
    assert weekly.index.max() == pd.Timestamp("2019-10-06")
    assert (weekly.index.dayofweek == 6).all()                 # toutes datées d'un dimanche
    assert ecarts.empty

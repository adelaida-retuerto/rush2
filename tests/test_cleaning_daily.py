"""Tests du nettoyage de l'export journalier (src/pharma/cleaning/daily.py).   [Ihman]

Lancer depuis la racine du projet :  python -m pytest tests/test_cleaning_daily.py
Principe : de petites données fabriquées où l'on connaît la bonne réponse, avec une erreur
glissée exprès qui doit être trouvée, puis un test sur les vrais exports.
"""
import sys
from pathlib import Path

# Rend le paquet pharma importable (src/) sans configuration commune
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from pharma import config  # noqa: E402
from pharma.cleaning.daily import HOUR_JOUR_COMPLET, clean_daily  # noqa: E402

G = config.GROUP_CODES


def donnees_journalieres(nb_jours=10):
    """Fabrique un export journalier cohérent : (export, colonnes dérivées, daily_all, complete_day)."""
    dates = pd.date_range("2018-01-01", periods=nb_jours, freq="D", name="date")
    export = pd.DataFrame({g: [float(i + 1) for i in range(nb_jours)] for g in G}, index=dates)
    derived = pd.DataFrame({
        "Year": dates.year, "Month": dates.month,
        "Hour": HOUR_JOUR_COMPLET, "Weekday Name": dates.day_name(),
    }, index=dates)
    daily_all = export.copy()                      # l'horaire recalculé donne les mêmes jours
    complete_day = pd.Series(True, index=dates)    # tous les jours complets
    return export, derived, daily_all, complete_day


def anomalies(journal):
    """Noms des contrôles en ANOMALIE dans le journal."""
    return [ligne["Contrôle"] for ligne in journal if ligne["Statut"] == "ANOMALIE"]


def test_export_propre_aucune_anomalie():
    export, derived, daily_all, complete_day = donnees_journalieres()
    journal = []
    daily, ecarts = clean_daily(export, derived, daily_all, complete_day, journal)
    assert anomalies(journal) == []
    assert ecarts.empty
    assert len(daily) == 10
    assert list(daily.columns) == G


def test_jour_manquant_detecte():
    export, derived, daily_all, complete_day = donnees_journalieres()
    jour = pd.Timestamp("2018-01-05")
    journal = []
    clean_daily(export.drop(jour), derived.drop(jour), daily_all, complete_day, journal)
    assert "Jours manquants dans la suite" in anomalies(journal)


def test_jour_de_semaine_faux_detecte():
    export, derived, daily_all, complete_day = donnees_journalieres()
    derived.loc["2018-01-03", "Weekday Name"] = "Sunday"   # le 03/01/2018 était un mercredi
    journal = []
    clean_daily(export, derived, daily_all, complete_day, journal)
    assert "Colonnes dérivées cohérentes avec la date" in anomalies(journal)


def test_colonne_hour_revele_un_jour_incomplet():
    export, derived, daily_all, complete_day = donnees_journalieres()
    derived.loc["2018-01-10", "Hour"] = sum(range(20))      # le jour s'arrête à 19h : 190
    journal = []
    clean_daily(export, derived, daily_all, complete_day, journal)
    assert "Jours incomplets selon la colonne Hour (≠ 276)" in anomalies(journal)


def test_jour_incomplet_exclu_des_ventes():
    export, derived, daily_all, complete_day = donnees_journalieres()
    complete_day[pd.Timestamp("2018-01-10")] = False        # l'horaire dit : jour incomplet
    journal = []
    daily, _ = clean_daily(export, derived, daily_all, complete_day, journal)
    assert pd.Timestamp("2018-01-10") not in daily.index
    assert len(daily) == 9


def test_ecart_avec_horaire_detecte():
    export, derived, daily_all, complete_day = donnees_journalieres()
    export.loc["2018-01-04", "R03"] += 12                    # l'export ne concorde plus avec l'horaire
    journal = []
    _, ecarts = clean_daily(export, derived, daily_all, complete_day, journal)
    assert len(ecarts) == 1
    assert ecarts.iloc[0]["Groupe"] == "R03"
    assert ecarts.iloc[0]["Écart"] == 12


def test_nouveau_code_atc_signale_avec_sa_famille():
    """Une colonne M01AC ajoutée par le logiciel de caisse est signalée, rangée dans les anti-inflammatoires."""
    export, derived, daily_all, complete_day = donnees_journalieres()
    derived["M01AC"] = 1.0
    journal = []
    clean_daily(export, derived, daily_all, complete_day, journal)
    ligne = [l for l in journal if l["Contrôle"] == "Nouveaux codes ATC dans l'export"][0]
    assert ligne["Statut"] == "ANOMALIE"
    assert "M01AC (Anti-inflammatoires)" in ligne["Détail"]


def test_vrais_exports():
    """Sur les exports du client : 2105 jours complets, aucun écart avec l'horaire."""
    from pharma.cleaning import hourly, loading
    journal = []
    h = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    daily, ecarts = clean_daily(loading.load_export("daily"), loading.load_derived_columns("daily"),
                                h.daily_all, h.complete_day, journal)
    assert len(daily) == 2105
    assert daily.index.max() == pd.Timestamp("2019-10-07")   # le 08/10/2019 (incomplet) est exclu
    assert ecarts.empty

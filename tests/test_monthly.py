import pandas as pd

from pharma.config import GROUP_CODES
from pharma.cleaning.monthly import clean_monthly


def test_recalcul_ecart_et_mois_incomplet():
    # Deux mois de ventes : une quantité par jour et par groupe
    dates = pd.date_range("2020-01-01", "2020-02-29", freq="D")
    daily_all = pd.DataFrame(1.0, index=dates, columns=GROUP_CODES)

    complete_day = pd.Series(True, index=dates)
    complete_day.loc[pd.Timestamp("2020-02-29")] = False

    export = daily_all.resample("ME").sum()
    export.loc[pd.Timestamp("2020-01-31"), "M01AB"] += 5

    journal = []
    monthly, ecarts = clean_monthly(
        export, None, daily_all, complete_day, journal
    )

    # Janvier est recalculé ; février est exclu
    assert monthly.index.tolist() == [pd.Timestamp("2020-01-31")]
    assert (monthly.loc["2020-01-31"] == 31).all()

    # L'erreur introduite dans l'export est détectée
    assert len(ecarts) == 1
    assert ecarts.iloc[0]["Groupe"] == "M01AB"
    assert ecarts.iloc[0]["Écart"] == 5

    # Le nettoyage ne modifie pas le tableau d'entrée
    assert export.loc["2020-01-31", "M01AB"] == 36
    assert any(
        ligne["Contrôle"] == "Mois incomplets exclus"
        and ligne["Statut"] == "ANOMALIE"
        for ligne in journal
    )
    
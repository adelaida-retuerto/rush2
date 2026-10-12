import pandas as pd

from pharma.config import GROUP_CODES
from pharma.analysis.forecast import evaluer_methodes


def test_prevision_sans_utiliser_les_ventes_futures():
    dates = pd.date_range("2020-01-01", periods=48, freq="MS")
    ventes = pd.DataFrame(10.0, index=dates, columns=GROUP_CODES)
    date_test = dates[-6]

    avant = evaluer_methodes(ventes, pd.DatetimeIndex([date_test]))

    # Modifier fortement le mois prévu et tous les mois suivants
    modifiees = ventes.copy()
    modifiees.loc[date_test:] = 9999.0

    apres = evaluer_methodes(
        modifiees, pd.DatetimeIndex([date_test])
    )

    # Les prévisions doivent rester identiques
    pd.testing.assert_series_equal(
        avant["Prévu"], apres["Prévu"]
    )

    assert len(avant) == 4 * 8
    assert (avant["Prévu"] == 10.0).all()

    # Les valeurs réelles changent bien, donc le test est significatif
    assert (apres["Réel"] == 9999.0).all()
    
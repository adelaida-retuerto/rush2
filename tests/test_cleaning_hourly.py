"""[Adelaida] Nettoyage de l'export horaire, la référence."""
import pandas as pd

from pharma.cleaning.hourly import clean_hourly
from helpers import fake_hourly


def test_dernier_jour_coupe_est_marque_incomplet():
    h = fake_hourly(days=10, drop_last_hours=5)
    res = clean_hourly(h, None, rows := [])
    assert not res.complete_day.iloc[-1] and res.complete_day.iloc[:-1].all()
    assert res.meta["last_day_partial"]


def test_heure_manquante_rend_le_jour_incomplet():
    h = fake_hourly(days=10).drop(pd.Timestamp("2018-01-05 14:00"))
    res = clean_hourly(h, None, rows := [])
    assert not res.complete_day[pd.Timestamp("2018-01-05")]
    assert any(r["Contrôle"].startswith("Heures manquantes") and r["Statut"] == "ANOMALIE" for r in rows)


def test_jour_recalcule_egal_somme_des_heures():
    h = fake_hourly(days=10)
    res = clean_hourly(h, None, [])
    pd.testing.assert_frame_equal(res.daily_all, h.resample("D").sum())

"""[Adelaida] Assemblage du nettoyage : les 4 exports ensemble, fichiers propres et rapport."""
import numpy as np
import pandas as pd
import pytest

from pharma import config
from pharma.cleaning import checks, loading, run
from helpers import write_exports

G = config.GROUP_CODES


def test_exports_coherents_aucun_ecart(tmp_path):
    write_exports(tmp_path / "raw")
    c = run.run_cleaning(tmp_path / "raw", tmp_path / "proc", tmp_path / "rep")
    assert c.discrepancies.empty


def test_export_mensuel_faux_ecarte(tmp_path):
    h = write_exports(tmp_path / "raw", monthly_bias=25)
    c = run.run_cleaning(tmp_path / "raw", tmp_path / "proc", tmp_path / "rep")
    assert len(c.discrepancies.query("Export == 'monthly'")) == 1
    assert c.sources.set_index("Source").loc["Mensuel", "Statut"] == "Écarté"
    assert c.monthly.iloc[0, 0] == h.resample("ME").sum().iloc[0, 0]


def test_jour_et_mois_incomplets_exclus(tmp_path):
    write_exports(tmp_path / "raw", days=70, drop_last_hours=5)
    c = run.run_cleaning(tmp_path / "raw", tmp_path / "proc", tmp_path / "rep")
    assert c.last_complete_month == pd.Timestamp("2018-02-28")
    assert pd.Timestamp("2018-03-11") not in c.daily.index


def test_fichiers_propres_relus_a_l_identique(tmp_path):
    write_exports(tmp_path / "raw")
    c = run.run_cleaning(tmp_path / "raw", tmp_path / "proc", tmp_path / "rep")
    for level, ref in [("daily", c.daily), ("monthly", c.monthly)]:
        back = run.load_processed(level, tmp_path / "proc")
        pd.testing.assert_frame_equal(back, ref, check_freq=False, check_names=False, atol=1e-3)
    assert (tmp_path / "rep" / "rapport_qualite.md").exists()


def test_export_mal_forme_refuse(tmp_path):
    write_exports(tmp_path / "raw")
    path = tmp_path / "raw" / config.EXPORTS["daily"]
    pd.read_csv(path).drop(columns=["N05B"]).to_csv(path, index=False)
    with pytest.raises(loading.ExportError):
        loading.load_export("daily", tmp_path / "raw")


def test_pics_conserves_mais_signales():
    idx = pd.date_range("2018-01-01", periods=120, freq="D")
    daily = pd.DataFrame(np.random.default_rng(1).normal(20, 2, size=(len(idx), len(G))), index=idx, columns=G)
    daily.iloc[60, 0] = 200
    out = checks.flag_outliers(daily)
    assert len(out) == 1 and out["Groupe"].iloc[0] == G[0]


def test_option_fin_analyse_jusqu_au_mois_demande(tmp_path):
    write_exports(tmp_path / "raw", days=70)                 # 01/01/2018 -> 11/03/2018
    c = run.run_cleaning(tmp_path / "raw", tmp_path / "proc", tmp_path / "rep", until="2018-01")
    assert c.last_complete_month == pd.Timestamp("2018-01-31")
    assert c.daily.index.max() == pd.Timestamp("2018-01-31")

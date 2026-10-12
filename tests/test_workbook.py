"""[Adelaida] Tests de la mise à jour du classeur : les 4 règles du modèle.

Ces tests utilisent les vrais exports, coupés pour simuler deux mois successifs de la mission.
Ils prennent environ une minute.
"""
import hashlib
import shutil

import pandas as pd
import pytest
from openpyxl import load_workbook
from openpyxl.utils import range_boundaries

from pharma import config, pipeline
from pharma.workbook import tables, template, verify


def _cut_exports(dest, last_date: str):
    """Copie les 4 exports en ne gardant que les données jusqu'à `last_date` (simule un export plus ancien)."""
    dest.mkdir(parents=True)
    fmt = {"hourly": "%m/%d/%Y %H:%M", "daily": "%m/%d/%Y", "weekly": "%m/%d/%Y", "monthly": "%Y-%m-%d"}
    for level, name in config.EXPORTS.items():
        df = pd.read_csv(config.RAW_DIR / name)
        dates = pd.to_datetime(df["datum"], format=fmt[level])
        df[dates <= pd.Timestamp(last_date)].to_csv(dest / name, index=False)


def _md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def deux_mois(tmp_path_factory):
    base = tmp_path_factory.mktemp("mission")
    tpl = template.build_template(base / "modele.xlsx")
    out = base / "deliverables"
    _cut_exports(base / "raw_aout", "2019-09-12 23:00")          # export reçu mi-septembre : dernier mois complet = août
    r1 = pipeline.run(offline=True, raw_dir=base / "raw_aout", output_dir=out, template_path=tpl)
    hash_aout = _md5(r1.workbook)
    r2 = pipeline.run(offline=True, raw_dir=config.RAW_DIR, output_dir=out, template_path=tpl)
    return tpl, r1, r2, hash_aout


def test_regle1_un_fichier_date_par_mois_et_l_ancien_archive_intact(deux_mois):
    tpl, r1, r2, hash_aout = deux_mois
    assert r1.workbook.name == "analyse_ventes_2019-08.xlsx"
    assert r2.workbook.name == "analyse_ventes_2019-09.xlsx"
    out = r2.workbook.parent
    archived = out / "archive" / "analyse_ventes_2019-08.xlsx"
    assert not r1.workbook.exists()                                  # deliverables/ : seulement le mois en vigueur
    assert archived.exists() and _md5(archived) == hash_aout         # le mois précédent est archivé, intact
    assert sorted(p.name for p in out.glob("*.xlsx")) == ["analyse_ventes_2019-09.xlsx"]


def test_regle2_seules_les_zones_declarees_changent(deux_mois):
    _, r1, r2, _ = deux_mois
    assert r1.checks.ok and r2.checks.ok
    noms = set(r2.checks.checks["Contrôle"])
    assert {"Présentation et formules inchangées", "Aucune zone écrasée par un tableau qui grandit"} <= noms


def test_regle3_les_tableaux_grandissent_et_les_formules_suivent(deux_mois):
    _, r1, r2, _ = deux_mois
    n = []
    archived_aout = r2.workbook.parent / "archive" / r1.workbook.name
    for path in (archived_aout, r2.workbook):
        wb = load_workbook(path)
        _, table = tables.tables(wb)["T_Jour"]
        c1, row1, c2, row2 = range_boundaries(table.ref)
        n.append(row2 - row1)
        assert wb["Outil"]["G10"].value == "=MIN(T_Jour[Date])"     # la formule pointe sur le tableau
        assert "T_Jour[N02BE]" in wb["Outil"]["D22"].value
    assert n[1] > n[0]                                             # septembre a plus de jours qu'août


def test_regle4_un_modele_abime_est_refuse(deux_mois, tmp_path):
    tpl, r1, r2, _ = deux_mois
    broken = tmp_path / "modele_abime.xlsx"
    shutil.copyfile(tpl, broken)
    wb = load_workbook(broken)
    wb["Outil"]["G10"] = "=MIN(Données_Jour!A2:A2000)"           # quelqu'un remet une plage fixe à la main
    wb.save(broken)
    rows = {name: 1 for name in template.contract()[0]}
    report = verify.check(broken, r2.workbook, rows, raise_on_error=False)
    assert not report.ok


def test_regle4_un_tableau_supprime_du_modele_arrete_la_mise_a_jour(tmp_path):
    tpl = template.build_template(tmp_path / "modele.xlsx")
    wb = load_workbook(tpl)
    ws = wb["Données_Jour"]
    del ws.tables["T_Jour"]
    wb.save(tpl)
    with pytest.raises(tables.TemplateError):
        tables.check_contract(load_workbook(tpl), *template.contract())


def test_archivage_ne_supprime_ni_n_ecrase_rien(tmp_path):
    from pharma.workbook.update import archive_previous
    out = tmp_path / "deliverables"
    (out / "archive").mkdir(parents=True)
    for name in ["analyse_ventes_2019-07.xlsx", "analyse_ventes_2019-08.xlsx", "analyse_ventes_2019-09.xlsx"]:
        (out / name).write_text(name)
    (out / "archive" / "analyse_ventes_2019-07.xlsx").write_text("déjà archivé")
    archive_previous(out, out / "analyse_ventes_2019-09.xlsx")
    assert [p.name for p in out.glob("*.xlsx")] == ["analyse_ventes_2019-09.xlsx"]
    archived = sorted(p.name for p in (out / "archive").glob("*.xlsx"))
    assert len(archived) == 3 and "analyse_ventes_2019-08.xlsx" in archived
    assert (out / "archive" / "analyse_ventes_2019-07.xlsx").read_text() == "déjà archivé"

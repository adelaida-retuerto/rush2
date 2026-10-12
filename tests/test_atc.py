"""Tests de la hiérarchie ATC (src/pharma/atc.py) : chaque code se range dans sa famille.   [Ihman]

Lancer depuis la racine du projet :  python -m pytest tests/test_atc.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from pharma import atc, config  # noqa: E402


@pytest.mark.parametrize("code, attendu", [
    ("M01AB", "Anti-inflammatoires"), ("M01AE", "Anti-inflammatoires"),
    ("N02BA", "Antalgiques"), ("N02BE", "Antalgiques"),
    ("N05B", "Psycholeptiques"), ("N05C", "Psycholeptiques"),
    ("R03", "Respiratoire"), ("R06", "Respiratoire"),
])
def test_les_8_groupes_suivis_sont_dans_leur_famille(code, attendu):
    assert atc.famille(code) == attendu


@pytest.mark.parametrize("code, attendu", [
    ("M01AC", "Anti-inflammatoires"),     # oxicams : nouveau code, préfixe M01 connu
    ("N02AA", "Antalgiques"),             # morphine : préfixe N02 connu
    ("R05CB", "Respiratoire"),            # mucolytiques : préfixe R connu
    ("n02be", "Antalgiques"),             # minuscules acceptées
])
def test_un_nouveau_code_rejoint_sa_famille(code, attendu):
    assert atc.famille(code) == attendu


def test_famille_inconnue_rangee_par_sa_premiere_lettre():
    assert atc.famille("A02BC") == "Autres · Système digestif et métabolisme"
    assert atc.famille("N06AB") == "Autres · Système nerveux"     # N06 (antidépresseurs) n'est pas une famille suivie


@pytest.mark.parametrize("texte", ["Year", "Hour", "Weekday Name", "datum", "N2BE", "X12", "Z99"])
def test_ce_qui_nest_pas_un_code_atc(texte):
    assert not atc.est_code_atc(texte)
    with pytest.raises(ValueError):
        atc.famille(texte)


def test_par_famille_additionne_et_range_un_nouveau_code():
    ventes = pd.DataFrame({"N02BA": [1, 2], "N02BE": [10, 20], "R03": [3, 3], "M01AC": [5, 5], "Year": [2019, 2019]})
    familles = atc.par_famille(ventes)
    assert set(familles.columns) == {"Antalgiques", "Respiratoire", "Anti-inflammatoires"}   # Year écarté
    assert list(familles["Antalgiques"]) == [11, 22]
    assert list(familles["Anti-inflammatoires"]) == [5, 5]


def test_codes_non_suivis():
    assert atc.codes_non_suivis(["Year", "Hour", "M01AC", "N02BE"]) == ["M01AC"]


def test_toutes_les_familles_de_config_sont_valides():
    for prefixe in config.FAMILLES_ATC:
        assert prefixe[0] in config.NIVEAU1_ATC

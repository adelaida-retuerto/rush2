"""Codes ATC : reconnaître un code et le ranger dans sa famille.   [Ihman]

Les tables (FAMILLES_ATC, NIVEAU1_ATC) sont dans config.py ; ce module contient la logique.
    est_code_atc("M01AC")   -> True
    famille("M01AC")        -> "Anti-inflammatoires"     (préfixe M01 connu)
    famille("A02BC")        -> "Autres · Système digestif et métabolisme"   (repli sur la 1re lettre)
"""
from __future__ import annotations

import re

import pandas as pd

from . import config

# Forme d'un code ATC : une lettre, deux chiffres, puis éventuellement une lettre, une lettre et deux chiffres
# (N02, N02B, N02BE, N02BE01). La lettre de tête doit être un des 14 groupes officiels.
_FORME_ATC = re.compile(r"^[A-Z]\d{2}(?:[A-Z](?:[A-Z](?:\d{2})?)?)?$")


def est_code_atc(code: str) -> bool:
    """Vrai si le texte a la forme d'un code ATC et commence par une lettre officielle."""
    code = str(code).strip().upper()
    return bool(_FORME_ATC.match(code)) and code[0] in config.NIVEAU1_ATC


def famille(code: str) -> str:
    """Famille d'un code ATC : le préfixe le plus long de FAMILLES_ATC qui correspond.

    Aucun préfixe connu : « Autres · » suivi du 1er niveau ATC (la lettre de tête).
    Pas un code ATC : erreur claire, plutôt qu'un classement faux.
    """
    code = str(code).strip().upper()
    if not est_code_atc(code):
        raise ValueError(f"« {code} » n'est pas un code ATC (ex. attendu : N02BE)")
    # On essaie les préfixes du plus long au plus court : N02BE, N02B, N02, N0, N
    for longueur in range(len(code), 0, -1):
        if code[:longueur] in config.FAMILLES_ATC:
            return config.FAMILLES_ATC[code[:longueur]]
    return f"Autres · {config.NIVEAU1_ATC[code[0]]}"


def table_des_groupes(codes: list[str] | None = None) -> pd.DataFrame:
    """Une ligne par code : code, libellé (si connu), famille, 1er niveau ATC. Par défaut, les groupes suivis."""
    codes = codes or config.GROUP_CODES
    return pd.DataFrame({
        "Groupe": codes,
        "Libellé": [config.GROUPS.get(c, "Nouveau code, libellé à ajouter dans config.GROUPS") for c in codes],
        "Famille": [famille(c) for c in codes],
        "Niveau 1 ATC": [config.NIVEAU1_ATC[c[0]] for c in codes],
    })


def par_famille(ventes: pd.DataFrame) -> pd.DataFrame:
    """Additionne les colonnes de groupes par famille (une colonne par famille, mêmes lignes).

    Toute colonne qui est un code ATC est rangée, y compris un code ajouté plus tard.
    """
    codes = [c for c in ventes.columns if est_code_atc(c)]
    familles = {c: famille(c) for c in codes}
    # groupby sur les colonnes : on transpose, on regroupe les lignes par famille, on retranspose
    return ventes[codes].T.groupby(familles).sum().T


def codes_non_suivis(colonnes) -> list[str]:
    """Colonnes d'un export qui ressemblent à un code ATC mais ne sont pas dans config.GROUPS."""
    return [c for c in colonnes if est_code_atc(c) and c not in config.GROUPS]

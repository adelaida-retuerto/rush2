"""Contrôle du classeur après la mise à jour (règle 4).   [Adelaida]

On compare le fichier produit au modèle : seules les zones déclarées (tableaux et cellules nommées)
ont le droit d'avoir changé. Tout le reste (titres, formules de l'outil, graphiques, listes déroulantes,
mises en forme conditionnelles) doit être identique. En cas d'écart, la mise à jour est refusée.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import range_boundaries

from . import tables


class ClasseurInvalide(RuntimeError):
    """Le classeur produit ne respecte pas le modèle : il ne doit pas être livré."""


@dataclass
class Report:
    checks: pd.DataFrame

    @property
    def ok(self) -> bool:
        return bool((self.checks["Statut"] == "OK").all())


def _in(ref: str, row: int, col: int) -> bool:
    c1, r1, c2, r2 = range_boundaries(ref)
    return c1 <= col <= c2 and r1 <= row <= r2


def check(template_path: Path, output_path: Path, expected_rows: dict[str, int], raise_on_error: bool = True) -> Report:
    tpl = load_workbook(template_path)
    out = load_workbook(output_path)
    rows: list[dict] = []

    def add(check_name, zone, ok, detail):
        rows.append({"Contrôle": check_name, "Zone": zone, "Statut": "OK" if ok else "ERREUR", "Détail": detail})

    # 1. Mêmes feuilles, même ordre
    add("Feuilles", "classeur", tpl.sheetnames == out.sheetnames, f"{len(out.sheetnames)} feuilles")

    # 2. Éléments de présentation conservés, feuille par feuille
    for ws_t in tpl.worksheets:
        ws_o = out[ws_t.title]
        for label, a, b in [("Graphiques", len(ws_t._charts), len(ws_o._charts)),
                            ("Listes déroulantes et contrôles de saisie",
                             len(ws_t.data_validations.dataValidation), len(ws_o.data_validations.dataValidation)),
                            ("Mises en forme conditionnelles", len(ws_t.conditional_formatting),
                             len(ws_o.conditional_formatting))]:
            if a or b:
                add(label, ws_t.title, a == b, f"modèle {a}, produit {b}")

    # 3. Tableaux : présents, mêmes colonnes, bon nombre de lignes, pas de chevauchement
    t_tpl, t_out = tables.tables(tpl), tables.tables(out)
    for name, n in expected_rows.items():
        if name not in t_out:
            add("Tableau présent", name, False, "absent du classeur produit")
            continue
        ws_o, tab = t_out[name]
        c1, r1, c2, r2 = range_boundaries(tab.ref)
        ws_t, tab_t = t_tpl[name]
        tc1, tr1, tc2, _ = range_boundaries(tab_t.ref)
        same_cols = [ws_o.cell(r1, c).value for c in range(c1, c2 + 1)] == \
                    [ws_t.cell(tr1, c).value for c in range(tc1, tc2 + 1)]
        got = r2 - r1
        add("Tableau rempli", name, same_cols and got == max(n, 1) and (c1, r1) == (tc1, tr1),
            f"{n} ligne(s) attendue(s), {got} dans le tableau ({tab.ref})")
    for name, (ws_a, ta) in t_out.items():
        for other, (ws_b, tb) in t_out.items():
            if name < other and ws_a.title == ws_b.title and tables._overlaps(ta.ref, tb.ref):
                add("Chevauchement de tableaux", f"{name} / {other}", False, f"{ta.ref} / {tb.ref}")

    # 4. Cellules nommées remplies
    for name, (sheet, coord) in tables.named_cells(out).items():
        v = out[sheet][coord].value
        add("Cellule nommée remplie", name, v not in (None, ""), f"{sheet}!{coord}")

    # 5. Rien d'autre n'a bougé : chaque cellule non vide du modèle hors zones déclarées est identique
    named = {(s, c) for s, c in tables.named_cells(tpl).values()}
    changed, overwritten = [], []
    for ws_t in tpl.worksheets:
        ws_o = out[ws_t.title]
        tpl_refs = [t.ref for w, t in t_tpl.values() if w.title == ws_t.title]
        out_refs = [t.ref for w, t in t_out.values() if w.title == ws_t.title]
        for row in ws_t.iter_rows():
            for cell in row:
                if cell.value is None or (ws_t.title, cell.coordinate) in named:
                    continue
                if any(_in(r, cell.row, cell.column) for r in tpl_refs):
                    continue
                if any(_in(r, cell.row, cell.column) for r in out_refs):
                    overwritten.append(f"{ws_t.title}!{cell.coordinate}")
                elif ws_o[cell.coordinate].value != cell.value:
                    changed.append(f"{ws_t.title}!{cell.coordinate}")
    add("Présentation et formules inchangées", "toutes les feuilles", not changed,
        f"{len(changed)} cellule(s) modifiée(s)" + (f" : {changed[:5]}" if changed else ""))
    add("Aucune zone écrasée par un tableau qui grandit", "toutes les feuilles", not overwritten,
        f"{len(overwritten)} cellule(s)" + (f" : {overwritten[:5]}" if overwritten else ""))

    report = Report(pd.DataFrame(rows))
    if raise_on_error and not report.ok:
        errors = report.checks[report.checks["Statut"] == "ERREUR"]
        raise ClasseurInvalide("Classeur non conforme au modèle :\n" + errors.to_string(index=False))
    return report

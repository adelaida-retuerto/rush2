"""Mise à jour mensuelle du classeur client.   [Adelaida : assemblage]

Règle 1 : on copie le MODÈLE vers un nouveau fichier daté (analyse_ventes_2019-09.xlsx) ;
          le fichier d'un autre mois n'est jamais ouvert ni modifié.
          Une fois le nouveau classeur contrôlé, celui du mois précédent est déplacé, intact,
          dans deliverables/archive/ : deliverables/ ne contient que le classeur en vigueur.
Règle 2 : chaque flux ne remplit que ses tableaux et cellules nommées (fill de chaque module).
Règle 3 : les formules et graphiques pointent sur les tableaux : rien à recalculer côté code.
Règle 4 : verify.check() contrôle le résultat et arrête tout en cas d'anomalie.
"""
from __future__ import annotations

import datetime as dt
import logging
import shutil
from pathlib import Path

from openpyxl import load_workbook

from .. import config
from . import tables, template, verify

log = logging.getLogger(__name__)


def output_path(c, output_dir: Path = config.OUTPUT_DIR) -> Path:
    return output_dir / config.OUTPUT_NAME.format(mois=f"{c.last_complete_month:%Y-%m}")


def archive_previous(output_dir: Path, current: Path) -> list[Path]:
    """Déplace les classeurs des mois précédents dans output_dir/archive/, sans les modifier.

    Ne supprime et n'écrase jamais rien : si un fichier du même nom est déjà archivé, la copie
    reçoit l'heure du déplacement dans son nom.
    """
    archive_dir = output_dir / config.ARCHIVE_SUBDIR
    moved = []
    pattern = config.OUTPUT_NAME.format(mois="*")
    for old in sorted(output_dir.glob(pattern)):
        if old.name == current.name:
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / old.name
        if target.exists():
            target = archive_dir / f"{old.stem}_{dt.datetime.now():%Y%m%d-%H%M%S}{old.suffix}"
        shutil.move(str(old), str(target))
        log.info("Archivé : %s -> %s", old.name, target.relative_to(output_dir))
        moved.append(target)
    return moved


def update_workbook(c, t, template_path: Path = config.TEMPLATE_PATH, output_dir: Path = config.OUTPUT_DIR,
                    flux: list[str] = template.ALL_FLUX, out: Path | None = None) -> tuple[Path, "verify.Report"]:
    if not template_path.exists():
        raise tables.TemplateError(f"Modèle absent : {template_path}. Lancez d'abord scripts/build_template.py")
    publish = out is None                                    # livraison réelle (pas un aperçu)
    out = out or output_path(c, output_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_name(f"~en_cours_{out.name}")            # brouillon : rien n'est livré avant le contrôle
    shutil.copyfile(template_path, work)                     # règle 1 : toujours repartir du modèle

    wb = load_workbook(work)
    tables.check_contract(wb, *template.contract(flux))       # le modèle a-t-il gardé toutes ses zones ?
    expected_rows: dict[str, int] = {}
    for module in template.modules(flux):
        expected_rows.update(module.fill(wb, c, t))          # règle 2 : chacune remplit ses zones
    wb.calculation.fullCalcOnLoad = True                     # Excel recalcule l'outil à l'ouverture
    wb.save(work)

    try:
        report = verify.check(template_path, work, expected_rows)  # règle 4 : bloque si anomalie
    except Exception:
        work.unlink(missing_ok=True)                         # le classeur en vigueur reste en place
        raise
    if publish:
        archive_previous(output_dir, out)                   # l'ancien mois part dans archive/, intact
    work.replace(out)                                        # même mois relancé : remplacé par la nouvelle version
    log.info("Classeur livré : %s", out)
    return out, report

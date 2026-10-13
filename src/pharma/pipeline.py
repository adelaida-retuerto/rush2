"""Enchaîne les trois couches : cleaning -> analysis -> workbook.   [Adelaida : assemblage]

Chaque bloc a sa propre fonction d'analyse, qui n'importe QUE ses modules (imports à
l'intérieur de la fonction). Ainsi `python scripts/preview.py sales` fonctionne même si le code
des autres blocs n'est pas encore dans le dépôt : personne n'attend personne.

    analyse_sales     Iman      statistiques descriptives, grippe, outil
    analyse_data      Adelaida  profils jour / heure, confidentialité
    analyse_forecast  Jeanne    prévision, valeur, synthèse
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from . import config
from .cleaning import run as cleaning_run

log = logging.getLogger(__name__)


@dataclass
class Results:
    clean: cleaning_run.CleanData
    tables: dict
    workbook: Path
    checks: object


def base_tables(c: cleaning_run.CleanData, n_monthly_rows: int) -> dict:
    """Informations communes issues du nettoyage, utilisées par plusieurs flux."""
    return {"n_bad_months": int(c.discrepancies.query("Export == 'monthly'")["Période"].nunique())
            if len(c.discrepancies) else 0, "n_monthly_rows": n_monthly_rows}


# ------------------------------------------------------------------------------------- flux Iman
def analyse_sales(c, offline: bool = False) -> dict:
    from .analysis import descriptive, environment
    t = {"group_volumes": descriptive.group_volumes(c), "year_to_date": descriptive.year_to_date(c),
         "yearly": descriptive.yearly(c), "seasonality": descriptive.seasonality_index(c), "peaks": descriptive.peak_months(c),
         "monthly": descriptive.monthly_table(c)}
    flu, flu_source = environment.load_flu(offline=offline)
    t["flu_effect"], t["flu_series"] = environment.flu_effect(c.weekly, flu)
    t["ladder"] = environment.link_ladder(t["flu_effect"])
    t["flu_source"] = f"Source : {flu_source}. Semaines ISO alignées sur la semaine lundi-dimanche des ventes."
    t["flu_note"] = (f"{t['flu_effect'].attrs['n_weeks']} semaines complètes. Modèle : ventes hebdo = effet du mois + "
                     f"effet grippe. « Forte grippe » = incidence ≥ {t['flu_effect'].attrs['threshold']:.0f} cas pour "
                     "100 000 (15 % des semaines les plus hautes). S-1 = incidence de la semaine précédente.")
    t["tool_note"] = (f"Dernier jour exporté : {c.meta['last_day']:%d/%m/%Y}"
                      + (f", incomplet (export arrêté à {c.meta['last_hour']}h)." if c.meta["last_day_partial"] else "."))
    return t


# --------------------------------------------------------------------------------- flux Adelaida
def analyse_data(c) -> dict:
    from .analysis import privacy, profiles
    t = {"weekday": profiles.weekday_index(c), "hourly": profiles.hourly_share(c),
         "heatmap": profiles.weekday_hour_heatmap(c), "privacy": privacy.small_counts(c)}
    t["compliance"] = privacy.compliance_chain(c, t["privacy"])
    t["run_info"] = f"Mis à jour le {dt.datetime.now():%d/%m/%Y %H:%M} ; dernier mois complet {c.last_complete_month:%m/%Y}."
    return t


# ----------------------------------------------------------------------------------- flux Jeanne
def analyse_forecast(c, base: dict) -> dict:
    from .analysis import forecast, summary
    t = {}
    t["fc_detail"], t["fc_summary"] = forecast.backtest(c.monthly)
    t["fc_next"] = forecast.previsions_recommandees(
        c.monthly, t["fc_detail"], t["fc_summary"]
    )
    t["value"] = forecast.business_value(t["fc_summary"])
    t["regularity"] = forecast.demand_regularity(c)
    s = t["fc_summary"].attrs
    t["fc_note"] = (
        f"Validation glissante sur {s['n_test']} mois "
        f"({s['test_start']:%m/%Y} à {s['test_end']:%m/%Y}), "
        "après sélection sur les 12 mois précédents. "
        "Chaque prévision utilise uniquement les ventes antérieures. "
        "Cinq méthodes comparées, dont Holt-Winters et une moyenne "
        "saisonnière sur deux ans. Analyse exploratoire ; "
        "fourchettes indicatives sans garantie de couverture. "
        "Repli vers la référence si le modèle sélectionné "
        "dégrade la MAE en validation."
    )
    t["verdict"] = summary.verdict_table(t)
    return t


def synthese(c, t: dict) -> dict:
    """Contenu de la Synthèse, qui croise les trois flux : chiffres clés, insights, recommandations,
    limites. Rempli à l'intégration ; tant qu'un flux manque, la feuille affiche « en attente »."""
    from .analysis import summary
    needed = {"group_volumes", "peaks", "weekday", "hourly", "flu_effect", "privacy", "value", "year_to_date"}
    out = {"subtitle": (f"8 groupes ATC - {config.UNIT_LABEL} - données jusqu'au {c.daily.index.max():%d/%m/%Y}, "
                        f"mis à jour le {dt.date.today():%d/%m/%Y}."),
           "limits": summary.limits(c)}
    if needed <= set(t):
        out["kpi"] = summary.kpis(c, t)
        out["insights"] = summary.insights(c, t)
        out["recommendations"] = summary.recommendations(c, t)
        out["message"] = summary.key_message(c, t)
    return out


def analyse(c: cleaning_run.CleanData, n_monthly_rows: int, offline: bool = False) -> dict:
    """Couche 2 complète : les trois flux, puis la synthèse."""
    t = base_tables(c, n_monthly_rows)
    t.update(analyse_sales(c, offline))
    t.update(analyse_data(c))
    t.update(analyse_forecast(c, t))
    t.update(synthese(c, t))
    return t


def run(offline: bool = False, raw_dir: Path = config.RAW_DIR, output_dir: Path = config.OUTPUT_DIR,
        template_path: Path = config.TEMPLATE_PATH, until: str | None = None) -> Results:
    from .workbook import update
    c = cleaning_run.run_cleaning(raw_dir, until=until)                          # couche 1
    t = analyse(c, c.meta["n_monthly_rows"], offline)                             # couche 2
    path, report = update.update_workbook(c, t, template_path, output_dir)        # couche 3
    report.checks.to_csv(config.QUALITY_REPORT_DIR / "controle_classeur.csv", index=False)
    return Results(clean=c, tables=t, workbook=path, checks=report)

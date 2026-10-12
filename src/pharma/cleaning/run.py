"""Couche 1 : assemble le nettoyage des 4 exports et écrit les tables propres.   [Adelaida]

Lancer seul :  python scripts/clean_data.py

Entrées  : data/raw/Pharma_Ventes_{Hourly,Daily,Weekly,Monthly}.csv  (jamais modifiés)
Sorties  : data/processed/ventes_{heure,jour,semaine,mois}.csv        (données propres)
           reports/quality/*.csv + rapport_qualite.md                  (traçabilité)

Règles de nettoyage (toutes tracées dans le journal) :
  1. Source de référence = export horaire ; jour, semaine et mois sont recalculés depuis lui.
  2. Les exports journalier, hebdomadaire et mensuel servent de contrôle ; un export en écart est écarté.
  3. Les jours, semaines (lundi -> dimanche) et mois incomplets sont exclus des tables propres.
  4. Les colonnes dérivées du logiciel (Year, Month, Hour, Weekday Name) sont ignorées.
  5. Les pics inhabituels sont signalés mais conservés : rien ne prouve une erreur de saisie.
  6. Aucune valeur n'est inventée ni corrigée à la main.
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

from dataclasses import dataclass, field

import pandas as pd

from .. import config
from . import checks, loading
from .daily import clean_daily
from .hourly import clean_hourly
from .monthly import clean_monthly
from .weekly import clean_weekly

log = logging.getLogger(__name__)
G = config.GROUP_CODES

@dataclass
class CleanData:
    """Tout ce que les analyses utilisent : tables propres + traçabilité du nettoyage."""
    hourly: pd.DataFrame                 # référence, index horaire
    daily: pd.DataFrame                  # jours complets, recalculés depuis l'horaire
    daily_all: pd.DataFrame              # tous les jours, y compris partiels
    weekly: pd.DataFrame                 # semaines complètes (lundi -> dimanche)
    monthly: pd.DataFrame                # mois complets
    last_complete_month: pd.Timestamp
    journal: pd.DataFrame                # un contrôle par ligne
    discrepancies: pd.DataFrame          # écarts export vs recalcul, par période et groupe
    outliers: pd.DataFrame               # pics signalés (non corrigés)
    sources: pd.DataFrame                # quelle source pour quel usage
    meta: dict = field(default_factory=dict)


def audit(exports: dict[str, pd.DataFrame], derived: dict[str, pd.DataFrame] | None = None) -> CleanData:
    """Lance les 4 nettoyages : l'horaire d'abord (référence), puis chaque export est comparé à lui."""
    derived = derived or {}
    rows: list[dict] = []
    ref = clean_hourly(exports["hourly"], derived.get("hourly"), rows)
    daily, d_disc = clean_daily(exports["daily"], derived.get("daily"), ref.daily_all, ref.complete_day, rows)
    weekly, w_disc = clean_weekly(exports["weekly"], derived.get("weekly"), ref.daily_all, ref.complete_day, rows)
    monthly, m_disc = clean_monthly(exports["monthly"], derived.get("monthly"), ref.daily_all, ref.complete_day, rows)
    discrepancies = pd.concat([d_disc, w_disc, m_disc], ignore_index=True)

    outliers = checks.flag_outliers(daily)
    checks.log(rows, "Pics journaliers (z robuste > %g)" % config.OUTLIER_Z, "daily", True,
               f"{len(outliers)} pic(s) signalé(s), détail ci-dessous", "Conservés : rien ne prouve une erreur de saisie")

    monthly_rejected = bool(len(m_disc))
    sources = pd.DataFrame([
        ["Horaire", "Source de référence : profils horaires, outil client, recalcul de tous les niveaux", "Retenu"],
        ["Journalier", "Contrôle de cohérence uniquement (identique à l'horaire si OK)", "Contrôle"],
        ["Hebdomadaire", "Contrôle de cohérence uniquement", "Contrôle"],
        ["Mensuel", "Écarté si écarts : mois recalculés depuis l'horaire", "Écarté" if monthly_rejected else "Contrôle"],
        ["Sentinelles (externe)", "Incidence hebdomadaire des syndromes grippaux, France", "Ajouté"],
    ], columns=["Source", "Usage", "Statut"])

    return CleanData(hourly=ref.hourly, daily=daily, daily_all=ref.daily_all, weekly=weekly, monthly=monthly,
                     last_complete_month=monthly.index.max(), journal=pd.DataFrame(rows, columns=checks.JOURNAL_COLUMNS),
                     discrepancies=discrepancies, outliers=outliers, sources=sources, meta=ref.meta)


PROCESSED_FILES = {
    "hourly": "ventes_heure.csv",
    "daily": "ventes_jour.csv",
    "weekly": "ventes_semaine.csv",
    "monthly": "ventes_mois.csv",
}


def _with_calendar(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Ajoute les colonnes de calendrier utiles aux autres flux, recalculées depuis la date."""
    out = df[G].round(4).copy()
    out.insert(0, "date", out.index)
    if level == "hourly":
        out.insert(1, "jour", out.index.strftime("%Y-%m-%d"))
        out.insert(2, "heure", out.index.hour)
        out.insert(3, "jour_semaine", out.index.dayofweek + 1)  # 1 = lundi
    elif level == "daily":
        out.insert(1, "jour_semaine", out.index.dayofweek + 1)
        out.insert(2, "mois", out.index.month)
        out.insert(3, "annee", out.index.year)
    elif level == "weekly":
        out.insert(1, "debut_semaine", out.index - pd.Timedelta(days=6))
        out = out.rename(columns={"date": "fin_semaine"})
    elif level == "monthly":
        out["date"] = out.index.to_period("M").astype(str)
        out = out.rename(columns={"date": "mois"})
        out.insert(1, "nb_jours", out.index.days_in_month)
    out["total"] = df[G].sum(axis=1).round(4)
    return out.reset_index(drop=True)


def _markdown_report(c: CleanData, exports: dict[str, pd.DataFrame]) -> str:
    j = c.journal
    n_anom = int((j["Statut"] == "ANOMALIE").sum())
    disc = c.discrepancies
    lines = [
        "# Rapport de qualité des données",
        "",
        f"Généré le {dt.datetime.now():%d/%m/%Y %H:%M} par `pharma.cleaning.run`.",
        "",
        "## Résumé",
        "",
        f"- Exports lus : " + ", ".join(f"{config.EXPORTS[k]} ({len(v)} lignes)" for k, v in exports.items()),
        f"- Contrôles : {len(j)}, dont {n_anom} anomalie(s)",
        f"- Jours complets retenus : {len(c.daily)} "
        f"(du {c.daily.index.min():%d/%m/%Y} au {c.daily.index.max():%d/%m/%Y})",
        f"- Dernier mois complet : {c.last_complete_month:%m/%Y}",
        f"- Cellules en écart entre exports et horaire : {len(disc)}",
        f"- Pics journaliers signalés (conservés) : {len(c.outliers)}",
        "",
        "## Quel export pour quel usage",
        "",
        c.sources.to_markdown(index=False),
        "",
        "## Journal des contrôles",
        "",
        j.to_markdown(index=False),
        "",
    ]
    if len(disc):
        by_month = (disc[disc["Export"] == "monthly"].groupby("Période")["Écart"].sum()
                    .sort_values(ascending=False).head(10).round(1))
        lines += ["## Les 10 plus gros écarts de l'export mensuel", "",
                  by_month.rename("Écart total (unités)").to_frame().to_markdown(), ""]
    lines += ["## Fichiers produits", "",
              "| Fichier | Contenu |", "| --- | --- |",
              "| `data/processed/ventes_heure.csv` | Ventes horaires (référence), tous les jours |",
              "| `data/processed/ventes_jour.csv` | Jours complets uniquement |",
              "| `data/processed/ventes_semaine.csv` | Semaines complètes, lundi -> dimanche |",
              "| `data/processed/ventes_mois.csv` | Mois complets, recalculés depuis l'horaire |",
              "| `reports/quality/journal_controles.csv` | Un contrôle par ligne |",
              "| `reports/quality/ecarts_exports.csv` | Chaque cellule en écart avec l'horaire |",
              "| `reports/quality/pics_signales.csv` | Pics inhabituels, conservés |", ""]
    return "\n".join(lines)


def cut_at(frames: dict[str, pd.DataFrame], until: str) -> dict[str, pd.DataFrame]:
    """Garde seulement les données jusqu'à la fin du mois `until` (AAAA-MM), comme un export plus ancien."""
    end = pd.Period(until, freq="M").end_time
    return {level: df[df.index <= end] for level, df in frames.items()}


def run_cleaning(raw_dir: Path = config.RAW_DIR,
                 processed_dir: Path = config.PROCESSED_DIR,
                 report_dir: Path = config.QUALITY_REPORT_DIR,
                 write: bool = True, until: str | None = None) -> CleanData:
    """Lit, contrôle, recalcule ; écrit les tables propres et le rapport si `write`.

    until = "AAAA-MM" (option --fin) : analyse l'historique jusqu'à la fin de ce mois seulement,
    pour refaire le classeur d'un mois passé. Le début de l'historique est toujours conservé.
    """
    log.info("Lecture des exports dans %s", raw_dir)
    exports = loading.load_all(raw_dir)
    derived = loading.load_all_derived(raw_dir)
    if until:
        exports, derived = cut_at(exports, until), cut_at(derived, until)
        log.info("Analyse limitée aux données jusqu'à fin %s", until)
    c = audit(exports, derived)
    c.meta["n_monthly_rows"] = len(exports["monthly"])
    if until and f"{c.last_complete_month:%Y-%m}" != until:
        log.warning("Le mois %s n'est pas complet dans les exports : dernier mois complet %s",
                    until, f"{c.last_complete_month:%Y-%m}")
    log.info("%d contrôles, %d anomalie(s) ; dernier mois complet %s",
             len(c.journal), int((c.journal["Statut"] == "ANOMALIE").sum()),
             f"{c.last_complete_month:%m/%Y}")
    if not write:
        return c

    processed_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    tables = {"hourly": c.hourly[c.hourly.index.normalize().isin(c.daily_all.index)],
              "daily": c.daily, "weekly": c.weekly, "monthly": c.monthly}
    for level, df in tables.items():
        path = processed_dir / PROCESSED_FILES[level]
        _with_calendar(df, level).to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S"
                                         if level == "hourly" else "%Y-%m-%d")
        log.info("Écrit %s (%d lignes)", path.relative_to(config.ROOT) if path.is_relative_to(config.ROOT)
                 else path, len(df))

    c.journal.to_csv(report_dir / "journal_controles.csv", index=False)
    c.discrepancies.to_csv(report_dir / "ecarts_exports.csv", index=False)
    c.outliers.to_csv(report_dir / "pics_signales.csv", index=False)
    (report_dir / "rapport_qualite.md").write_text(_markdown_report(c, exports), encoding="utf-8")
    log.info("Rapport : %s", report_dir / "rapport_qualite.md")
    return c


def load_processed(level: str, processed_dir: Path = config.PROCESSED_DIR) -> pd.DataFrame:
    """Pour les autres flux : relit une table propre, indexée par date, colonnes = groupes ATC."""
    path = processed_dir / PROCESSED_FILES[level]
    if not path.exists():
        raise FileNotFoundError(f"{path} absent : lancez d'abord `python scripts/clean_data.py`")
    df = pd.read_csv(path)
    key = {"hourly": "date", "daily": "date", "weekly": "fin_semaine", "monthly": "mois"}[level]
    idx = pd.to_datetime(df[key])
    if level == "monthly":
        idx = idx + pd.offsets.MonthEnd(0)
    return df[G].set_index(idx.rename("date"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Nettoyage et contrôle qualité des exports de la pharmacie")
    parser.add_argument("--raw-dir", type=Path, default=config.RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=config.PROCESSED_DIR)
    parser.add_argument("--report-dir", type=Path, default=config.QUALITY_REPORT_DIR)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    c = run_cleaning(args.raw_dir, args.processed_dir, args.report_dir)
    anomalies = c.journal[c.journal["Statut"] == "ANOMALIE"]
    print(f"\nNettoyage terminé : {len(c.journal)} contrôles, {len(anomalies)} anomalie(s).")
    for _, r in anomalies.iterrows():
        print(f" ! [{r['Export']}] {r['Contrôle']} : {r['Détail']} -> {r['Décision']}")


if __name__ == "__main__":
    main()

"""Chargement des 4 exports bruts. Aucune correction ici : on lit, on type, on vérifie le schéma."""
from __future__ import annotations

import pandas as pd

from .. import config

# Formats de date observés dans les exports (format US mois/jour/année)
_DATE_FORMATS = {
    "hourly": "%m/%d/%Y %H:%M",
    "daily": "%m/%d/%Y",
    "weekly": "%m/%d/%Y",
    "monthly": "%Y-%m-%d",
}


class ExportError(ValueError):
    """Export illisible ou schéma inattendu : on arrête plutôt que de produire des chiffres faux."""


def _parse_dates(series: pd.Series, level: str) -> pd.Series:
    try:
        return pd.to_datetime(series, format=_DATE_FORMATS[level])
    except (ValueError, TypeError):
        # Format changé par le logiciel : on tente une lecture souple, puis on refuse les trous
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.isna().any():
            bad = series[parsed.isna()].head(3).tolist()
            raise ExportError(f"Dates illisibles dans l'export {level} : {bad}")
        return parsed


def load_export(level: str, raw_dir=config.RAW_DIR) -> pd.DataFrame:
    """Lit un export et renvoie un DataFrame indexé par date, colonnes = groupes ATC."""
    path = raw_dir / config.EXPORTS[level]
    if not path.exists():
        raise ExportError(f"Export manquant : {path}")
    df = pd.read_csv(path)
    missing = [c for c in ["datum", *config.GROUP_CODES] if c not in df.columns]
    if missing:
        raise ExportError(f"Colonnes manquantes dans {path.name} : {missing}")
    df["date"] = _parse_dates(df["datum"], level)
    values = df[config.GROUP_CODES].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        raise ExportError(f"Valeurs non numériques dans {path.name}")
    out = values.set_index(df["date"]).sort_index()
    out.index.name = "date"
    out.attrs["source_file"] = path.name
    out.attrs["extra_columns"] = [c for c in df.columns if c not in ["datum", "date", *config.GROUP_CODES]]
    return out


def load_all(raw_dir=config.RAW_DIR) -> dict[str, pd.DataFrame]:
    return {level: load_export(level, raw_dir) for level in config.EXPORTS}


def load_derived_columns(level: str, raw_dir=config.RAW_DIR) -> pd.DataFrame:
    """Colonnes ajoutées par le logiciel (Year, Month, Hour, Weekday Name...), indexées par date.

    Elles ne servent pas à l'analyse (on les recalcule depuis la date), mais l'audit vérifie
    qu'elles sont cohérentes avec la date : une incohérence révélerait un export corrompu.
    """
    path = raw_dir / config.EXPORTS[level]
    df = pd.read_csv(path)
    extra = [c for c in df.columns if c not in ["datum", *config.GROUP_CODES]]
    out = df[extra].copy()
    out.index = _parse_dates(df["datum"], level)
    out.index.name = "date"
    return out


def load_all_derived(raw_dir=config.RAW_DIR) -> dict[str, pd.DataFrame]:
    return {level: load_derived_columns(level, raw_dir) for level in config.EXPORTS}

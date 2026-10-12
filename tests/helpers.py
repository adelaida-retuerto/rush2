"""Faux exports pour les tests : mêmes colonnes et formats de date que le logiciel de caisse."""
from pathlib import Path

import numpy as np
import pandas as pd

from pharma import config

G = config.GROUP_CODES


def fake_hourly(days: int = 70, drop_last_hours: int = 0, start: str = "2018-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=days * 24, freq="h")
    if drop_last_hours:
        idx = idx[:-drop_last_hours]
    rng = np.random.default_rng(0)
    return pd.DataFrame(rng.poisson(1, size=(len(idx), len(G))).astype(float), index=idx, columns=G)


def write_exports(folder: Path, days: int = 70, monthly_bias: float = 0.0, drop_last_hours: int = 0) -> pd.DataFrame:
    """Écrit 4 exports cohérents entre eux (sauf biais mensuel volontaire) et renvoie l'horaire."""
    h = fake_hourly(days, drop_last_hours)
    d = h.resample("D").sum()
    w = d.resample("W-SUN").sum()
    m = d.resample("ME").sum()
    m.iloc[0, 0] += monthly_bias
    folder.mkdir(parents=True, exist_ok=True)
    h.assign(datum=h.index.strftime("%-m/%-d/%Y %-H:%M"), Hour=h.index.hour)[["datum", *G, "Hour"]] \
        .to_csv(folder / config.EXPORTS["hourly"], index=False)
    d.assign(datum=d.index.strftime("%-m/%-d/%Y"))[["datum", *G]].to_csv(folder / config.EXPORTS["daily"], index=False)
    w.assign(datum=w.index.strftime("%-m/%-d/%Y"))[["datum", *G]].to_csv(folder / config.EXPORTS["weekly"], index=False)
    m.assign(datum=m.index.strftime("%Y-%m-%d"))[["datum", *G]].to_csv(folder / config.EXPORTS["monthly"], index=False)
    return h

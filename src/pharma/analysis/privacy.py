"""[Adelaida] Risque de ré-identification et conformité selon le niveau de détail partagé.

Idée : plus le comptage d'une cellule est petit (1, 2 ventes dans une heure), plus une
personne qui connaît la pharmacie (voisin, employé, proche) peut relier une vente à
un individu qu'elle a vu entrer. On mesure la part de cellules "petites" par niveau.
"""
from __future__ import annotations

import pandas as pd

from .. import config
from ..cleaning.run import CleanData

G = config.GROUP_CODES


def small_counts(c: CleanData) -> pd.DataFrame:
    levels = {"Heure": c.hourly, "Jour": c.daily, "Semaine": c.weekly, "Mois": c.monthly}
    thr = config.SMALL_COUNT_THRESHOLD
    rows = []
    for level, df in levels.items():
        for g in G:
            x = df[g]
            nz = x[x > 0]
            rows.append({
                "Niveau": level, "Groupe": g,
                "Sensible (art. 9 RGPD)": "Oui" if g in config.SENSITIVE_GROUPS else "Non",
                "Cellules avec vente": int(len(nz)),
                f"Dont ≤ {thr} unités": int((nz <= thr).sum()),
                f"Part ≤ {thr} unités": float((nz <= thr).mean()) if len(nz) else 0.0,
                "Médiane des cellules non nulles": float(nz.median()) if len(nz) else 0.0,
            })
    return pd.DataFrame(rows)


def compliance_chain(c: CleanData, counts: pd.DataFrame) -> pd.DataFrame:
    """Du constat à la décision : fait, règle, conséquence, actions (9 lignes)."""
    pv = counts.set_index(["Niveau", "Groupe"])
    h05c = pv.loc[("Heure", "N05C")]
    m05c_min = c.monthly["N05C"].min()
    thr = config.SMALL_COUNT_THRESHOLD
    return pd.DataFrame([
        ["Fait mesuré", f"{h05c[f'Part ≤ {thr} unités']:.0%} des heures avec un hypnotique vendu comptent ≤ {thr} unités ; "
                        f"au mensuel, minimum {m05c_min:.0f} unités"],
        ["Règle", "Données rattachables à une personne par recoupement : non anonymes (RGPD, considérant 26) ; "
                  "données concernant la santé (art. 9) ; secret professionnel du pharmacien"],
        ["Conséquence", "Le transfert de l'export brut n'entre dans aucune exception de l'art. 9 ; la pharmacie, "
                        "responsable de traitement, en porterait le risque"],
        ["Au-delà du RGPD", "Encadrement des avantages consentis par l'industrie, indépendance professionnelle, "
                            "pouvoir de négociation du laboratoire, réputation"],
        ["Action 1", "Refuser la transmission de l'export horaire ou journalier"],
        ["Action 2", "Si négociation : totaux mensuels uniquement, sans N05B ni N05C"],
        ["Action 3", "Contrat écrit : finalité limitée, interdiction de ré-identifier et de revendre"],
        ["Action 4", "Avis d'un juriste ou de l'Ordre sur la contrepartie avant signature"],
        ["Action 5", "Décision écrite du titulaire, consignée au registre des traitements"],
    ], columns=["Étape", "Contenu"])

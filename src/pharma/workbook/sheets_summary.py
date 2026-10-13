"""Remplissage des feuilles de synthèse et cadrage — Jeanne."""

from ..analysis import summary
from . import tables as X

SHEETS = ["Synthèse", "Cadrage", "Prévision"]

TABLES = [
    "T_Messages", "T_Chiffres_Cles", "T_Verdict", "T_Besoins",
    "T_Criteres", "T_Limites", "T_Decisions", "T_Risques", "T_Prevision", "T_Valeur", "T_Regularite", "T_Detail_Backtest", "T_Backtest"
]

NAMES = ["txt_sous_titre", "txt_prevision_note"]


def fill(wb, c, t):
    contenus = {
        "T_Messages": summary.key_messages(c, t),
        "T_Chiffres_Cles": summary.kpis(c, t),
        "T_Verdict": t["verdict"],
        "T_Besoins": t["needs"],
        "T_Criteres": summary.success_criteria(c, t),
        "T_Limites": t["limits"],
        "T_Decisions": t["decisions"],
        "T_Risques": t["risks"]
    }

    lignes = {
        nom: X.fill_table(wb, nom, contenu)
        for nom, contenu in contenus.items()
    }

    X.set_named(
        wb, "txt_sous_titre",
        f"Analyse de {len(c.monthly)} mois complets ; "
        f"dernier mois complet : {c.last_complete_month:%m/%Y}."
    )
    X.set_named(wb, "txt_prevision_note", t["fc_note"])

    lignes.update(fill_prevision(wb, t))
    lignes.update(fill_detail_backtest(wb, t))
    lignes.update(fill_backtest(wb, t))
    return lignes

def fill_prevision(wb, t):
    import pandas as pd

    verdicts = t["value"].set_index("Groupe")["Verdict : prévisible ?"]

    previsions = pd.DataFrame({
        "Groupe": t["fc_next"]["Groupe"],
        "Mois prévu": t["fc_next"]["Date"].dt.strftime("%Y-%m"),
        "Méthode retenue": t["fc_next"]["Méthode"],
        "Prévision": t["fc_next"]["Quantité prévue"],
        "Fourchette basse (80 %)": None,
        "Fourchette haute (80 %)": None,
        "Verdict": t["fc_next"]["Groupe"].map(verdicts)
    })

    return {
        "T_Prevision": X.fill_table(wb, "T_Prevision", previsions),
        "T_Valeur": X.fill_table(wb, "T_Valeur", t["value"]),
        "T_Regularite": X.fill_table(wb, "T_Regularite", t["regularity"])
    }

def fill_detail_backtest(wb, t):
    detail = t["fc_detail"].copy()

    detail["Date"] = detail["Date"].dt.strftime("%Y-%m")

    detail = detail.rename(columns={
        "Date": "Mois testé",
        "Prévu": "Prévision"
    })

    detail = detail[[
        "Groupe", "Mois testé", "Méthode",
        "Prévision", "Réel", "Erreur absolue"
    ]].sort_values(["Groupe", "Mois testé", "Méthode"])

    return {
        "T_Detail_Backtest": X.fill_table(
            wb, "T_Detail_Backtest", detail
        )
    }

def fill_backtest(wb, t):
    import pandas as pd
    from openpyxl.utils.cell import range_boundaries

    detail = t["fc_detail"]
    bilan = t["fc_summary"]
    valeur = t["value"].set_index("Groupe")

    scores = detail.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )

    niveaux = detail.drop_duplicates(
        ["Date", "Groupe"]
    ).groupby("Groupe")["Réel"].mean()

    # Reprendre les intitulés exacts du modèle actuel
    feuille, tableau = X.tables(wb)["T_Backtest"]
    c1, ligne, c2, _ = range_boundaries(tableau.ref)
    colonnes = [
        feuille.cell(ligne, col).value
        for col in range(c1, c2 + 1)
    ]
    assert len(colonnes) == 19, "Structure du backtest inattendue."

    lignes = []

    for groupe, resultat in bilan.iterrows():
        methode = resultat["Méthode choisie avant validation"]
        reference = resultat["Référence choisie avant validation"]

        erreurs = detail.loc[
            detail["Groupe"] == groupe
        ].pivot(
            index="Date",
            columns="Méthode",
            values="Erreur absolue"
        )

        mois_gagnes = int(
            (erreurs[methode] < erreurs[reference]).sum()
        )

        lignes.append([
            groupe,
            niveaux[groupe],
            scores.loc[groupe, "Mois précédent"],
            scores.loc[groupe, "Même mois N-1"],
            scores.loc[groupe, "Moyenne 3 mois"],
            scores.loc[groupe, "Holt-Winters"],
            None, None, None, None,  # MASE non calculés
            reference,
            resultat["Erreur relative (%)"] / 100,
            resultat["Gain (%)"] / 100,
            mois_gagnes,
            None,  # p-valeur non calculée
            valeur.loc[groupe, "Verdict : prévisible ?"],
            valeur.loc[groupe, "Erreur évitée par le modèle (unités/mois)"],
            valeur.loc[groupe, "Équivalent en jours de vente"],
            valeur.loc[groupe, "Méthode recommandée"]
        ])

    return {
        "T_Backtest": X.fill_table(
            wb, "T_Backtest",
            pd.DataFrame(lignes, columns=colonnes)
        )
    }

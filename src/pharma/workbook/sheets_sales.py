"""Feuilles Stats_Groupes, Stats_Mensuel et Environnement.   [Ihman]

fill(wb, c, t) : remplit chaque mois les tableaux et cellules nommées du modèle (lancé par main.py).
La mise en page (titres, graphiques, emplacement des tableaux) est déjà dans le modèle
templates/workbook_template.xlsx : ici, on ne fait qu'écrire les données dans les zones prévues.
"""
from __future__ import annotations

from . import tables as X

# Les zones que ce module a le droit de remplir (contrôlées par template.contract et verify)
TABLES = ["T_Groupes", "T_Saisonnalite", "T_Mois_Forts", "T_Cumul", "T_Annees", "T_Mensuel",
          "T_Grille_Liens", "T_Grippe_Effet", "T_Grippe_Serie"]
NAMES = ["txt_cumul_titre", "txt_grippe_source", "txt_grippe_note"]


def build(wb) -> None:
    """Dessin des feuilles dans le modèle : pas encore porté dans ce module.

    Le modèle versionné contient déjà ces feuilles. Si on doit le reconstruire
    (scripts/build_template.py), il faudra reprendre ici la mise en page actuelle.
    """
    raise NotImplementedError("sheets_sales.build : mise en page à reprendre depuis le modèle actuel")


def fill(wb, c, t) -> dict[str, int]:
    """Écrit les tableaux de statistiques et de grippe ; renvoie le nombre de lignes de chaque tableau.

    t : les tables calculées par pipeline.analyse_sales (descriptive.py et environment.py)
    """
    lignes = {
        # Feuille Stats_Groupes
        "T_Groupes": X.fill_table(wb, "T_Groupes", t["group_volumes"]),
        "T_Saisonnalite": X.fill_table(wb, "T_Saisonnalite", t["seasonality"]),
        "T_Mois_Forts": X.fill_table(wb, "T_Mois_Forts", t["peaks"]),
        "T_Cumul": X.fill_table(wb, "T_Cumul", t["year_to_date"]),
        "T_Annees": X.fill_table(wb, "T_Annees", t["yearly"]),
        # Feuille Stats_Mensuel
        "T_Mensuel": X.fill_table(wb, "T_Mensuel", t["monthly"]),
        # Feuille Environnement
        "T_Grille_Liens": X.fill_table(wb, "T_Grille_Liens", t["ladder"]),
        "T_Grippe_Effet": X.fill_table(wb, "T_Grippe_Effet", t["flu_effect"]),
        "T_Grippe_Serie": X.fill_table(wb, "T_Grippe_Serie", t["flu_series"]),
    }

    # Cellules de texte : titre du cumul (la période change chaque mois), source et note de la grippe
    X.set_named(wb, "txt_cumul_titre", f"Cumul de l'année : {t['year_to_date'].attrs['periode']}")
    X.set_named(wb, "txt_grippe_source", t["flu_source"])
    X.set_named(wb, "txt_grippe_note", t["flu_note"])
    return lignes

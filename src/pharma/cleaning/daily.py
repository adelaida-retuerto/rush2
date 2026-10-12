"""Nettoyage de l'export journalier (Pharma_Ventes_Daily.csv).

Ce fichier ne contient que ce qui est propre au journalier.
Les contrôles communs aux 4 exports (valeurs manquantes, négatives,
doublons, jours manquants) sont dans checks.py.
"""

import pandas as pd


def verifier_calendrier(journalier):
    """Vérifie que Year, Month et Weekday Name concordent avec la date de chaque ligne.

    Reçoit le tableau journalier avec la date en index (nommé datum).
    Renvoie les lignes qui ne concordent pas : un tableau vide si tout va bien.
    """
    annee_ok = journalier["Year"] == journalier.index.year
    mois_ok = journalier["Month"] == journalier.index.month
    # day_name() donne le nom du jour en anglais, comme dans l'export
    jour_ok = journalier["Weekday Name"] == journalier.index.day_name()

    # On garde les lignes où au moins une des trois colonnes est fausse
    return journalier[~(annee_ok & mois_ok & jour_ok)]


# Dans l'export, la colonne Hour d'un jour = la somme des heures présentes ce jour-là.
# Un jour complet a les 24 heures : 0 + 1 + ... + 23 = 276.
HOUR_JOUR_COMPLET = sum(range(24))


def reperer_jours_incomplets(journalier):
    """Repère les jours auxquels il manque des heures, grâce à la colonne Hour.

    Exemple : 248 = 8 + 9 + ... + 23 (le jour commence à 8h),
    190 = 0 + 1 + ... + 19 (le jour s'arrête à 19h).
    Renvoie les jours incomplets avec leur valeur de Hour : un tableau vide si tous sont complets.
    """
    incomplets = journalier["Hour"] != HOUR_JOUR_COMPLET
    return journalier.loc[incomplets, ["Hour"]]


# Colonnes du journalier qui ne sont pas des ventes :
# Year, Month et Weekday Name se recalculent à partir de la date, Hour est un artefact.
COLONNES_CALENDRIER = ["Year", "Month", "Hour", "Weekday Name"]


def garder_ventes(journalier):
    """Retire les colonnes de calendrier : il ne reste que les ventes des 8 groupes ATC.

    À appeler APRÈS verifier_calendrier et reperer_jours_incomplets,
    qui ont besoin de ces colonnes.
    """
    return journalier.drop(columns=COLONNES_CALENDRIER)


def nettoyer_journalier(journalier):
    """Enchaîne les 3 étapes dans le bon ordre : la seule fonction à appeler depuis run.py.

    Reçoit le journalier chargé (date en index, nommée datum).
    Renvoie deux choses :
    - ventes : une ligne par jour, les 8 groupes ATC en colonnes ;
    - rapport : ce qui a été trouvé, pour l'état des données.
    """
    # 1. Les contrôles d'abord, tant que les colonnes de calendrier sont là
    rapport = {
        "erreurs_calendrier": verifier_calendrier(journalier),
        "jours_incomplets": reperer_jours_incomplets(journalier),
    }
    # 2. Puis on ne garde que les ventes
    ventes = garder_ventes(journalier)
    return ventes, rapport


# Ce bloc ne s'exécute que si on lance ce fichier directement, pour tester.
# Provisoire : en attendant loading.py (socle), on lit le fichier nous-mêmes.
if __name__ == "__main__":
    from pathlib import Path

    racine = Path(__file__).resolve().parents[3]  # daily.py → cleaning → pharma → src → racine
    journalier = pd.read_csv(racine / "data" / "raw" / "Pharma_Ventes_Daily.csv")
    journalier["datum"] = pd.to_datetime(journalier["datum"], format="%m/%d/%Y")
    journalier = journalier.set_index("datum")

    ventes, rapport = nettoyer_journalier(journalier)

    print("Lignes dont le calendrier ne concorde pas :", len(rapport["erreurs_calendrier"]))
    print("Jours incomplets :", len(rapport["jours_incomplets"]))
    print(rapport["jours_incomplets"])
    print("Ventes :", len(ventes), "jours ; colonnes :", list(ventes.columns))

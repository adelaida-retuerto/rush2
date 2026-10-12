"""Nettoyage de l'export hebdomadaire (Pharma_Ventes_Weekly.csv).

Ce fichier ne contient que ce qui est propre à l'hebdomadaire.
Les contrôles communs aux 4 exports (valeurs manquantes, négatives,
doublons) sont dans checks.py.
"""

import pandas as pd


def verifier_dimanches(hebdomadaire):
    """Vérifie que chaque semaine est datée d'un dimanche (le dernier jour de la semaine).

    Reçoit le tableau hebdomadaire avec la date en index (nommé datum).
    Renvoie les semaines qui ne tombent pas un dimanche : un tableau vide si tout va bien.
    """
    # dayofweek numérote les jours de 0 (lundi) à 6 (dimanche)
    pas_dimanche = hebdomadaire.index.dayofweek != 6
    return hebdomadaire[pas_dimanche]


def verifier_ecarts(hebdomadaire):
    """Vérifie qu'il y a exactement 7 jours entre deux semaines qui se suivent.

    Un écart plus grand veut dire qu'une semaine manque dans l'export ;
    plus petit, que deux lignes se chevauchent.
    Renvoie les semaines dont l'écart avec la précédente n'est pas de 7 jours,
    avec cet écart en jours : un tableau vide si tout va bien.
    """
    dates = hebdomadaire.index.to_series()
    # diff() calcule, pour chaque date, le temps écoulé depuis la date précédente
    ecarts_en_jours = dates.diff().dt.days

    # La première semaine n'a pas de précédente (écart vide) : on ne la compte pas
    anormal = ecarts_en_jours.notna() & (ecarts_en_jours != 7)
    return ecarts_en_jours[anormal].to_frame("ecart_en_jours")


def comparer_au_journalier(hebdomadaire, ventes_journalieres):
    """Compare l'export hebdomadaire à la somme des jours de chaque semaine.

    ventes_journalieres : le tableau propre renvoyé par nettoyer_journalier (daily.py).
    Renvoie une ligne par case qui ne concorde pas (semaine, groupe, écart, les deux valeurs) :
    un tableau vide si tout concorde.
    """
    # On additionne les jours par semaine finissant le dimanche (W-SUN = Week, SUNday)
    somme_des_jours = ventes_journalieres.resample("W-SUN").sum()

    # Différence case par case, arrondie au centième ; en dessous de 0,01 ce sont des arrondis
    ecarts = (hebdomadaire - somme_des_jours).round(2)
    faux = ecarts.abs() > 0.01

    # On met les cases fausses en liste : une ligne par (semaine, groupe)
    # dropna() est nécessaire avec pandas 3 : stack() garde sinon les cases vides
    liste = ecarts[faux].stack().dropna().reset_index()
    liste.columns = ["semaine", "groupe", "ecart"]
    liste["hebdomadaire_client"] = [hebdomadaire.loc[s, g] for s, g in zip(liste["semaine"], liste["groupe"])]
    liste["somme_des_jours"] = [somme_des_jours.loc[s, g] for s, g in zip(liste["semaine"], liste["groupe"])]
    return liste


def reperer_semaines_incompletes(ventes_journalieres):
    """Repère les semaines qui ont moins de 7 jours de données.

    En pratique : la première semaine (les données ne commencent pas un lundi)
    et la dernière (l'export s'arrête en cours de semaine).
    Renvoie ces semaines avec leur nombre de jours : un tableau vide si toutes sont complètes.
    """
    # size() compte le nombre de jours présents dans chaque semaine
    jours_par_semaine = ventes_journalieres.resample("W-SUN").size()
    incompletes = jours_par_semaine < 7
    return jours_par_semaine[incompletes].to_frame("nombre_de_jours")


def nettoyer_hebdomadaire(hebdomadaire, ventes_journalieres):
    """Enchaîne les 4 contrôles : la seule fonction à appeler depuis run.py.

    Reçoit l'hebdomadaire chargé (date en index, nommée datum)
    et les ventes journalières propres renvoyées par nettoyer_journalier.
    Renvoie deux choses :
    - ventes : une ligne par semaine, les 8 groupes ATC en colonnes ;
    - rapport : ce qui a été trouvé, pour l'état des données.
    Les semaines incomplètes sont signalées, pas retirées : c'est à l'analyse de décider.
    """
    rapport = {
        "semaines_pas_dimanche": verifier_dimanches(hebdomadaire),
        "ecarts_anormaux": verifier_ecarts(hebdomadaire),
        "ecarts_avec_journalier": comparer_au_journalier(hebdomadaire, ventes_journalieres),
        "semaines_incompletes": reperer_semaines_incompletes(ventes_journalieres),
    }
    # L'export hebdomadaire ne contient que les ventes : rien à retirer
    return hebdomadaire, rapport


# Ce bloc ne s'exécute que si on lance ce fichier directement, pour tester.
# Provisoire : en attendant loading.py (socle), on lit le fichier nous-mêmes.
if __name__ == "__main__":
    from pathlib import Path

    racine = Path(__file__).resolve().parents[3]  # weekly.py → cleaning → pharma → src → racine
    hebdomadaire = pd.read_csv(racine / "data" / "raw" / "Pharma_Ventes_Weekly.csv")
    hebdomadaire["datum"] = pd.to_datetime(hebdomadaire["datum"], format="%m/%d/%Y")
    hebdomadaire = hebdomadaire.set_index("datum")

    # Les ventes journalières propres, obtenues avec daily.py
    from daily import nettoyer_journalier

    journalier = pd.read_csv(racine / "data" / "raw" / "Pharma_Ventes_Daily.csv")
    journalier["datum"] = pd.to_datetime(journalier["datum"], format="%m/%d/%Y")
    journalier = journalier.set_index("datum")
    ventes_journalieres, _ = nettoyer_journalier(journalier)

    ventes, rapport = nettoyer_hebdomadaire(hebdomadaire, ventes_journalieres)

    print("Semaines :", len(ventes))
    print("Semaines qui ne finissent pas un dimanche :", len(rapport["semaines_pas_dimanche"]))
    print("Écarts différents de 7 jours :", len(rapport["ecarts_anormaux"]))
    print("Cases qui ne concordent pas avec le journalier :", len(rapport["ecarts_avec_journalier"]))
    print("Semaines incomplètes :", len(rapport["semaines_incompletes"]))
    print(rapport["semaines_incompletes"])

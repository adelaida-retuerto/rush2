"""Donnée externe : la grippe (réseau Sentinelles) et son lien avec les ventes.   [Ihman]

Appelé par pipeline.py :
    flu, source = load_flu(offline)
    effet, serie = flu_effect(c.weekly, flu)
    grille = link_ladder(effet)
"""
from __future__ import annotations

import datetime as dt
import logging

import pandas as pd
import requests
import statsmodels.formula.api as smf

from .. import config

log = logging.getLogger(__name__)

SOURCE_SENTINELLES = "Réseau Sentinelles (Inserm, Sorbonne Université), syndromes grippaux, France entière"


def load_flu(offline: bool = False) -> tuple[pd.DataFrame, str]:
    """Récupère l'incidence hebdomadaire de la grippe en France.

    En ligne : télécharge la version à jour et la garde en copie dans data/external/.
    Hors ligne (ou si le site ne répond pas) : relit cette copie.
    Renvoie (tableau, phrase de source). Le tableau a une ligne par semaine, datée du
    dimanche comme nos ventes, et une colonne « incidence » en cas pour 100 000 habitants.
    """
    fichier = config.SENTIWEB_CACHE

    # 1. Téléchargement, sauf si on demande explicitement de rester hors ligne
    telecharge = False
    if not offline:
        try:
            reponse = requests.get(config.SENTIWEB_URL, timeout=30)
            reponse.raise_for_status()  # arrête si le site renvoie une erreur (page introuvable...)
            fichier.parent.mkdir(parents=True, exist_ok=True)
            fichier.write_text(reponse.text, encoding="utf-8")
            telecharge = True
        except requests.RequestException as erreur:
            log.warning("Sentinelles injoignable (%s) : on utilise la copie locale", erreur)

    if not fichier.exists():
        raise FileNotFoundError(f"Pas de copie locale de la donnée grippe : {fichier}. Relancer sans --offline.")

    if telecharge:
        source = f"{SOURCE_SENTINELLES}, téléchargé le {dt.date.today():%d/%m/%Y}"
    else:
        date_copie = dt.date.fromtimestamp(fichier.stat().st_mtime)
        source = f"{SOURCE_SENTINELLES}, copie locale du {date_copie:%d/%m/%Y}"

    # 2. Lecture : la première ligne du fichier est un commentaire (#), qu'on ignore
    brut = pd.read_csv(fichier, comment="#")

    # 3. Dates : la colonne week vaut par ex. 201403 = semaine ISO n°3 de 2014 (du lundi au dimanche).
    #    On la date de son dimanche (%u = 7), comme les semaines de ventes.
    annee = brut["week"] // 100
    semaine = brut["week"] % 100
    texte_iso = annee.astype(str) + "-W" + semaine.astype(str).str.zfill(2) + "-7"
    dates = pd.to_datetime(texte_iso, format="%G-W%V-%u")

    # 4. On garde l'incidence pour 100 000 habitants, du plus ancien au plus récent.
    #    Une semaine sans donnée est notée « - » (ex. semaine 19 de 1989) : elle devient vide (NaN).
    incidence = pd.to_numeric(brut["inc100"], errors="coerce")
    flu = pd.DataFrame({"incidence": incidence.values}, index=dates).sort_index()
    flu.index.name = "date"
    return flu, source


def aligner(weekly: pd.DataFrame, flu: pd.DataFrame) -> pd.DataFrame:
    """Met côte à côte, semaine par semaine, les ventes (8 groupes) et l'incidence de la grippe.

    weekly : semaines complètes de ventes (c.weekly), datées du dimanche
    On ajoute aussi l'incidence de la semaine précédente (incidence_s1).
    On ne garde que les semaines présentes des deux côtés, sans valeur vide.
    """
    grippe = flu[["incidence"]].copy()
    # shift(1) décale d'une ligne : chaque semaine reçoit l'incidence de la semaine d'avant.
    # On le fait sur la série grippe complète, AVANT de la coller aux ventes, pour ne pas sauter de semaine.
    grippe["incidence_s1"] = grippe["incidence"].shift(1)
    # join « inner » : seulement les dates communes aux deux tableaux
    return weekly[config.GROUP_CODES].join(grippe, how="inner").dropna()


def correlation_brute(donnees: pd.DataFrame) -> pd.Series:
    """Corrélation de Spearman entre l'incidence de la grippe et les ventes de chaque groupe.

    Spearman compare les CLASSEMENTS des semaines (de la plus faible à la plus forte), pas les
    valeurs : il mesure si les deux montent ensemble, même sans proportionnalité, et un pic
    isolé ne le fausse pas. Résultat entre -1 et +1 (0 = aucun lien).
    ATTENTION : c'est un lien BRUT. La grippe et beaucoup de ventes montent toutes les deux en
    hiver : une corrélation peut venir seulement de la saison commune.
    """
    ventes = donnees[config.GROUP_CODES]
    return ventes.corrwith(donnees["incidence"], method="spearman")


# Deux semaines qui se suivent se ressemblent (ventes et grippe évoluent lentement) : les 300
# semaines ne sont pas 300 observations indépendantes. On corrige les p-valeurs en tenant
# compte de ce lien sur 4 semaines (environ un mois), méthode dite HAC (Newey-West).
SEMAINES_LIEES = 4


def effet_a_saison_egale(donnees: pd.DataFrame) -> pd.DataFrame:
    """Effet de la grippe sur les ventes de chaque groupe, À SAISON ÉGALE.

    On compare deux modèles de régression, groupe par groupe :
      - « saison seule »   : ventes de la semaine = niveau habituel de son mois ;
      - « saison + grippe » : la même chose + un effet proportionnel à l'incidence.
    L'effet de la grippe est donc mesuré en comparant les semaines d'un même mois entre
    elles (un janvier de forte grippe face aux autres janvier) : la saison est neutralisée.
    """
    donnees = donnees.copy()
    donnees["mois"] = donnees.index.month

    lignes = []
    for groupe in config.GROUP_CODES:
        # C(mois) = « un niveau propre à chaque mois » (12 catégories, pas un nombre de 1 à 12)
        saison_seule = smf.ols(f"{groupe} ~ C(mois)", data=donnees).fit()
        saison_grippe = smf.ols(f"{groupe} ~ C(mois) + incidence", data=donnees).fit(
            cov_type="HAC", cov_kwds={"maxlags": SEMAINES_LIEES})

        # Coefficient = ventes en plus par cas pour 100 000 ; on l'exprime pour +100 cas
        effet_100 = saison_grippe.params["incidence"] * 100
        lignes.append({
            "Groupe": groupe,
            "Effet par +100 cas/100k (même mois)": round(effet_100, 2),
            "p-valeur": round(saison_grippe.pvalues["incidence"], 4),
            "Effet en % de la moyenne hebdo": round(effet_100 / donnees[groupe].mean(), 4),
            "R² saison seule": round(saison_seule.rsquared, 3),
            "R² saison + grippe": round(saison_grippe.rsquared, 3),
            "Gain de R²": round(saison_grippe.rsquared - saison_seule.rsquared, 3),
        })
    return pd.DataFrame(lignes)


def effet_semaine_precedente(donnees: pd.DataFrame) -> pd.DataFrame:
    """Même modèle qu'effet_a_saison_egale, mais avec la grippe de la SEMAINE PRÉCÉDENTE (S-1).

    Idée : on achète peut-être ses médicaments après le pic de symptômes, pas pendant.
    """
    donnees = donnees.copy()
    donnees["mois"] = donnees.index.month

    lignes = []
    for groupe in config.GROUP_CODES:
        modele = smf.ols(f"{groupe} ~ C(mois) + incidence_s1", data=donnees).fit(
            cov_type="HAC", cov_kwds={"maxlags": SEMAINES_LIEES})
        lignes.append({
            "Groupe": groupe,
            "Effet avec grippe S-1": round(modele.params["incidence_s1"] * 100, 2),
            "p-valeur S-1": round(modele.pvalues["incidence_s1"], 4),
        })
    return pd.DataFrame(lignes)


# Saison de la grippe en France : de décembre à mars
MOIS_HIVER = [12, 1, 2, 3]


def comparaison_hivers(donnees: pd.DataFrame) -> tuple[pd.Series, float]:
    """Compare, en hiver, les semaines de forte grippe aux autres semaines d'hiver.

    « Forte grippe » = les 15 % de semaines où l'incidence est la plus haute (config.EPIDEMIC_PERCENTILE).
    Pour ne pas comparer un janvier à un mars, chaque semaine est d'abord divisée par la
    moyenne de son mois (1,10 = 10 % au-dessus d'un mois habituel).
    Renvoie (rapport par groupe, seuil d'incidence) : 1,15 = 15 % de ventes en plus
    pendant les semaines de forte grippe, à mois égal.
    """
    seuil = donnees["incidence"].quantile(config.EPIDEMIC_PERCENTILE)
    hiver = donnees.index.month.isin(MOIS_HIVER)
    forte = donnees["incidence"] >= seuil

    rapports = {}
    for groupe in config.GROUP_CODES:
        # Indice = ventes de la semaine / moyenne de toutes les semaines du même mois
        moyenne_du_mois = donnees.groupby(donnees.index.month)[groupe].transform("mean")
        indice = donnees[groupe] / moyenne_du_mois
        rapports[groupe] = indice[hiver & forte].mean() / indice[hiver & ~forte].mean()
    return pd.Series(rapports).round(3), seuil


# Seuils de lecture des résultats
SEUIL_P = 0.01             # « lien significatif » si p < 0,01 (choix de l'équipe, titre de colonne du classeur)
SEUIL_CORRELATION = 0.3    # en dessous de 0,3 (en valeur absolue), une corrélation est faible
SEUIL_HAUSSE_HIVER = 1.10  # au moins +10 % en semaine de forte grippe, à mois égal


def nature_du_lien(spearman: float, p_valeur: float, effet: float, rapport_hiver: float) -> tuple[str, str]:
    """Traduit les chiffres d'un groupe en deux phrases : la nature du lien et ce qu'on peut dire de la causalité."""
    if p_valeur < SEUIL_P and effet > 0:
        return ("Effet propre de la grippe, au-delà de la saison",
                "Plausible, non démontrée : données observées, pas d'expérience")
    if rapport_hiver >= SEUIL_HAUSSE_HIVER:
        return ("Hausse pendant les épidémies, non prouvée statistiquement",
                "Non démontrée : tendance à surveiller")
    if abs(spearman) >= SEUIL_CORRELATION:
        return ("Lien de saison seulement : grippe et ventes suivent le même calendrier",
                "Non : la saison explique le lien")
    return ("Pas de lien", "Non")


def flu_effect(weekly: pd.DataFrame, flu: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assemble toute l'analyse grippe pour le classeur (feuille Environnement).

    weekly : semaines complètes de ventes (c.weekly) ; flu : résultat de load_flu
    Renvoie :
    - effet : une ligne par groupe, colonnes du tableau T_Grippe_Effet ;
    - serie : ventes et incidence semaine par semaine, pour le graphique (T_Grippe_Serie).
    """
    donnees = aligner(weekly, flu)

    # Les 4 analyses, chacune déjà testée séparément
    spearman = correlation_brute(donnees)
    saison = effet_a_saison_egale(donnees).set_index("Groupe")
    retard = effet_semaine_precedente(donnees).set_index("Groupe")
    hiver, seuil = comparaison_hivers(donnees)

    # On les réunit dans l'ordre exact des colonnes du modèle Excel
    effet = saison.join(retard)
    effet.insert(0, "Corrélation de Spearman (brute)", spearman.round(3))
    effet["Hiver : ventes sem. forte grippe / autres"] = hiver
    effet["Lien significatif (p<0,01)"] = ["Oui" if p < SEUIL_P else "Non" for p in effet["p-valeur"]]

    phrases = [nature_du_lien(spearman[g], effet.loc[g, "p-valeur"],
                              effet.loc[g, "Effet par +100 cas/100k (même mois)"], hiver[g])
               for g in effet.index]
    effet["Nature du lien"] = [nature for nature, _ in phrases]
    effet["Causalité"] = [causalite for _, causalite in phrases]
    effet = effet.reset_index()

    # Informations reprises dans la note sous le tableau (pipeline.py)
    effet.attrs["n_weeks"] = len(donnees)
    effet.attrs["threshold"] = seuil
    # Nombre d'hivers observés : un hiver va de décembre à mars, on le nomme par l'année de son mois de janvier
    hivers = donnees.index[donnees.index.month.isin(MOIS_HIVER)]
    effet.attrs["n_hivers"] = len({d.year + 1 if d.month == 12 else d.year for d in hivers})

    # Série pour le graphique : les dernières semaines (config.CHART_WINDOW_WEEKS = 3 ans)
    serie = donnees[config.GROUP_CODES + ["incidence"]].tail(config.CHART_WINDOW_WEEKS)
    serie = serie.rename(columns={"incidence": "Incidence grippe"})
    serie.insert(0, "Semaine", serie.index)
    serie = serie.reset_index(drop=True)
    return effet, serie


def link_ladder(effet: pd.DataFrame) -> pd.DataFrame:
    """Grille de lecture (tableau T_Grille_Liens) : du lien le plus faible à la causalité.

    Chaque niveau est illustré par NOS résultats (calculés depuis effet, donc à jour chaque mois).
    """
    e = effet.set_index("Groupe")
    nom = lambda g: f"{g} · {config.GROUPS[g]}"  # charte : toujours le code ATC avec son nom
    # Un nombre écrit à la française : 0,68 et non 0.68 (format = ".2f", "+.1%"...)
    nombre = lambda valeur, format_: format(valeur, format_).replace(".", ",")

    # Exemples tirés des résultats
    spearman = e["Corrélation de Spearman (brute)"]
    plus_correle, moins_correle = spearman.idxmax(), spearman.idxmin()
    hausses = e[e["Hiver : ventes sem. forte grippe / autres"] >= SEUIL_HAUSSE_HIVER]
    hausses = hausses.sort_values("Hiver : ventes sem. forte grippe / autres", ascending=False)
    significatifs = e[e["Lien significatif (p<0,01)"] == "Oui"]

    texte_hausses = " ; ".join(f"{nom(g)} {nombre(r - 1, '+.0%')}"
                               for g, r in hausses["Hiver : ventes sem. forte grippe / autres"].items())
    texte_significatifs = (", ".join(nom(g) for g in significatifs.index) if len(significatifs)
                           else f"Aucun groupe (plus petite p-valeur : {nombre(e['p-valeur'].min(), '.2f')})")

    lignes = [
        ["1. Corrélation brute",
         "Les ventes et la grippe montent et baissent en même temps",
         f"{nom(plus_correle)} : {nombre(spearman[plus_correle], '+.2f')} ; "
         f"{nom(moins_correle)} : {nombre(spearman[moins_correle], '+.2f')}",
         "Rien sur la grippe : le lien peut venir de la saison commune (l'hiver)"],
        ["2. Lien à saison égale",
         "Même lien, en comparant les semaines d'un même mois entre elles",
         f"{nom('N02BE')} : {nombre(e.loc['N02BE', 'Effet en % de la moyenne hebdo'], '+.1%')} par +100 cas/100k ; "
         f"la grippe n'ajoute que {nombre(e.loc['N02BE', 'Gain de R²'], '.3f')} de R² à la saison",
         "Le calendrier explique l'essentiel ; la grippe ajoute peu en moyenne"],
        ["3. Hausse pendant les épidémies",
         "En hiver, semaines de forte grippe comparées aux autres semaines d'hiver, à mois égal",
         texte_hausses or "Aucune hausse d'au moins 10 %",
         "Signal utile pour le stock des médicaments contre la fièvre, la douleur et la gêne respiratoire"],
        ["4. Lien significatif",
         f"Lien trop net pour être dû au hasard (p < {nombre(SEUIL_P, '.2f')})",
         texte_significatifs,
         f"Avec {effet.attrs.get('n_hivers', '?')} hivers observés, la hausse en épidémie n'est pas prouvée : "
         "c'est une tendance"],
        ["5. Causalité",
         "La grippe PROVOQUE les achats",
         "Mécanisme plausible (fièvre, courbatures, toux), mais données observées sans expérience",
         "Non démontrée : utiliser la grippe comme signal d'alerte, pas comme prévision certaine"],
    ]
    return pd.DataFrame(lignes, columns=["Niveau", "Définition", "Exemple dans ce projet", "Ce qu'on peut en conclure"])


# Test : depuis le dossier src, lancer   python -m pharma.analysis.environment
if __name__ == "__main__":
    flu, source = load_flu()
    print(source)
    print(f"{len(flu)} semaines, du {flu.index.min():%d/%m/%Y} au {flu.index.max():%d/%m/%Y}")
    print("Jours de la semaine des dates (6 = dimanche) :", sorted(set(flu.index.dayofweek)))
    print(flu.loc["2014":"2019", "incidence"].describe().round(0))

    # Les semaines complètes de ventes, comme dans pipeline.py (c.weekly)
    from ..cleaning import hourly, loading
    from ..cleaning.weekly import clean_weekly

    journal = []
    horaire = hourly.clean_hourly(loading.load_export("hourly"), loading.load_derived_columns("hourly"), journal)
    weekly, _ = clean_weekly(loading.load_export("weekly"), None, horaire.daily_all, horaire.complete_day, journal)

    effet, serie = flu_effect(weekly, flu)
    print(f"\n{effet.attrs['n_weeks']} semaines analysées ; forte grippe = au moins {effet.attrs['threshold']:.0f} cas/100k")
    print(effet[["Groupe", "Corrélation de Spearman (brute)", "p-valeur",
                 "Hiver : ventes sem. forte grippe / autres", "Nature du lien"]].to_string(index=False))
    print(f"\nSérie pour le graphique : {len(serie)} semaines, du {serie['Semaine'].min():%d/%m/%Y} au {serie['Semaine'].max():%d/%m/%Y}")

    print("\nGrille de lecture :")
    for _, ligne in link_ladder(effet).iterrows():
        print(f"\n{ligne['Niveau']} — {ligne['Définition']}")
        print(f"   Exemple : {ligne['Exemple dans ce projet']}")
        print(f"   Conclusion : {ligne['Ce qu\'on peut en conclure']}")

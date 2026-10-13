"""Contenu de la feuille Synthèse : message clé, chiffres clés, insights, recommandations, limites.   [Jeanne · Adelaida]

Tout est recalculé à chaque mise à jour à partir des tables des trois flux (t) : aucune phrase
chiffrée n'est écrite à la main. Les tailles (6 chiffres clés, 6 insights, 5 recommandations,
6 limites) correspondent aux cartes du modèle (workbook/sheets_summary.py).
"""
from __future__ import annotations

import pandas as pd

from .. import config
from .descriptive import NOMS_MOIS, family_volumes

G = config.GROUP_CODES


# --- Petits outils d'écriture à la française ------------------------------------------------------
def _nombre(x: float, decimales: int = 0) -> str:
    """1 315,0 et non 1,315.0 (espace insécable comme séparateur de milliers)."""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


def _pct(x: float, signe: bool = False) -> str:
    texte = f"{x:+.0%}" if signe else f"{x:.0%}"
    return texte.replace("%", " %")


def _nom(g: str) -> str:
    """Charte : le code ATC toujours avec son nom, en version courte (« R06 · Antihistaminiques »)."""
    return f"{g} · {config.GROUPS[g].split(' (')[0]}"


def _liste(mots: list[str]) -> str:
    if not mots:
        return "aucun"
    return mots[0] if len(mots) == 1 else ", ".join(mots[:-1]) + " et " + mots[-1]


def _mois_avant(mois: str) -> str:
    """« Mai » -> « avril » : le mois où il faut constituer le stock."""
    return NOMS_MOIS[(NOMS_MOIS.index(mois) - 1) % 12].lower()


def _groupes_prevus(t) -> list[str]:
    """Groupes où un modèle a fait mieux que la règle simple en validation (verdict « Gain observé ... »)."""
    valeur = t["value"]
    return list(valeur.loc[valeur["Verdict : prévisible ?"].str.startswith("Gain"), "Groupe"])


def _pointes(t) -> tuple[str, str]:
    """Heure la plus chargée du matin (avant 14 h) et de l'après-midi."""
    parts = t["hourly"].set_index("Heure")["Total"]
    matin = parts[[int(h[:2]) < 14 for h in parts.index]].idxmax()
    soir = parts[[int(h[:2]) >= 14 for h in parts.index]].idxmax()
    return matin, soir


def _hausses_grippe(t) -> pd.Series:
    """Hausse des ventes en semaine de forte grippe, à mois égal (0,16 = +16 %), triée."""
    effet = t["flu_effect"].set_index("Groupe")
    return (effet["Hiver : ventes sem. forte grippe / autres"] - 1).sort_values(ascending=False)


# --- 1. Chiffres clés (6 cartes) ------------------------------------------------------------------
def kpis(c, t) -> pd.DataFrame:
    cumul = t["year_to_date"]
    evolution = cumul["Cumul année en cours"].sum() / cumul["Cumul année précédente"].sum() - 1
    familles = family_volumes(c)
    top = familles.iloc[0]
    seuil = config.SMALL_COUNT_THRESHOLD
    comptages = t["privacy"].set_index(["Niveau", "Groupe"])
    part_n05c = comptages.loc[("Heure", "N05C"), f"Part ≤ {seuil} unités"]
    return pd.DataFrame([
        [_nombre(len(c.daily)), f"jours complets analysés, du {c.daily.index.min():%d/%m/%Y} "
                                f"au {c.daily.index.max():%d/%m/%Y}"],
        [_nombre(c.daily[G].sum(axis=1).mean(), 1), "quantités vendues par jour en moyenne (8 groupes, "
                                                   "unité du logiciel de caisse)"],
        [f"{evolution:+.1%}".replace(".", ",").replace("%", "\u00a0%"), f"ventes {cumul.attrs.get('periode', 'depuis janvier vs N-1')}"],
        [_pct(top["Part du volume"]), f"des volumes : {top['Famille'].lower()} ({top['Groupes']})"],
        [f"{t['n_bad_months']} / {t['n_monthly_rows']}", "mois faux dans l'export mensuel : "
                                                         "ne pas l'utiliser pour commander"],
        [_pct(part_n05c), f"des ventes horaires d'hypnotiques tiennent en ≤ {seuil} unités : identifiables"],
    ], columns=["Valeur", "Libellé"])


# --- 2. Ce qu'il faut retenir (6 cartes : thème, chiffre marquant, message) -------------------------
def insights(c, t) -> pd.DataFrame:
    volumes = t["group_volumes"].set_index("Groupe")["Part du volume"]
    pics = t["peaks"].set_index("Groupe")
    jours = t["weekday"].set_index("Jour")["Total"]
    jour_fort = jours.idxmax()
    matin, soir = _pointes(t)
    hausses = _hausses_grippe(t)
    top_grippe = hausses.index[0]
    attrs = t["flu_effect"].attrs
    prevus = _groupes_prevus(t)
    ecarts = c.discrepancies
    n_ecarts_controle = int(ecarts["Export"].isin(["daily", "weekly"]).sum()) if len(ecarts) else 0
    amplitude = pics["Amplitude max sur min"].astype(float)
    plus_saisonnier = amplitude.idxmax()

    lignes = [
        ["QUALITÉ DES DONNÉES",
         f"{n_ecarts_controle} écart" if n_ecarts_controle < 2 else f"{n_ecarts_controle} écarts",
         f"Horaire, journalier et hebdomadaire concordent. L'export mensuel est faux sur {t['n_bad_months']} mois, "
         "toujours trop haut : tout est recalculé depuis l'horaire."],
        ["CE QUI SE VEND",
         _pct(volumes["N02BE"]),
         f"des volumes pour {_nom('N02BE')} (paracétamol). Avec {_nom('N05B')} ({_pct(volumes['N05B'])}), "
         f"deux groupes portent {_pct(volumes['N02BE'] + volumes['N05B'])} de l'activité."],
        ["SAISONS",
         f"×{_nombre(amplitude[plus_saisonnier], 1)}",
         f"entre le mois fort ({pics.loc[plus_saisonnier, 'Mois le plus fort'].lower()}) et le mois faible pour "
         f"{_nom(plus_saisonnier)}. {_nom('R03')} culmine en {pics.loc['R03', 'Mois le plus fort'].lower()}, "
         f"{_nom('N02BE')} en {pics.loc['N02BE', 'Mois le plus fort'].lower()}."],
        ["SEMAINE ET HEURES",
         _pct(jours[jour_fort] - 1, True),
         f"de ventes le {jour_fort.lower()}, jour le plus chargé. Deux pointes par jour : {matin} et {soir}."],
        ["GRIPPE (DONNÉE PUBLIQUE)",
         _pct(hausses[top_grippe], True),
         f"pour {_nom(top_grippe)} en semaine de forte grippe, à mois égal (Sentinelles). Signal à surveiller, "
         f"non prouvé : {attrs.get('n_hivers', '?')} hivers observés."],
        ["PRÉVISION",
         f"{len(prevus)} / {len(G)}",
         f"groupes où un modèle fait mieux qu'une règle simple sur 12 mois jamais vus ({_liste(prevus)}), "
         "utilité à confirmer. Pour les autres, une règle simple (mois précédent, moyenne 3 mois) suffit."],
    ]
    return pd.DataFrame(lignes, columns=["Thème", "Chiffre", "Message"])


# --- 3. Recommandations (5 leviers : axe, action précise et chiffrée) ---------------------------------
def recommendations(c, t) -> pd.DataFrame:
    pics = t["peaks"].set_index("Groupe")
    jours = t["weekday"].set_index("Jour")["Total"]
    parts_heure = t["hourly"].set_index("Heure")["Total"]
    matin, soir = _pointes(t)
    hausses = _hausses_grippe(t)
    seuil_grippe = t["flu_effect"].attrs.get("threshold", float("nan"))
    a_renforcer = [g for g in hausses.index if hausses[g] >= 0.10]  # repère +10 %, comme environment.py
    prevus = _groupes_prevus(t)
    autres = len(G) - len(prevus)
    seuil = config.SMALL_COUNT_THRESHOLD
    part_n05c = t["privacy"].set_index(["Niveau", "Groupe"]).loc[("Heure", "N05C"), f"Part ≤ {seuil} unités"]

    def pic(g: str) -> str:
        """« mai, ×1,90 » : mois le plus fort et son indice de saison."""
        return f"{pics.loc[g, 'Mois le plus fort'].lower()}, ×{_nombre(pics.loc[g, 'Indice max'], 2)}"

    return pd.DataFrame([
        ["Anticiper les saisons",
         f"Constituer le stock un mois avant chaque pic : {_nom('R06')} dès {_mois_avant(pics.loc['R06', 'Mois le plus fort'])} "
         f"(pic en {pic('R06')} la moyenne) ; {_nom('N02BE')} dès {_mois_avant(pics.loc['N02BE', 'Mois le plus fort'])} "
         f"({pic('N02BE')}) ; {_nom('R03')} dès {_mois_avant(pics.loc['R03', 'Mois le plus fort'])} ({pic('R03')}). "
         "Mise en avant limitée aux médicaments sans ordonnance."],
        ["Déclencher sur la grippe",
         f"Suivre l'incidence Sentinelles chaque semaine. Au-delà de {_nombre(seuil_grippe)} cas pour 100 000, "
         "augmenter le stock de "
         + _liste([f"{_nom(g)} ({_pct(hausses[g], True)})" for g in a_renforcer]) + "."],
        ["Caler l'effectif sur l'affluence",
         f"Renforcer le comptoir le {jours.idxmax().lower()} ({_pct(jours.max() - 1, True)} de ventes) et aux "
         f"pointes de {matin} et {soir} ({_pct(parts_heure[matin])} et {_pct(parts_heure[soir])} des ventes "
         "de la journée)."],
        ["Protéger les données de santé",
         f"Ne céder aucun export horaire, journalier ou hebdomadaire : {_pct(part_n05c)} des heures avec un "
         f"hypnotique vendu comptent {seuil} unités ou moins. Au plus des totaux mensuels sans N05B ni N05C, "
         "sous contrat écrit et après avis juridique."],
        ["Piloter sur des chiffres fiables",
         f"Commander à partir des ventes recalculées, jamais de l'export mensuel ({t['n_bad_months']} mois sur "
         f"{t['n_monthly_rows']} surestimés). Prévision par modèle pour {_liste(prevus)} ; règle simple pour les "
         f"{autres} autres groupes."],
    ], columns=["Axe", "Recommandation"])


def key_message(c, t) -> str:
    """Le message clé de la Synthèse : la situation et l'enjeu en une phrase."""
    cumul = t["year_to_date"]
    evolution = cumul["Cumul année en cours"].sum() / cumul["Cumul année précédente"].sum() - 1
    volumes = t["group_volumes"].set_index("Groupe")["Part du volume"]
    pics = t["peaks"].set_index("Groupe")
    plus_saisonnier = pics["Amplitude max sur min"].astype(float).idxmax()
    return (f"Une activité stable ({f'{evolution:+.1%}'.replace('.', ',').replace('%', chr(160) + '%')} sur un an), portée par le paracétamol "
            f"({_pct(volumes['N02BE'])} des volumes) et rythmée par des saisons prévisibles (jusqu'à "
            f"×{_nombre(pics.loc[plus_saisonnier, 'Amplitude max sur min'], 1)} pour {_nom(plus_saisonnier)}) : "
            "le levier est d'anticiper le stock, et l'export détaillé ne doit pas sortir de la pharmacie.")


# --- 4. Limites (6 lignes) ----------------------------------------------------------------------------
def limits(c) -> pd.DataFrame:
    return pd.DataFrame([
        ["Unité des quantités non documentée", "On parle de quantités, jamais de boîtes",
         "Demander l'unité à l'éditeur du logiciel"],
        ["Aucun prix", "Aucune conclusion en euros : la valeur de la prévision est chiffrée en jours de vente",
         "Obtenir les prix d'achat (mission de suivi)"],
        ["Données d'observation", "On mesure des associations (grippe, saisons) ; aucune causalité n'est démontrée",
         "Tester un changement (stock, planning) avant / après"],
        ["Pharmacie probablement hors de France", "Ventes 7 j/7 de 7 h à 22 h, même les jours fériés : le lien avec la "
         "grippe française reste une approximation", "Confirmer la localisation de la pharmacie"],
        [f"{len(c.monthly)} mois d'historique", "Peu d'hivers pour juger la grippe et la prévision : les verdicts "
         "peuvent changer", "Relancer chaque mois : les tests se refont seuls"],
        ["Dernier jour incomplet", f"Export arrêté le {c.meta['last_day']:%d/%m/%Y} à {c.meta['last_hour']}h : "
         f"mois en cours exclu", "Rien à faire : exclu automatiquement"],
    ], columns=["Limite", "Conséquence sur les conclusions", "Comment la lever"])


# --- 5. Verdict de prévision (tableau T_Verdict) -------------------------------------------------------
def verdict_table(t) -> pd.DataFrame:
    """Verdict de prévision par groupe, avec la prévision du mois suivant (8 lignes, tableau T_Verdict)."""
    valeur = t["value"][["Groupe", "Verdict : prévisible ?", "Méthode recommandée"]]
    bilan = t["fc_summary"].reset_index()[["Groupe", "Gain (%)", "Erreur relative (%)"]]  # Groupe est l'index
    bilan = bilan.rename(columns={"Gain (%)": "Gain vs référence (%)"})
    suivant = t["fc_next"][["Groupe", "Quantité prévue", "Borne basse indicative", "Borne haute indicative"]]
    suivant = suivant.rename(columns={"Quantité prévue": "Prévision"})
    return valeur.merge(bilan, on="Groupe").merge(suivant, on="Groupe")

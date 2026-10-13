"""Cadrage et limites de l'analyse — Jeanne."""

import pandas as pd


def needs():
    return pd.DataFrame([
        [
            "Manager",
            "Évaluer la solidité de l'analyse",
            "Décider d'une mission de suivi",
            "Contrôles des exports et test des prévisions",
            "Synthèse, prévision et deck manager"
        ],
        [
            "Pharmacien achats",
            "Anticiper les quantités et les périodes",
            "Adapter les commandes",
            "Saisonnalité, signal grippe et outil de sélection",
            "Classeur Excel et deck pharmacien"
        ],
        [
            "Propriétaire",
            "Adapter le fonctionnement et examiner le partage",
            "Choisir les actions et les conditions de partage",
            "Profils de ventes et analyse des risques",
            "Confidentialité, note PDF et deck propriétaire"
        ]
    ], columns=[
        "Interlocuteur", "Problématique", "Décision attendue",
        "Ce que nous apportons", "Livrable"
    ])


def limits(c):
    n_mois = len(c.monthly)

    return pd.DataFrame([
        [
            "Unité des quantités non documentée ; aucun prix",
            "Pas de conversion en boîtes, euros ou marge",
            "Demander le dictionnaire des données au client"
        ],
        [
            f"Historique de {n_mois} mois complets",
            "Résultats propres à cette pharmacie et cette période",
            "Tester sur de nouveaux exports"
        ],
        [
            "Validation sur 12 mois déjà observés en exploration",
            "Comparaison exploratoire ; sélection possiblement influencée",
            "Évaluer les choix fixés sur de nouveaux mois"
        ],
        [
            "Fourchettes indicatives issues de 12 erreurs",
            "Aucune garantie de couverture à 80 % ou 90 %",
            "Évaluer la couverture sur une période distincte"
        ],
        [
            "Grippe non intégrée aux modèles de prévision",
            "Son apport prédictif n'est pas démontré ici",
            "Tester un signal disponible avant chaque prévision"
        ],
          [
            "Aucune donnée de stock",
            "Les jours de ventes équivalents ne sont pas un gain de stock",
            "Obtenir stocks, délais et ruptures"
        ],
        [
            "Sensibilité numérique de Holt-Winters",
            "De faibles arrondis peuvent modifier l'ajustement ; "
            "les données en mémoire sont la source retenue",
            "Conserver la même précision et tester la stabilité du modèle"
        ],
    ], columns=[
        "Limite", "Conséquence sur les conclusions", "Comment la lever"
    ])

def decisions(c, base):
    return pd.DataFrame([
        [
            "Source des ventes",
            "Recalculer depuis l'export horaire",
            "Utiliser directement l'export mensuel",
            f"{base['n_bad_months']} mois en écart sur "
            f"{base['n_monthly_rows']} mois exportés"
        ],
        [
            "Périodes incomplètes",
            "Utiliser les mois complets pour prévoir",
            "Traiter les mois partiels comme des mois entiers",
            f"{len(c.monthly)} mois complets ; dernier mois : "
            f"{c.last_complete_month:%Y-%m}"
        ],
        [
            "Pics de ventes",
            "Signaler les pics et conserver les quantités",
            "Supprimer automatiquement les valeurs élevées",
            "Un pic peut refléter une variation réelle"
        ],
        [
            "Choix des méthodes",
            "Sélection sur une période antérieure à la validation",
            "Choisir uniquement la meilleure méthode après validation",
            "Limiter le biais de sélection ; analyse encore exploratoire"
        ],
        [
            "Modèle moins précis",
            "Revenir à la référence pour la recommandation",
            "Imposer Holt-Winters à tous les groupes",
            "Repli décidé après validation, non validé indépendamment"
        ]
    ], columns=[
        "Sujet", "Décision", "Alternative écartée", "Raison"
    ])


def project_risks():
    return pd.DataFrame([
        [
            "Nouvel export avec un format différent",
            "Non estimée",
            "Contrôler les colonnes, dates et quantités à chaque relance"
        ],
        [
            "Prévisions moins précises sur de nouveaux mois",
            "Non estimée",
            "Comparer régulièrement les prévisions aux ventes réelles"
        ],
        [
            "Fourchettes interprétées comme garanties",
            "Non estimée",
            "Afficher leur caractère indicatif"
        ],
        [
            "Gain d'erreur présenté comme une économie de stock",
            "Non estimée",
            "Préciser : équivalent en jours de ventes, sans stocks réels"
        ]
    ], columns=["Risque", "Probabilité", "Mesure"])

def verdict_table(t):
    bilan = t["fc_summary"]
    previsions = t["fc_next"].set_index("Groupe")
    valeur = t["value"].set_index("Groupe")

    lignes = []

    for groupe, resultat in bilan.iterrows():
        lignes.append({
            "Groupe": groupe,
            "Meilleure référence naïve":
                resultat["Référence choisie avant validation"],
            "Erreur du modèle en % du niveau":
                resultat["Erreur relative (%)"] / 100,
            "Gain du modèle vs meilleure référence":
                resultat["Gain (%)"] / 100,
            "Verdict : prévisible ?":
                valeur.loc[groupe, "Verdict : prévisible ?"],
            "Prévision":
                previsions.loc[groupe, "Quantité prévue"],
            "Fourchette basse (80 %)": None,
            "Fourchette haute (80 %)": None
        })

    return pd.DataFrame(lignes)

def kpis(c, t):
    return pd.DataFrame([
        ["Mois complets analysés", len(c.monthly)],
        ["Dernier mois complet", c.last_complete_month.strftime("%Y-%m")],
        ["Mois exportés en écart", t["n_bad_months"]],
        ["Groupes analysés", len(c.monthly.columns)],
        ["Mois de validation", t["fc_summary"].attrs["n_test"]]
    ], columns=["Indicateur", "Valeur"])


def key_messages(c, t):
    bilan = t["fc_summary"]
    gain_n02be = bilan.loc["N02BE", "Gain (%)"]
    erreur_r06 = bilan.loc["R06", "Erreur relative (%)"]

    return pd.DataFrame([
        [
            "Qualité des données",
            f"{t['n_bad_months']} mois exportés en écart ; "
            "ventes recalculées depuis l'horaire."
        ],
        [
            "Prévision",
            f"N02BE : réduction d'erreur de {gain_n02be:.1f} % "
            "face à la référence sélectionnée."
        ],
        [
            "Prudence",
            f"R06 : erreur relative de {erreur_r06:.1f} %. "
            "Pour R03, repli vers la référence après validation."
        ],
        [
            "Suivi",
            "Relancer les contrôles et comparer les prévisions "
            "aux nouvelles ventes chaque mois."
        ]
    ], columns=["Thème", "Message"])


def success_criteria(c, t):
    return pd.DataFrame([
        [
            "Qualité",
            "Concordance entre exports",
            f"{t['n_bad_months']} mois en écart ; "
            "source horaire retenue",
            "Écarts documentés"
        ],
        [
            "Prévision",
            "Comparaison hors apprentissage à des références simples",
            f"{t['fc_summary'].attrs['n_test']} mois de validation",
            "Test exécuté ; portée exploratoire"
        ],
        [
            "Outil",
            "Sélection dans Excel 365 sans macros",
            "Validation manuelle non renseignée ici",
            "À confirmer par Iman"
        ]
    ], columns=[
        "Axe", "Critère fixé avant l'analyse",
        "Résultat mesuré", "Statut"
    ])


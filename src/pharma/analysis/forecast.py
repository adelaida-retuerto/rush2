import pandas as pd

def prevoir_holt_winters(historique):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # Utiliser jusqu'à 36 mois de ventes antérieures
    donnees = historique.tail(36).copy()
    donnees.index = donnees.index.to_period("M").to_timestamp()
    donnees = donnees.asfreq("MS")

    if len(donnees) < 36:
        raise ValueError("Holt-Winters nécessite ici 36 mois d'historique.")

    if donnees.isna().any().any():
        raise ValueError("Mois ou quantités manquants dans l'historique.")

    predictions = {}

    for groupe in donnees.columns:
        modele = ExponentialSmoothing(
            donnees[groupe],
            trend="add",
            damped_trend=True,
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated"
        )

        ajustement = modele.fit(optimized=True)
        predictions[groupe] = max(
            0.0, float(ajustement.forecast(1).iloc[0])
        )

    return pd.Series(predictions)

def evaluer_methodes(ventes, dates):
    lignes = []

    for date in dates:
        historique = ventes.loc[ventes.index < date].tail(24)

        predictions = {
            "Mois précédent": historique.iloc[-1],
            "Moyenne 3 mois": historique.tail(3).mean(),
            "Même mois N-1": historique.loc[
                date - pd.DateOffset(years=1)
            ],
            "Moyenne même mois sur 2 ans": historique.loc[
                historique.index.month == date.month
            ].mean()
        }

        for methode, prediction in predictions.items():
            for groupe in ventes.columns:
                reel = ventes.loc[date, groupe]
                prevu = prediction[groupe]

                lignes.append({
                    "Date": date,
                    "Groupe": groupe,
                    "Méthode": methode,
                    "Réel": reel,
                    "Prévu": prevu,
                    "Erreur absolue": abs(reel - prevu)
                })

    return pd.DataFrame(lignes)

def backtest_quatre_methodes(monthly):
    # Normaliser les dates pour retrouver le même mois de l'année précédente
    ventes = monthly.copy().sort_index()
    ventes.index = ventes.index.to_period("M").to_timestamp()

    if len(ventes) < 48:
        raise ValueError(
            "Il faut au moins 48 mois pour ce protocole de test."
        )

    references = [
        "Mois précédent",
        "Moyenne 3 mois",
        "Même mois N-1"
    ]

    # Choisir les méthodes avant la période de validation
    selection = evaluer_methodes(ventes, ventes.index[-24:-12])
    scores_selection = selection.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )

    choix = scores_selection.idxmin(axis=1)
    choix_reference = scores_selection[references].idxmin(axis=1)

    # Tester les choix sur les 12 derniers mois
    detail = evaluer_methodes(ventes, ventes.index[-12:])
    scores = detail.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )

    bilan = pd.DataFrame(index=scores.index)
    bilan["Méthode choisie avant validation"] = choix
    bilan["Référence choisie avant validation"] = choix_reference
    bilan["MAE méthode"] = [
        scores.loc[g, choix[g]] for g in bilan.index
    ]
    bilan["MAE référence"] = [
        scores.loc[g, choix_reference[g]] for g in bilan.index
    ]
    bilan["Gain (%)"] = (
        1 - bilan["MAE méthode"] / bilan["MAE référence"]
    ) * 100
    bilan["Erreur relative (%)"] = (
        bilan["MAE méthode"]
        / ventes.tail(12).mean().replace(0, float("nan"))
    ) * 100

    bilan.attrs.update({
        "n_test": 12,
        "test_start": ventes.index[-12],
        "test_end": ventes.index[-1],
        "scores_selection": scores_selection
    })

    return detail, bilan

def next_month_forecast(monthly, detail, bilan):
    ventes = monthly.copy().sort_index()
    ventes.index = ventes.index.to_period("M").to_timestamp()

    date_future = ventes.index.max() + pd.DateOffset(months=1)
    historique = ventes.tail(24)

    predictions = {
        "Mois précédent": historique.iloc[-1],
        "Moyenne 3 mois": historique.tail(3).mean(),
        "Même mois N-1": historique.loc[
            date_future - pd.DateOffset(years=1)
        ],
        "Moyenne même mois sur 2 ans": historique.loc[
            historique.index.month == date_future.month
        ].mean()
    }

    predictions["Holt-Winters"] = prevoir_holt_winters(ventes)
    choix = bilan["Méthode choisie avant validation"]

    erreurs = detail.loc[
        detail["Méthode"] == detail["Groupe"].map(choix)
    ]
    marges = erreurs.groupby("Groupe")[
        "Erreur absolue"
    ].quantile(0.90)

    lignes = []
    for groupe in ventes.columns:
        methode = choix[groupe]
        prevu = predictions[methode][groupe]
        marge = marges[groupe]

        lignes.append({
            # Date de fin de mois conformément au contrat commun
            "Date": date_future + pd.offsets.MonthEnd(0),
            "Groupe": groupe,
            "Méthode": methode,
            "Quantité prévue": prevu,
            "MAE de validation": bilan.loc[groupe, "MAE méthode"],
            "Marge indicative": marge,
            "Borne basse indicative": max(0, prevu - marge),
            "Borne haute indicative": prevu + marge
        })

    return pd.DataFrame(lignes)

def demand_regularity(c):
    from .. import config

    ventes_jour = c.daily[config.GROUP_CODES]

    resultat = pd.DataFrame({
        "Groupe": config.GROUP_CODES,
        "Libellé": [
            config.GROUPS[g] for g in config.GROUP_CODES
        ],
        "Moyenne par jour": ventes_jour.mean().values,
        "Écart-type par jour": ventes_jour.std().values,
        "Coef. de variation": (
            ventes_jour.std()
            / ventes_jour.mean().replace(0, float("nan"))
        ).values,
        "P95 par jour": ventes_jour.quantile(0.95).values,
        "Max par jour": ventes_jour.max().values,
        "Part de jours sans vente": (
            ventes_jour.eq(0).mean()
        ).values
    })

    return resultat

def backtest(monthly):
    detail, bilan = bilan_cinq_methodes(monthly)

    bilan = bilan.rename(columns={
        "Méthode sélectionnée": "Méthode choisie avant validation",
        "Référence sélectionnée": "Référence choisie avant validation",
    })

    dates = pd.DatetimeIndex(sorted(detail["Date"].unique()))
    bilan.attrs.update({
        "n_test": len(dates),
        "test_start": dates.min(),
        "test_end": dates.max(),
    })

    # Volume moyen par jour calendaire sur les mois de validation
    reels = detail.drop_duplicates(["Date", "Groupe"]).copy()
    reels["Jours du mois"] = reels["Date"].dt.days_in_month

    volumes = reels.groupby("Groupe").agg(
        quantite_totale=("Réel", "sum"),
        jours_totaux=("Jours du mois", "sum")
    )

    bilan["Moyenne par jour sur validation"] = (
        volumes["quantite_totale"] / volumes["jours_totaux"]
    )
    return detail, bilan

def business_value(bilan):
    lignes = []

    for groupe, resultat in bilan.iterrows():
        gain = (
            resultat["MAE référence"] - resultat["MAE méthode"]
        )

        if gain > 0:
            verdict = "Gain observé ; utilité à confirmer"
            methode = resultat["Méthode choisie avant validation"]
        elif gain < 0:
            verdict = "Modèle moins précis que la référence"
            methode = resultat["Référence choisie avant validation"]
        else:
            verdict = "Référence simple retenue"
            methode = resultat["Référence choisie avant validation"]

        lignes.append({
            "Groupe": groupe,
            "Verdict : prévisible ?": verdict,
            "Méthode recommandée": methode,
            "Erreur évitée par le modèle (unités/mois)": gain,
                       "Équivalent en jours de vente": (
                gain / resultat["Moyenne par jour sur validation"]
                if resultat["Moyenne par jour sur validation"] > 0
                else None
            )
        })

    return pd.DataFrame(lignes)

def previsions_recommandees(monthly, detail, bilan):
    # Conserver le bilan de validation original
    bilan_recommande = bilan.copy()
    recommandations = business_value(bilan).set_index("Groupe")

    scores = detail.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )

    for groupe in bilan_recommande.index:
        methode = recommandations.loc[groupe, "Méthode recommandée"]

        bilan_recommande.loc[
            groupe, "Méthode choisie avant validation"
        ] = methode

        bilan_recommande.loc[groupe, "MAE méthode"] = scores.loc[
            groupe, methode
        ]

    return next_month_forecast(
        monthly, detail, bilan_recommande
    )

def comparer_holt_winters(ventes):
    ventes = ventes.copy().sort_index()
    ventes.index = ventes.index.to_period("M").to_timestamp()
    dates_test = ventes.index[-12:]

    # Résultats des quatre méthodes déjà testées
    detail = evaluer_methodes(ventes, dates_test)
    lignes = []

    for date in dates_test:
        historique = ventes.loc[ventes.index < date]
        predictions = prevoir_holt_winters(historique)

        for groupe in ventes.columns:
            reel = ventes.loc[date, groupe]
            prevu = predictions[groupe]

            lignes.append({
                "Date": date,
                "Groupe": groupe,
                "Méthode": "Holt-Winters",
                "Réel": reel,
                "Prévu": prevu,
                "Erreur absolue": abs(reel - prevu)
            })

    detail = pd.concat(
        [detail, pd.DataFrame(lignes)],
        ignore_index=True
    )

    scores = detail.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )

    return detail, scores

def selection_holt_winters(ventes):
    ventes = ventes.copy().sort_index()
    ventes.index = ventes.index.to_period("M").to_timestamp()

    lignes = []

    for date in ventes.index[-24:-12]:
        historique = ventes.loc[ventes.index < date]
        predictions = prevoir_holt_winters(historique)

        for groupe in ventes.columns:
            lignes.append({
                "Groupe": groupe,
                "Erreur absolue": abs(
                    ventes.loc[date, groupe] - predictions[groupe]
                )
            })

    return pd.DataFrame(lignes).groupby("Groupe")[
        "Erreur absolue"
    ].mean()

def bilan_cinq_methodes(ventes):
    _, ancien_bilan = backtest_quatre_methodes(ventes)
    selection = ancien_bilan.attrs["scores_selection"].copy()
    selection["Holt-Winters"] = selection_holt_winters(ventes)

    detail, scores_validation = comparer_holt_winters(ventes)

    references = [
        "Mois précédent",
        "Moyenne 3 mois",
        "Même mois N-1"
    ]

    choix = selection.idxmin(axis=1)
    choix_reference = selection[references].idxmin(axis=1)

    bilan = pd.DataFrame(index=selection.index)
    bilan["Méthode sélectionnée"] = choix
    bilan["Référence sélectionnée"] = choix_reference

    bilan["MAE méthode"] = [
        scores_validation.loc[g, choix[g]]
        for g in bilan.index
    ]
    bilan["MAE référence"] = [
        scores_validation.loc[g, choix_reference[g]]
        for g in bilan.index
    ]

    bilan["Gain (%)"] = (
        1 - bilan["MAE méthode"] / bilan["MAE référence"]
    ) * 100

    bilan["Erreur relative (%)"] = (
        bilan["MAE méthode"]
        / ventes.sort_index().tail(12).mean().replace(0, float("nan"))
    ) * 100

    return detail, bilan

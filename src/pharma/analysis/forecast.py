from pathlib import Path
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

def main():
    racine = Path(__file__).resolve().parents[3]
    
    groupes = [
        "M01AB", "M01AE", "N02BA", "N02BE",
        "N05B", "N05C", "R03", "R06"
    ]
    
    table = pd.read_csv(
        racine / "data" / "processed" / "ventes_mois.csv"
    )
    
    dates = pd.PeriodIndex(table["mois"], freq="M").to_timestamp()
    
    ventes = table[groupes].copy()
    
    ventes.index = dates
    
    ventes.index.name = "Date"
    
    ventes = ventes.sort_index()
    
    apprentissage = ventes.iloc[:-12]
    
    test = ventes.iloc[-12:]
    
    print("Mois disponibles :", len(ventes))
    
    print("\nHistorique initial :", len(apprentissage), "mois")
    
    print(apprentissage.index.min(), "→", apprentissage.index.max())
    
    print("\nPériode de test :", len(test), "mois")
    
    print(test.index.min(), "→", test.index.max())
    
    resultats = []
    
    for date_test in test.index:
        historique = ventes.loc[ventes.index < date_test]
    
        predictions = {
            "Mois précédent": historique.iloc[-1],
            "Même mois N-1": ventes.loc[
                date_test - pd.DateOffset(years=1)
            ],
            "Moyenne 3 mois": historique.tail(3).mean()
        }
    
        for methode, prediction in predictions.items():
            for groupe in ventes.columns:
                reel = ventes.loc[date_test, groupe]
                prevu = prediction[groupe]
    
                resultats.append({
                    "Date": date_test,
                    "Groupe": groupe,
                    "Méthode": methode,
                    "Réel": reel,
                    "Prévu": prevu,
                    "Erreur absolue": abs(reel - prevu)
                })
    
    resultats = pd.DataFrame(resultats)
    
    scores = resultats.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )
    
    print("\nErreur moyenne absolue (MAE), en quantités :")
    
    print(scores.round(2).to_string())
    
    resultats_modele = []
    
    for date_test in test.index:
        # Utiliser uniquement les 24 mois précédant le mois à prévoir
        historique = ventes.loc[
            (ventes.index < date_test)
            & (ventes.index >= date_test - pd.DateOffset(months=24))
        ]
    
        memes_mois = historique.loc[
            historique.index.month == date_test.month
        ]
        prediction = memes_mois.mean()
    
        for groupe in ventes.columns:
            reel = ventes.loc[date_test, groupe]
            prevu = prediction[groupe]
    
            resultats_modele.append({
                "Date": date_test,
                "Groupe": groupe,
                "Méthode": "Moyenne même mois sur 2 ans",
                "Réel": reel,
                "Prévu": prevu,
                "Erreur absolue": abs(reel - prevu)
            })
    
    comparaison = pd.concat(
        [resultats, pd.DataFrame(resultats_modele)],
        ignore_index=True
    )
    
    scores_complets = comparaison.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )
    
    print("\nComparaison des quatre méthodes — MAE :")
    
    print(scores_complets.round(2).to_string())
    
    references = [
        "Mois précédent",
        "Moyenne 3 mois",
        "Même mois N-1"
    ]
    
    bilan = pd.DataFrame(index=scores_complets.index)
    
    bilan["Référence retenue"] = scores_complets[references].idxmin(axis=1)
    
    bilan["MAE référence"] = scores_complets[references].min(axis=1)
    
    bilan["MAE méthode 2 ans"] = scores_complets[
        "Moyenne même mois sur 2 ans"
    ]
    
    bilan["Gain (%)"] = (
        1 - bilan["MAE méthode 2 ans"] / bilan["MAE référence"]
    ) * 100
    
    volumes_moyens = test.mean()
    
    bilan["Erreur relative méthode 2 ans (%)"] = (
        bilan["MAE méthode 2 ans"]
        / volumes_moyens.replace(0, float("nan"))
    ) * 100
    
    print("\nBilan par groupe :")
    
    print(bilan.round(2).to_string())
    
    selection = evaluer_methodes(ventes, ventes.index[-24:-12])
    
    scores_selection = selection.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )
    
    methodes_choisies = scores_selection.idxmin(axis=1)
    
    references_choisies = scores_selection[references].idxmin(axis=1)
    
    validation = evaluer_methodes(ventes, ventes.index[-12:])
    
    scores_validation = validation.pivot_table(
        index="Groupe",
        columns="Méthode",
        values="Erreur absolue",
        aggfunc="mean"
    )
    
    bilan_final = pd.DataFrame(index=scores_validation.index)
    
    bilan_final["Méthode choisie avant validation"] = methodes_choisies
    
    bilan_final["Référence choisie avant validation"] = references_choisies
    
    bilan_final["MAE méthode"] = [
        scores_validation.loc[g, methodes_choisies[g]]
        for g in bilan_final.index
    ]
    
    bilan_final["MAE référence"] = [
        scores_validation.loc[g, references_choisies[g]]
        for g in bilan_final.index
    ]
    
    bilan_final["Gain (%)"] = (
        1 - bilan_final["MAE méthode"] / bilan_final["MAE référence"]
    ) * 100
    
    bilan_final["Erreur relative (%)"] = (
        bilan_final["MAE méthode"] / test.mean().replace(0, float("nan"))
    ) * 100
    
    print("\nValidation avec méthodes fixées à l'avance :")
    
    print(bilan_final.round(2).to_string())
    
    date_future = ventes.index.max() + pd.DateOffset(months=1)
    
    historique = ventes.tail(24)
    
    predictions_futures = {
        "Mois précédent": historique.iloc[-1],
        "Moyenne 3 mois": historique.tail(3).mean(),
        "Même mois N-1": historique.loc[
            date_future - pd.DateOffset(years=1)
        ],
        "Moyenne même mois sur 2 ans": historique.loc[
            historique.index.month == date_future.month
        ].mean()
    }
    
    prevision_finale = pd.DataFrame([
        {
            "Date": date_future,
            "Groupe": groupe,
            "Méthode": methodes_choisies[groupe],
            "Quantité prévue": predictions_futures[
                methodes_choisies[groupe]
            ][groupe],
            "MAE de validation": bilan_final.loc[groupe, "MAE méthode"]
        }
        for groupe in ventes.columns
    ])
    
    print("\nPrévision du mois suivant le dernier mois complet :")
    
    print(prevision_finale.to_string(index=False, float_format="%.2f"))
    
    erreurs_retenues = validation.loc[
        validation["Méthode"] == validation["Groupe"].map(methodes_choisies)
    ].copy()
    
    marges = erreurs_retenues.groupby("Groupe")["Erreur absolue"].quantile(0.90)
    
    prevision_finale["Marge indicative"] = prevision_finale["Groupe"].map(marges)
    
    prevision_finale["Borne basse indicative"] = (
        prevision_finale["Quantité prévue"]
        - prevision_finale["Marge indicative"]
    ).clip(lower=0)
    
    prevision_finale["Borne haute indicative"] = (
        prevision_finale["Quantité prévue"]
        + prevision_finale["Marge indicative"]
    )
    
    print("\nPrévisions avec fourchettes indicatives :")
    
    print(prevision_finale.to_string(index=False, float_format="%.2f"))
    
    dossier_sortie = racine / "reports"
    
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    
    prevision_finale.to_csv(
        dossier_sortie / "previsions_octobre_2019.csv",
        index=False,
        date_format="%Y-%m-%d"
    )
    
    with pd.ExcelWriter(
        dossier_sortie / "controle_prevision_jeanne.xlsx",
        engine="openpyxl"
    ) as writer:
        scores_selection.to_excel(writer, sheet_name="Choix_methodes")
        bilan_final.to_excel(writer, sheet_name="Validation")
        prevision_finale.to_excel(
            writer, sheet_name="Prevision", index=False
        )
        validation.to_excel(
            writer, sheet_name="Detail_test", index=False
        )
    
    print("\nRésultats enregistrés dans :", dossier_sortie)
    
    print("previsions_octobre_2019.csv")
    
    print("controle_prevision_jeanne.xlsx")
    
    assert len(validation) == 12 * 8 * 4, \
        "Nombre de résultats de validation inattendu."
    
    assert not validation.duplicated(
        ["Date", "Groupe", "Méthode"]
    ).any(), "Une prévision apparaît plusieurs fois."
    
    assert validation[["Réel", "Prévu", "Erreur absolue"]].notna().all().all(), \
        "Une valeur manque dans la validation."
    
    assert len(prevision_finale) == 8, \
        "Il faut une prévision par groupe."
    
    assert prevision_finale["Groupe"].is_unique, \
        "Un groupe apparaît plusieurs fois."
    
    assert (
        prevision_finale["Borne basse indicative"]
        <= prevision_finale["Quantité prévue"]
    ).all(), "Une borne basse dépasse la prévision."
    
    assert (
        prevision_finale["Quantité prévue"]
        <= prevision_finale["Borne haute indicative"]
    ).all(), "Une borne haute est inférieure à la prévision."
    
    print("\nContrôles réussis : prévisions complètes et fourchettes cohérentes.")
    
    detail_fonction, bilan_fonction = backtest_quatre_methodes(ventes)

    pd.testing.assert_frame_equal(bilan_fonction, bilan_final)
    
    print("Fonction backtest vérifiée : résultats identiques.")
    
    prevision_fonction = next_month_forecast(
        ventes, detail_fonction, bilan_fonction
    )
    
    pd.testing.assert_frame_equal(
        prevision_fonction.drop(columns="Date"),
        prevision_finale.drop(columns="Date")
    )
    
    assert prevision_fonction["Date"].dt.is_month_end.all()
    
    print("Fonction de prévision vérifiée : résultats identiques, dates en fin de mois.")

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

if __name__ == "__main__":
    main()

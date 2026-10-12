from pathlib import Path
import pandas as pd

# Retrouver la racine du projet
racine = Path(__file__).resolve().parents[3]

# Charger les ventes mensuelles nettoyées
ventes = pd.read_csv(
    racine / "output" / "ventes_mensuelles_propres.csv",
    parse_dates=["Date"]
).set_index("Date").sort_index()

# Garder les 12 derniers mois pour tester les prévisions
apprentissage = ventes.iloc[:-12]
test = ventes.iloc[-12:]

print("Mois disponibles :", len(ventes))

print("\nHistorique initial :", len(apprentissage), "mois")
print(apprentissage.index.min(), "→", apprentissage.index.max())

print("\nPériode de test :", len(test), "mois")
print(test.index.min(), "→", test.index.max())
resultats = []

# Prévoir chaque mois test avec seulement les mois précédents
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

# MAE : moyenne des erreurs absolues sur les 12 mois test
scores = resultats.pivot_table(
    index="Groupe",
    columns="Méthode",
    values="Erreur absolue",
    aggfunc="mean"
)

print("\nErreur moyenne absolue (MAE), en quantités :")
print(scores.round(2).to_string())
# Prévision : moyenne du même mois sur les deux années précédentes
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

# Comparer toutes les méthodes sur les mêmes mois
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

# Une erreur relative comparable entre groupes
volumes_moyens = test.mean()
bilan["Erreur relative méthode 2 ans (%)"] = (
    bilan["MAE méthode 2 ans"]
    / volumes_moyens.replace(0, float("nan"))
) * 100

print("\nBilan par groupe :")
print(bilan.round(2).to_string())
def evaluer_methodes(dates):
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
                lignes.append({
                    "Date": date,
                    "Groupe": groupe,
                    "Méthode": methode,
                    "Réel": ventes.loc[date, groupe],
                    "Prévu": prediction[groupe],
                    "Erreur absolue": abs(
                        ventes.loc[date, groupe] - prediction[groupe]
                    )
                })

    return pd.DataFrame(lignes)


# Choisir les méthodes sur les 12 mois précédant le test final
selection = evaluer_methodes(ventes.index[-24:-12])

scores_selection = selection.pivot_table(
    index="Groupe",
    columns="Méthode",
    values="Erreur absolue",
    aggfunc="mean"
)

methodes_choisies = scores_selection.idxmin(axis=1)
references_choisies = scores_selection[references].idxmin(axis=1)

# Évaluer les choix fixés sur les 12 derniers mois
validation = evaluer_methodes(ventes.index[-12:])

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
# Prévoir le mois suivant le dernier mois complet
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
# Retenir les erreurs de la méthode choisie pour chaque groupe
erreurs_retenues = validation.loc[
    validation["Méthode"] == validation["Groupe"].map(methodes_choisies)
].copy()

# Largeur fondée sur le 90e percentile des erreurs absolues
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
dossier_sortie = racine / "output"
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
# Vérifier que les quatre méthodes couvrent les 12 mois et 8 groupes
assert len(validation) == 12 * 8 * 4, \
    "Nombre de résultats de validation inattendu."

assert not validation.duplicated(
    ["Date", "Groupe", "Méthode"]
).any(), "Une prévision apparaît plusieurs fois."

assert validation[["Réel", "Prévu", "Erreur absolue"]].notna().all().all(), \
    "Une valeur manque dans la validation."

# Vérifier les prévisions finales et leurs fourchettes
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
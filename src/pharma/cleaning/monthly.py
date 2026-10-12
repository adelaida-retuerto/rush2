from pathlib import Path
import pandas as pd

# Retrouver le dossier du projet depuis ce script
racine =racine = Path(__file__).resolve().parents[3]
Path(__file__).resolve().parent.parent

# Lire le CSV brut sans le modifier
chemin = racine / "data" / "raw" / "Pharma_Ventes_Monthly.csv"
mensuel = pd.read_csv(chemin)

# Observer le contenu
print("Premières lignes :")
print(mensuel.head())

print("\nNombre de lignes et de colonnes :")
print(mensuel.shape)

print("\nTypes des colonnes :")
mensuel.info()
# Convertir le texte en dates ; une date invalide devient NaT
mensuel["Date"] = pd.to_datetime(
    mensuel["datum"],
    format="%Y-%m-%d",
    errors="coerce"
)

print("\nDates invalides :", mensuel["Date"].isna().sum())
print("Dates en double :", mensuel["Date"].duplicated().sum())
print("Dates dans l'ordre :", mensuel["Date"].is_monotonic_increasing)
print("Première date :", mensuel["Date"].min())
print("Dernière date :", mensuel["Date"].max())

# Afficher les éventuelles lignes avec une date invalide
print("\nLignes avec une date invalide :")
print(mensuel.loc[mensuel["Date"].isna()])
# Les huit colonnes de quantités attendues
groupes = [
    "M01AB", "M01AE", "N02BA", "N02BE",
    "N05B", "N05C", "R03", "R06"
]

# Comparer les mois présents à un calendrier continu
mois_presents = mensuel["Date"].dt.to_period("M")
mois_attendus = pd.period_range(
    start=mois_presents.min(),
    end=mois_presents.max(),
    freq="M"
)

mois_manquants = mois_attendus.difference(mois_presents)

print("\nMois manquants :", mois_manquants.tolist())
print("Lignes supplémentaires pour un même mois :",
      mois_presents.duplicated().sum())

# Contrôler les quantités, groupe par groupe
print("\nQuantités manquantes par groupe :")
print(mensuel[groupes].isna().sum())

print("\nQuantités négatives par groupe :")
print((mensuel[groupes] < 0).sum())
# Lire l'export horaire brut
chemin_horaire = racine / "data" / "raw" / "Pharma_Ventes_Hourly.csv"
horaire = pd.read_csv(chemin_horaire)

print("\nPremières lignes du fichier horaire :")
print(horaire.head().to_string(index=False))

print("\nDernières lignes du fichier horaire :")
print(horaire.tail().to_string(index=False))

print("\nTypes des colonnes horaires :")
horaire.info()
# Convertir les dates avec leur format exact
horaire["Date"] = pd.to_datetime(
    horaire["datum"],
    format="%m/%d/%Y %H:%M",
    errors="coerce"
)

print("\nDates horaires invalides :", horaire["Date"].isna().sum())
print("Dates horaires en double :", horaire["Date"].duplicated().sum())
print("Dates horaires dans l'ordre :",
      horaire["Date"].is_monotonic_increasing)
print("Début de l'historique :", horaire["Date"].min())
print("Fin de l'historique :", horaire["Date"].max())

# Vérifier les colonnes de calendrier
print("\nIncohérences Year :",
      (horaire["Date"].dt.year != horaire["Year"]).sum())
print("Incohérences Month :",
      (horaire["Date"].dt.month != horaire["Month"]).sum())
print("Incohérences Hour :",
      (horaire["Date"].dt.hour != horaire["Hour"]).sum())
print("Incohérences Weekday Name :",
      (horaire["Date"].dt.day_name() != horaire["Weekday Name"]).sum())
# Construire la liste des heures entre le début et la fin de l'export
heures_attendues = pd.date_range(
    start=horaire["Date"].min(),
    end=horaire["Date"].max(),
    freq="h"
)

heures_absentes = heures_attendues.difference(
    pd.DatetimeIndex(horaire["Date"])
)

print("\nNombre d'heures absentes :", len(heures_absentes))
print("Premières heures absentes :", heures_absentes[:10].tolist())

# Vérifier les quantités utilisées pour recalculer les mois
print("\nQuantités horaires manquantes par groupe :")
print(horaire[groupes].isna().sum())

print("\nQuantités horaires négatives par groupe :")
print((horaire[groupes] < 0).sum())
# Additionner les quantités horaires pour chaque mois
horaire["Mois"] = horaire["Date"].dt.to_period("M")
mensuel_recalcule = horaire.groupby("Mois")[groupes].sum()

# Associer chaque ligne du fichier mensuel à son mois
mensuel["Mois"] = mensuel["Date"].dt.to_period("M")
mensuel_original = mensuel.set_index("Mois")[groupes]

# Vérifier que les deux tableaux couvrent les mêmes mois
if not mensuel_original.index.equals(mensuel_recalcule.index):
    raise ValueError("Les deux exports ne couvrent pas les mêmes mois.")

# Écart = quantité du CSV mensuel moins quantité recalculée
ecarts = mensuel_original - mensuel_recalcule

# Ignorer uniquement les minuscules écarts de calcul décimal
cellules_en_ecart = ecarts.abs() > 0.000001
mois_en_ecart = cellules_en_ecart.any(axis=1)

print("\nNombre de mois comparés :", len(ecarts))
print("Nombre de mois avec un écart :", mois_en_ecart.sum())

print("\nNombre d'écarts par groupe :")
print(cellules_en_ecart.sum())

print("\nÉcarts des 10 premiers mois concernés :")
print(ecarts.loc[mois_en_ecart].head(10).to_string())
# Compter les heures présentes dans chaque mois
heures_presentes = horaire.groupby("Mois").size()

# Calculer le nombre d'heures attendu pour un mois entier
heures_attendues_par_mois = pd.Series(
    mensuel_recalcule.index.days_in_month * 24,
    index=mensuel_recalcule.index
)

# Un mois est complet si toutes ses heures sont présentes
mois_complets = heures_presentes == heures_attendues_par_mois

controle_couverture = pd.DataFrame({
    "Heures présentes": heures_presentes,
    "Heures attendues": heures_attendues_par_mois,
    "Complet": mois_complets
})

print("\nMois incomplets à écarter de la prévision :")
print(controle_couverture.loc[~mois_complets].to_string())

# Conserver les quantités recalculées des mois complets
mensuel_propre = mensuel_recalcule.loc[mois_complets].copy()

print("\nNombre de mois complets conservés :", len(mensuel_propre))
print("Premier mois conservé :", mensuel_propre.index.min())
print("Dernier mois conservé :", mensuel_propre.index.max())
# Calculer un seuil de détection pour chaque groupe
q1 = mensuel_propre[groupes].quantile(0.25)
q3 = mensuel_propre[groupes].quantile(0.75)
ecart_interquartile = q3 - q1
seuils = q3 + 1.5 * ecart_interquartile

# Repérer les quantités mensuelles supérieures au seuil
pics = mensuel_propre[groupes].gt(seuils)

print("\nNombre de pics signalés par groupe :")
print(pics.sum())

# Afficher chaque pic avec son mois, sa quantité et son seuil
journal_pics = []

for mois in mensuel_propre.index:
    for groupe in groupes:
        if pics.loc[mois, groupe]:
            journal_pics.append({
                "Mois": str(mois),
                "Groupe": groupe,
                "Quantité": mensuel_propre.loc[mois, groupe],
                "Seuil": seuils[groupe]
            })

pics_signales = pd.DataFrame(
    journal_pics,
    columns=["Mois", "Groupe", "Quantité", "Seuil"]
)

print("\nDétail des pics signalés :")
print(pics_signales.round(3).to_string(index=False))
# Créer le dossier des résultats si nécessaire
dossier_sortie = racine / "data" / "processed"
dossier_sortie.mkdir(parents=True, exist_ok=True)

dossier_rapports = racine / "reports"
dossier_rapports.mkdir(parents=True, exist_ok=True)

# Préparer les données : Date puis les huit groupes ATC
table_propre = mensuel_propre.copy()
table_propre.index = table_propre.index.to_timestamp(how="start")
table_propre.index.name = "Date"
table_propre = table_propre.reset_index()

# Enregistrer les quantités recalculées, sans les arrondir
table_propre.to_csv(
    dossier_sortie / "ventes_mensuelles_propres.csv",
    index=False,
    date_format="%Y-%m-%d"
)

# Documenter les décisions dans une feuille État des données
etat_donnees = pd.DataFrame([
    {
        "Contrôle": "Comparaison mensuel / horaire",
        "Résultat": f"{int(mois_en_ecart.sum())} mois en écart sur {len(ecarts)}",
        "Décision": "Utiliser les totaux recalculés depuis l'export horaire"
    },
    {
        "Contrôle": "Couverture des mois",
        "Résultat": ", ".join(
            controle_couverture.index[~mois_complets].astype(str)
        ),
        "Décision": "Exclure ces mois incomplets de la prévision"
    },
    {
        "Contrôle": "Pics de ventes",
        "Résultat": f"{len(pics_signales)} pics signalés",
        "Décision": "Conserver les valeurs et les examiner"
    },
    {
        "Contrôle": "Unité des quantités",
        "Résultat": "Unité non documentée ; aucun prix",
        "Décision": "Parler de quantités, pas de boîtes ni d'euros"
    }
])

# Créer un classeur de contrôle pour ta partie
with pd.ExcelWriter(
    dossier_sortie / "controle_mensuel_jeanne.xlsx",
    engine="openpyxl"
) as writer:
    table_propre.to_excel(writer, sheet_name="Mensuel_propre", index=False)
    etat_donnees.to_excel(writer, sheet_name="État des données", index=False)
    ecarts.to_excel(writer, sheet_name="Écarts")
    controle_couverture.to_excel(writer, sheet_name="Couverture")
    pics_signales.to_excel(writer, sheet_name="Pics", index=False)

print("\nRésultats enregistrés dans :", dossier_sortie)
print("ventes_mensuelles_propres.csv")
print("controle_mensuel_jeanne.xlsx")
# Relire le fichier enregistré
verification = pd.read_csv(
    dossier_sortie / "ventes_mensuelles_propres.csv",
    parse_dates=["Date"]
)

# Comparer le fichier relu au tableau calculé
pd.testing.assert_frame_equal(
    verification,
    table_propre,
    check_dtype=False,
    check_exact=False,
    rtol=1e-10,
    atol=1e-6
)

# Vérifier que chaque mois conservé est complet
assert mois_complets.loc[mensuel_propre.index].all(), \
    "Un mois incomplet a été conservé."

# Vérifier la continuité des mois conservés
calendrier = pd.period_range(
    mensuel_propre.index.min(),
    mensuel_propre.index.max(),
    freq="M"
)

assert mensuel_propre.index.equals(calendrier), \
    "Il manque un mois dans les données propres."

print("\nVérifications réussies : CSV fidèle et mois complets consécutifs.")

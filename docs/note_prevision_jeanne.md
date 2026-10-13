# Partie 1 — Peut-on prévoir les ventes du mois suivant ?

## Réponse

Les données permettent de produire des estimations mensuelles,
avec une précision variable selon les groupes. Leur utilité pour les
commandes dépend de l’erreur acceptable pour le pharmacien.

N02BE présente le gain le plus net face à la référence sélectionnée.
Pour R03, le modèle sélectionné dégrade la précision ; nous recommandons
donc un repli vers le mois précédent.

## Données utilisées

Les ventes mensuelles sont recalculées depuis l’export horaire.
Le contrôle révèle 45 cellules en écart dans 31 des 70 mois exportés.

La prévision utilise 68 mois complets, de février 2014 à septembre 2019.
Janvier 2014 et octobre 2019 sont incomplets et exclus.
Les pics sont signalés mais conservés.

Le mois à prévoir est octobre 2019.

## Protocole

Cinq méthodes sont comparées :
- mois précédent ;
- même mois de l’année précédente ;
- moyenne des trois derniers mois ;
- moyenne du même mois sur les deux années précédentes ;
- Holt-Winters à tendance amortie et saisonnalité additive annuelle.

Les méthodes sont sélectionnées sur octobre 2017 à septembre 2018,
puis évaluées sur octobre 2018 à septembre 2019.

Chaque prévision utilise uniquement les ventes antérieures au mois prévu.
Holt-Winters utilise jusqu’à 36 mois d’historique.

L’erreur est mesurée par la MAE : moyenne des écarts absolus entre
prévisions et ventes réelles.

## Principaux résultats

Pour N02BE, Holt-Winters réduit la MAE d’environ 49,9 % face à la
référence sélectionnée. La réduction d’erreur représente environ
3,81 jours de ventes moyennes, sans constituer une économie de stock
constatée.

Pour R06, la moyenne saisonnière sur deux ans apporte un gain
d’environ 9,1 %, avec une erreur relative d’environ 23,8 %.

Pour R03, Holt-Winters dégrade la MAE d’environ 23,7 %.
La recommandation finale revient au mois précédent.
Ce repli est décidé après validation et n’a pas été évalué
sur une nouvelle période indépendante.

Pour les cinq autres groupes, une référence simple est retenue.
Cela ne signifie pas que leurs ventes sont imprévisibles.

## Limites

La validation couvre seulement 12 mois, déjà observés pendant
l’exploration : l’analyse reste exploratoire.

Les fourchettes calculées sont indicatives. Aucune couverture future
à 80 % ou 90 % n’est démontrée ; aucune p-valeur n’est annoncée.

Holt-Winters présente une sensibilité numérique aux arrondis.
Les résultats livrés utilisent les données du nettoyage en mémoire.

Les données de grippe sont analysées dans le projet, mais ne sont
pas intégrées à ces modèles de prévision.

Les quantités ont une unité non documentée. Aucun prix ni stock
n’est disponible : nous ne pouvons pas calculer une économie financière.

## Recommandation

Utiliser les prévisions comme aide à la décision, avec contrôle humain.
Relancer le programme à chaque nouvel export et suivre les erreurs
sur les nouveaux mois avant d’automatiser les commandes.

## Résultats détaillés générés

Les scores portent sur la méthode sélectionnée avant validation. La méthode recommandée peut différer après le repli vers la référence.

| Groupe   | Méthode testée sélectionnée   | Méthode recommandée         |   MAE méthode testée |   MAE référence |   Gain (%) |   Erreur relative (%) |
|:---------|:------------------------------|:----------------------------|---------------------:|----------------:|-----------:|----------------------:|
| M01AB    | Moyenne 3 mois                | Moyenne 3 mois              |                16.29 |           16.29 |       0.00 |                  9.92 |
| M01AE    | Moyenne 3 mois                | Moyenne 3 mois              |                21.99 |           21.99 |       0.00 |                 18.40 |
| N02BA    | Mois précédent                | Mois précédent              |                11.85 |           11.85 |       0.00 |                 12.40 |
| N02BE    | Holt-Winters                  | Holt-Winters                |               119.22 |          237.85 |      49.88 |                 12.58 |
| N05B     | Moyenne 3 mois                | Moyenne 3 mois              |                25.30 |           25.30 |       0.00 |                  9.57 |
| N05C     | Moyenne 3 mois                | Moyenne 3 mois              |                 6.03 |            6.03 |       0.00 |                 26.89 |
| R03      | Holt-Winters                  | Mois précédent              |                80.02 |           64.68 |     -23.72 |                 32.41 |
| R06      | Moyenne même mois sur 2 ans   | Moyenne même mois sur 2 ans |                25.01 |           27.50 |       9.07 |                 23.79 |

### Prévisions d’octobre 2019

Fourchettes indicatives, sans garantie de couverture.

| Groupe   |   Quantité prévue |   Borne basse indicative |   Borne haute indicative |
|:---------|------------------:|-------------------------:|-------------------------:|
| M01AB    |            174.66 |                   148.76 |                   200.56 |
| M01AE    |            101.08 |                    57.05 |                   145.11 |
| N02BA    |             93.50 |                    68.22 |                   118.78 |
| N02BE    |           1289.19 |                   958.61 |                  1619.76 |
| N05B     |            238.47 |                   192.04 |                   284.89 |
| N05C     |             20.67 |                     8.73 |                    32.60 |
| R03      |            121.42 |                     0.00 |                   274.28 |
| R06      |             64.45 |                    14.36 |                   114.54 |

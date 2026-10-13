# Deck manager — Analyse des ventes pharmaceutiques

## Slide 1 — Une analyse relançable pour une mission de suivi
- Objectif : fiabiliser les ventes et tester leur prévisibilité.
- 8 groupes de médicaments, 68 mois complets analysés.
- Un programme régénère les analyses et le classeur.

À dire — 40 secondes :
« Nous proposons un suivi mensuel fondé sur des données contrôlées.
La prévision est une aide à la décision, avec une précision variable
selon les groupes. »

## Slide 2 — Contrôler les données avant de conclure
- 45 cellules en écart dans 31 des 70 mois exportés.
- Totaux reconstruits depuis les ventes horaires.
- Janvier 2014 et octobre 2019 incomplets : exclus de la prévision.
- Pics signalés et conservés.

À dire — 50 secondes :
« Un fichier lisible n’est pas forcément cohérent.
Nous avons comparé les exports, documenté les écarts et conservé
les données brutes pour pouvoir refaire les contrôles. »

## Slide 3 — Tester les prévisions sur des mois futurs simulés
- 5 méthodes, dont 3 références simples.
- Sélection : octobre 2017 à septembre 2018.
- Validation : octobre 2018 à septembre 2019.
- Chaque prévision utilise seulement les ventes antérieures.

À dire — 60 secondes :
« Nous comparons les prévisions aux ventes réellement observées.
La mesure principale est la MAE : l’erreur moyenne en quantités.
Le choix initial et sa performance en validation restent distincts. »

## Slide 4 — Des résultats différents selon les groupes
- N02BE : Holt-Winters réduit l’erreur d’environ 49,9 %.
- R06 : gain d’environ 9,1 %, erreur relative d’environ 23,8 %.
- R03 : modèle moins précis ; repli vers le mois précédent.
- Pour les cinq autres groupes, une référence simple est retenue.

À dire — 70 secondes :
« Il n’y a pas une méthode gagnante pour tous les groupes.
Le gain de N02BE équivaut à environ 3,81 jours de ventes moyennes,
sans démontrer une économie de stock.
Nous conservons aussi les résultats défavorables. »

## Slide 5 — Proposer un suivi pilote et mesurer sa valeur
- Relancer les contrôles et le classeur à chaque nouvel export.
- Suivre les erreurs sur les nouveaux mois.
- Faire valider les décisions d’achat par le pharmacien.
- Limites : 12 mois de validation, analyse exploratoire,
  sensibilité numérique de Holt-Winters, fourchettes indicatives.

À dire — 60 secondes :
« Nous recommandons une mission pilote avec suivi des erreurs.
Le classeur complet a passé 56 contrôles de conformité au modèle.
La prochaine étape est de mesurer l’utilité opérationnelle
sur de nouvelles données, avant d’automatiser les commandes. »

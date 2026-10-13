# Notes orales — Deck manager (5 minutes)

Support : `deck_manager_jeanne.pdf` (5 slides). Durée cible : 4 min 40, ce qui laisse
20 secondes de marge. Rythme : environ 130 mots par minute, sans lire la slide.

| Slide | Message | Temps | Cumul |
|---|---|---|---|
| 1 | Une analyse relançable pour un suivi mensuel | 0:40 | 0:40 |
| 2 | Contrôler les données avant de conclure | 0:50 | 1:30 |
| 3 | Tester sur des mois futurs simulés | 1:00 | 2:30 |
| 4 | Des résultats différents selon les groupes | 1:10 | 3:40 |
| 5 | Proposer un pilote et mesurer sa valeur | 1:00 | 4:40 |

---

## Slide 1 — Une analyse relançable pour un suivi mensuel (40 s)

« Notre objectif était double : fiabiliser les ventes de la pharmacie,
puis tester si on peut prévoir le mois suivant.
Nous avons travaillé sur 8 groupes de médicaments et 68 mois complets,
de février 2014 à septembre 2019 : ce sont des ventes historiques.
Tout est produit par un programme qu'on relance à chaque export.
Notre proposition : un suivi mensuel fondé sur des données contrôlées.
La prévision y reste une aide à la décision, avec une précision
qui varie selon les groupes. »

*Transition :* « Avant de prévoir quoi que ce soit, il fallait pouvoir faire confiance aux chiffres. »

## Slide 2 — Contrôler les données avant de conclure (50 s)

« Un fichier lisible n'est pas forcément cohérent.
En comparant les exports, nous avons trouvé 45 cellules en écart,
réparties sur 31 des 70 mois exportés.
Nous avons donc reconstruit les totaux mensuels à partir des ventes horaires,
et documenté chaque écart.
Deux mois sont incomplets, janvier 2014 et octobre 2019 :
ils sont exclus de la prévision. Il reste 68 mois complets.
Les pics sont signalés mais conservés, parce que ce sont de vraies ventes.
Et nous gardons les données brutes pour pouvoir refaire les contrôles. »

*Transition :* « Sur cette base propre, comment savoir si une prévision est bonne ? »

## Slide 3 — Tester les prévisions sur des mois futurs simulés (60 s)

« Nous avons simulé l'avenir : chaque prévision n'utilise que les ventes
antérieures au mois prévu.
Nous comparons cinq méthodes : trois références simples — le mois précédent,
le même mois l'an dernier, la moyenne des trois derniers mois —
et deux méthodes saisonnières : la moyenne du même mois sur deux ans,
et Holt-Winters.
La méthode est choisie sur une première année, d'octobre 2017 à septembre 2018,
puis évaluée sur l'année suivante, jusqu'en septembre 2019.
La mesure principale est la MAE : l'erreur moyenne, en quantités vendues.
Point important : le choix initial et sa performance en validation restent distincts. »

*Transition :* « Et le résultat dépend beaucoup du groupe. »

## Slide 4 — Des résultats différents selon les groupes (70 s)

« Il n'y a pas de méthode gagnante pour tous les groupes.
Pour N02BE, le paracétamol, Holt-Winters réduit l'erreur d'environ 49,9 %
face à la référence simple.
Cette réduction équivaut à environ 3,81 jours de ventes moyennes —
c'est une façon de lire l'erreur, pas des jours de stock économisés :
nous n'avons ni prix ni stock.
Pour R06, les antihistaminiques, la moyenne saisonnière gagne environ 9,1 %,
avec une erreur relative encore d'environ 23,8 %.
Pour R03, l'asthme, Holt-Winters avait été sélectionné, mais il est
moins précis en validation, d'environ 23,7 %. Nous recommandons donc
un repli vers le mois précédent — décidé après validation, donc pas encore
testé sur une période indépendante.
Pour les cinq autres groupes, une référence simple est conservée,
ce qui ne veut pas dire que leurs ventes sont imprévisibles.
Nous montrons aussi les résultats défavorables. »

*Transition :* « D'où notre proposition. »

## Slide 5 — Proposer un suivi pilote et mesurer sa valeur (60 s)

« Nous recommandons une mission pilote de suivi mensuel,
avec une méthode par groupe et une décision d'achat validée par le pharmacien.
Concrètement : relancer les contrôles et le classeur à chaque nouvel export —
le classeur complet passe déjà 56 contrôles de conformité au modèle —
puis suivre l'erreur sur les nouveaux mois.
Il faut être clair sur les limites : l'analyse est exploratoire,
avec seulement 12 mois de validation ; Holt-Winters est sensible
aux arrondis numériques ; les fourchettes sont indicatives,
sans garantie de couverture à 80 ou 90 %.
Et nos ventes s'arrêtent en 2019 : le pilote doit tourner sur des exports récents.
La prochaine étape est donc de mesurer l'utilité opérationnelle
sur de nouvelles données, avant d'automatiser les commandes. »

---

## Si le manager pose une question

- **« Quel gain financier ? »** — Aucun chiffrage possible : pas de prix, pas de stock,
  unité des quantités non documentée. Le pilote sert justement à mesurer l'utilité.
- **« C'est significatif ? »** — Nous n'annonçons pas de p-valeur : 12 mois de validation,
  analyse exploratoire. On le confirmera sur les nouveaux mois.
- **« Et la grippe ? »** — Les données de grippe sont analysées dans le projet,
  mais ne sont pas intégrées à ces modèles de prévision.
- **« Les fourchettes d'octobre 2019 ? »** — Indicatives seulement, sans couverture garantie
  (ex. N02BE : 1 289 prévu, de 959 à 1 620 environ).

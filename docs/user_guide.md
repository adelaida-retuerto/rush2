# Mode d'emploi du classeur : guide du pharmacien

Ce guide explique comment consulter vos ventes dans le classeur Excel livré chaque mois.
Il ne demande aucune connaissance technique.

## 1. Ouvrir le bon classeur

- Le classeur du mois s'appelle `analyse_ventes_AAAA-MM.xlsx` (par exemple `analyse_ventes_2019-09.xlsx`).
  Il est dans le dossier `deliverables/`. C'est **le seul à ouvrir** : les mois précédents sont rangés,
  intacts, dans `deliverables/archive/`.
- Il fonctionne sous **Excel 365**, **sans macros** : tout est calculé par des formules.
- Si Excel affiche un bandeau jaune « Mode protégé », cliquez sur **Activer la modification** :
  sinon les formules ne se calculent pas et les cellules restent vides.

## 2. L'outil de consultation (feuille « Outil »)

Il répond à la question : *combien ai-je vendu de tels groupes sur telle période ?*
Vous ne modifiez que les **cellules jaunes**.

### Étape 1 : choisir les groupes

Dans la colonne **« Inclure ? »**, choisissez **Oui** ou **Non** pour chacun des 8 groupes, dans la liste déroulante.
La ligne « Groupes inclus » indique combien sont sélectionnés (par exemple `3 / 8`).

| Code ATC | Groupe |
| --- | --- |
| M01AB | Anti-inflammatoires (diclofénac) |
| M01AE | Anti-inflammatoires (ibuprofène) |
| N02BA | Antalgiques (aspirine) |
| N02BE | Antalgiques (paracétamol) |
| N05B | Anxiolytiques |
| N05C | Hypnotiques et sédatifs (somnifères) |
| R03 | Médicaments de l'asthme et de la BPCO |
| R06 | Antihistaminiques (allergies) |

### Étape 2 : choisir la période

Saisissez une **date de début** et une **date de fin**. Pour un seul jour, mettez deux fois la même date.

À l'ouverture, l'outil affiche le **dernier mois complet** (par exemple du 01/09/2019 au 30/09/2019).

La cellule **« Contrôle »** vous prévient en cas de problème :

| Message | Ce que cela veut dire | Que faire |
| --- | --- | --- |
| `OK` | La période est valide | Rien |
| `Fin avant début !` | La date de fin est avant la date de début | Inverser les deux dates |
| `Hors données` | Une date sort de l'historique disponible | Rester entre les dates « Données du … au … » affichées juste en dessous |

### Étape 3 : lire les résultats

Tout se met à jour immédiatement.

- **3. Ventes sur la période** : pour chaque groupe choisi,
  - la **quantité** vendue,
  - la **moyenne par jour**,
  - la quantité de la **même période un an plus tôt** (N-1), et l'**évolution** en %,
  - la **part** du groupe dans la sélection.

  Un graphique compare les groupes sélectionnés.
- **4. Répartition par heure** : à quelles heures se font les ventes des groupes choisis, en quantité,
  en moyenne par jour et en part du total. Utile pour organiser le comptoir.
- **5. Détail dans le temps** : l'évolution sur la période, par **jour** (92 jours ou moins),
  par **semaine** (jusqu'à 92 semaines) ou par **mois** au-delà.

### Exemples

- *Combien de paracétamol en septembre ?* Mettez Oui seulement pour N02BE, période du 01/09 au 30/09.
- *Les allergies ce printemps, comparées à l'an dernier ?* Oui pour R06, période du 01/03 au 31/05 :
  lisez les colonnes « Même période N-1 » et « Évolution ».
- *Un jour précis ?* Même date en début et en fin.

## 3. Les autres feuilles à consulter

| Feuille | Ce que vous y trouvez |
| --- | --- |
| **Stats_Groupes** | Le poids de chaque groupe, sa **saison** mois par mois (indice : 1,00 = un mois habituel, 1,50 = 50 % de plus), ses mois forts et faibles, le cumul de l'année face à l'an dernier |
| **Stats_Mensuel** | Les ventes mois par mois, avec un graphique des 60 derniers mois |
| **Stats_Calendrier** | Les jours de la semaine et les heures les plus chargés |
| **Environnement** | Le lien entre la grippe (réseau Sentinelles) et les ventes |
| **État_des_données** | Ce qui a été contrôlé et corrigé dans les exports de la caisse |

## 4. Ce qu'il faut savoir sur les chiffres

- **Unité** : les quantités sont celles enregistrées par la caisse. Leur unité n'est pas documentée
  (il y a des décimales) : ce ne sont donc pas forcément des **boîtes**.
- **Jours complets seulement** : le dernier jour exporté est souvent incomplet (l'export s'arrête en cours de journée).
  Il est écarté des données de l'outil ; la note sous la période l'indique.
- **L'export mensuel de la caisse est faux** pour une partie des mois : tous les totaux mensuels du classeur
  sont recalculés à partir des ventes heure par heure. Ne pilotez pas vos achats avec l'export mensuel du logiciel.
- **Mise à jour** : chaque mois, un nouveau classeur est produit à partir des nouveaux exports.
  Ne saisissez pas de ventes à la main : elles seraient perdues le mois suivant.

## 5. Les rendez-vous d'achat conseillés

| Quand | Quoi |
| --- | --- |
| Septembre | Renforcer le stock de paracétamol et d'ibuprofène (pic d'octobre) |
| Mars | Stock et mise en avant des antihistaminiques (pic d'avril à juin) |
| Octobre | Ajuster le stock des médicaments de l'asthme (pic de décembre) |
| Chaque semaine d'hiver | Consulter le bulletin du réseau Sentinelles : au-delà d'environ 200 cas pour 100 000 habitants, prévoir environ +15 % de paracétamol |

Pour les médicaments sur ordonnance (anxiolytiques, somnifères, la plupart des médicaments de l'asthme),
on parle uniquement de **stock**, jamais de promotion.

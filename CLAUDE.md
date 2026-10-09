# Rush 2 : analyse des ventes pharmaceutiques (Bootcamp Data, Epitech MBA)

## Contexte du projet

**Sujet.** Nous sommes consultantes Data & Santé pour une pharmacie indépendante en France. Le client a exporté ~6 ans de ventes (janvier 2014 à octobre 2019) pour 8 groupes de médicaments identifiés par leur code ATC. Les quantités sont celles du logiciel de caisse : unité non documentée (décimales présentes, donc ne JAMAIS parler de « boîtes »), aucun prix.

**Groupe.** 3 personnes (Ihman, Adelaida, + 1). Rendu lundi 12 octobre 2026 après-midi, report possible au mardi. Outils imposés : Excel et Python. L'IA est autorisée, mais il faut comprendre et maîtriser son code.

**Livrables :**
- Classeur Excel (.xlsx) : feuille de synthèse, statistiques descriptives, état des données (quel export pour quoi, ce qui est corrigé ou écarté), outil de sélection.
- Code Python qui RÉGÉNÈRE les statistiques du classeur à partir des exports. Le client renverra chaque mois les 4 mêmes fichiers avec l'historique complet : le manager doit pouvoir relancer le code sans rien refaire à la main. Le code doit marcher depuis un clone neuf du repo.
- 3 decks de 5 slides max (manager, pharmacien acheteur, propriétaire), avec trois messages différents, pas trois habillages du même deck.
- Note PDF : partie 1 = réponse sur la prévision ; partie 2 = risques du partage de données.
- Le repo est un livrable : l'historique Git doit montrer la répartition du travail, le README dit qui a fait quoi, et le repo ne contient RIEN d'inutile pour le client ou le manager.

**Outil client (dans Excel).** Le pharmacien, sous Excel 365, choisit un ou plusieurs groupes et un jour ou une période, et voit immédiatement les ventes. SANS MACROS. Pistes : segments/chronologie sur un tableau croisé, ou FILTRE / SOMME.SI.ENS avec listes déroulantes. Approche retenue de préférence : Python remplit les données d'un modèle Excel dans lequel l'outil est déjà construit.

**Source externe obligatoire.** Au moins une recommandation doit s'appuyer sur des données publiques et structurées récupérées nous-mêmes et INTÉGRÉES à l'analyse (pas seulement citées). Pistes : grippe (réseau Sentinelles, Santé publique France), météo, pollens (RNSA), jours fériés et vacances. Attention aux fausses corrélations : grippe et paracétamol montent tous deux en hiver. Le test sérieux compare les hivers entre eux.

**Question de prévision.** « Peut-on prévoir, pour chaque groupe, les ventes du mois qui suit le dernier mois complet ? » Réponse possible : oui, non ou « pour certains seulement ». Elle doit reposer sur un VRAI test : prévisions sur des mois non utilisés pour construire le modèle, comparées à des prévisions naïves (mois précédent ; même mois de l'année précédente), par groupe ATC. L'allure d'une courbe n'est pas un test.

**Partage des données.** Un laboratoire propose de meilleures conditions d'achat contre l'accès à l'export. N05B et N05C (anxiété, sommeil) sont sensibles. À analyser : RGPD, secret professionnel, Code de déontologie des pharmaciens, loi anti-cadeaux, risque de réidentification selon le niveau de détail (horaire, journalier, mensuel). Au niveau horaire, N05C (~0,6 vente par jour) permet de relier une vente à une personne vue au comptoir.

**Constats déjà vérifiés sur les données (à automatiser dans le code, pas à refaire à la main) :**
- Les 4 fichiers : `datum` + 8 colonnes ATC (M01AB, M01AE, N02BA, N02BE, N05B, N05C, R03, R06). Horaire et journalier ont aussi Year, Month, Hour, Weekday Name.
- Dates au format M/J/AAAA (ex. 1/2/2014 = 2 janvier) dans horaire, journalier et hebdomadaire ; AAAA-MM-JJ dans le mensuel. Vérifié : les jours de la semaine concordent sur toutes les lignes.
- Aucune valeur manquante, aucune valeur négative, aucun jour manquant, aucun doublon.
- Horaire → journalier → hebdomadaire (semaines finissant le dimanche) concordent au centième près.
- Le MENSUEL NE CONCORDE PAS : 31 mois sur 70 ont un écart avec la somme des jours, toujours vers le haut. Octobre 2014 est faux sur tous les groupes (N02BE : 1 830 au mensuel contre 1 046 en sommant les jours). Ailleurs, une seule case fausse à chaque fois (+10 à +40 unités) ; R03 est le groupe le plus touché (12 mois). Décision : reconstruire le mensuel à partir du journalier et documenter chaque écart dans l'état des données.
- La colonne `Hour` du fichier journalier est un artefact : c'est la somme des heures de la journée (276 = 0+1+…+23 ; 248 le 1er jour qui commence à 8h ; 190 le dernier jour, coupé). À ignorer.
- Les données s'arrêtent le 08/10/2019 à 19h. Octobre 2019 est incomplet (8 jours), le dernier jour l'est aussi. La dernière semaine (au 13/10) n'a que 2 jours. Le dernier mois complet est SEPTEMBRE 2019.
- Ventes entre 7h et 22h, 7 jours sur 7, dimanches compris, aucun jour fermé (même jours fériés). Peu typique d'une officine française : le jeu ressemble à un jeu public Kaggle (pharmacie serbe, non vérifié). À signaler comme limite lors du croisement avec des données françaises.
- N05C est très rare (~0,6 par jour, nombreuses périodes de 7 à 23 jours sans vente) : prévision fragile.
- Quelques pics isolés à signaler : N02BE à 161 le 30/12/2016 et le 13/01/2017, R03 à 41 et 45, N05B à 54,8 le 11/10/2016.
- Saisonnalité nette déjà observée (moyennes 2014-2018) : R06 passe de ~51 en janvier à ~161 en mai ; N02BE est haut en hiver (~1 270 en janvier) et bas en été (~600 en juillet).

**Règles métier pour les recommandations.** Pas de « promotions » sur des médicaments sur ordonnance (N05B, N05C, la plupart des R03) : en France, le Code de déontologie interdit d'inciter à une consommation abusive de médicaments, et la publicité auprès du public est limitée aux médicaments non remboursés et sans ordonnance. Parler plutôt de stock et de mise en avant pour les médicaments sans ordonnance, et de promotions sur la parapharmacie associée.

**Rôles :**
- P1 Données & prévision : script Python, contrôles, test de prévision, dépôt Git → deck manager + note partie 1.
- P2 Excel & achats : classeur, outil de sélection, statistiques saisonnières → deck pharmacien.
- P3 Environnement & conformité : source externe, RGPD, recommandations → deck propriétaire + note partie 2.

**Charte graphique.** Polices Playfair Display (titres) et Lato (texte). Couleurs dans `src/config.py`. Toujours écrire le code ATC avec son nom (« N05B · Anxiolytiques »). Graphiques : le titre est le message, étiquettes directes plutôt que légende, pas de 3D, jamais les couleurs par défaut de matplotlib ou d'Excel.

**Règles de code :**
- Python simple et commenté en français : chaque membre doit pouvoir expliquer chaque ligne à l'oral.
- Chemins relatifs uniquement, tout doit tourner depuis un clone neuf.
- Les contrôles de cohérence sont faits dans le code à chaque exécution (le prochain export pourra avoir d'autres erreurs).
- Toutes les statistiques du classeur viennent du code, jamais saisies à la main.
- Aucun fichier inutile dans le repo (pas de notebooks brouillons, pas de fichiers de test qui traînent).
- Ne jamais push sans accord. Chaque membre committe sa propre partie depuis son propre compte.

## Environnement technique

- Python 3.14 pour tout le groupe (version de référence ; 3.12 au minimum, exigé par les versions figées de numpy et scipy). Environnement virtuel dans `.venv/`.
- Toutes les constantes (chemins, noms ATC, couleurs) sont dans `src/config.py` : les importer, ne jamais les redéfinir ailleurs.
- Les documents du cours (sujet, charte, kick-off, zip d'origine) sont dans le dossier local mais ignorés par Git.

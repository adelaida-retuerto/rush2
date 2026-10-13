# Rush 2 – Analyse des ventes d'une pharmacie

Analyse de près de six ans de ventes (janvier 2014 - octobre 2019) pour 8 groupes de médicaments (codes ATC),
à partir des 4 exports du logiciel de caisse. Chaque mois, **un double-clic** produit un classeur Excel daté
(`deliverables/analyse_ventes_AAAA-MM.xlsx`) que le pharmacien utilise seul, sans Python ni macro.

## En bref

1. **Une seule fois** : installer Python et les bibliothèques (partie « Installation »).
2. **Chaque mois** : remplacer les 4 exports dans `data/raw/`, puis **double-cliquer** sur
   `lancer_mac.command` (Mac) ou `lancer_windows.bat` (Windows).
3. Le classeur du mois s'ouvre dans Excel. Mode d'emploi pour le pharmacien : [`docs/user_guide.md`](docs/user_guide.md).

## Installation (une seule fois)

Prérequis : **Python 3.14** (3.12 au minimum) et une connexion internet pour installer les bibliothèques.
Deux méthodes au choix, qui donnent le même résultat : **conda** (utilisée par l'équipe) ou **venv**.
Le lanceur double-clic trouve tout seul l'une ou l'autre : il faut seulement que l'environnement conda s'appelle
**`rush2`**, ou que le dossier **`.venv`** soit à la racine du projet.

> Évitez les espaces dans le chemin du dossier (ex. `Rush2` plutôt que `Rush 2`). Sinon, mettez le chemin
> entre guillemets dans le terminal : `cd "…/Rush 2/rush2"`.

### Option A · conda

Installer **Miniconda** (docs.anaconda.com/miniconda ; sur Mac, version Apple Silicon ou Intel selon la machine).
Puis, dans **Terminal** (Mac) ou **Anaconda Prompt** (Windows) :

```bash
cd chemin/vers/rush2
conda create -n rush2 -c conda-forge python=3.14
conda activate rush2
pip install -r requirements.txt
python -m pytest                        # aucun « failed » = installation correcte
```

### Option B · venv

Installer **Python 3.14** depuis python.org (Windows : cocher « Add python.exe to PATH »).

**Mac** (Terminal) :

```bash
cd chemin/vers/rush2
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                        # aucun « failed »
```

**Windows** (PowerShell) :

```powershell
cd chemin\vers\rush2
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

Windows, si l'activation est refusée (« l'exécution de scripts est désactivée ») :
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, répondre `O`, puis relancer l'activation.

### Pour les notebooks (Jupyter, facultatif)

Une seule fois, environnement activé :

```bash
python -m ipykernel install --user --name rush2 --display-name "Python (rush2)"
```

Puis `jupyter lab` depuis le dossier du projet, et choisir le noyau **Python (rush2)** dans chaque notebook.

## Utilisation : le double-clic

À la racine du projet, à côté de `main.py` :

| Système | Fichier à double-cliquer |
| --- | --- |
| Mac | `lancer_mac.command` |
| Windows | `lancer_windows.bat` |

Le lanceur :

1. se place dans le dossier du projet (quel que soit l'endroit d'où on l'ouvre) ;
2. cherche le Python de l'environnement conda **`rush2`**, sinon celui du dossier **`.venv`** ;
3. lance `main.py --offline` : nettoyage et contrôle des 4 exports, analyses, classeur du mois, contrôle du classeur ;
4. ouvre dans Excel le classeur le plus récent de `deliverables/` ;
5. garde la fenêtre ouverte pour lire les messages : appuyer sur **Entrée** (Mac) ou une touche (Windows) pour la fermer.

En cas d'erreur, la fenêtre affiche le message et **aucun classeur n'est ouvert** : voir « En cas d'erreur » ci-dessous.

### Premier double-clic sur Mac : « Apple n'a pas pu confirmer… »

Si le projet a été **téléchargé** (fichier ZIP, clé USB, mail, AirDrop), macOS bloque le lanceur au premier
double-clic avec le message :

> Élément « lancer_mac.command » non ouvert. Apple n'a pas pu confirmer que « lancer_mac.command » ne contenait pas
> de logiciel malveillant…

Le fichier n'est pas dangereux : macOS bloque tout script téléchargé qui n'est pas signé par un développeur
enregistré auprès d'Apple. Cliquer sur **Terminé** (surtout pas « Placer dans la corbeille »), puis au choix :

- **Par les Réglages** (une seule fois) : menu  > **Réglages Système** > **Confidentialité et sécurité** ;
  descendre jusqu'à la section **Sécurité** : le message « lancer_mac.command a été bloqué » apparaît. Cliquer sur
  **Ouvrir quand même**, saisir son mot de passe, puis confirmer **Ouvrir**.
  (Sur les macOS plus anciens que la version 15, un **clic droit** > **Ouvrir** sur le fichier suffit.)
- **Par le Terminal** : retirer la marque « téléchargé » du fichier, puis double-cliquer de nouveau :

  ```bash
  cd chemin/vers/rush2
  xattr -d com.apple.quarantine lancer_mac.command
  ```

Autres blocages possibles sur Mac :

| Ce qui se passe | Solution |
| --- | --- |
| « …n'a pas les autorisations d'accès appropriées » | Le fichier a perdu son droit d'exécution (copie depuis un ZIP) : `chmod +x lancer_mac.command` dans le Terminal, depuis le dossier du projet |
| Le fichier s'ouvre dans un éditeur de texte | Clic droit > **Lire les informations** > **Ouvrir avec** : **Terminal**, puis **Tout modifier** |
| Un projet récupéré avec `git clone` | Pas de blocage : seuls les fichiers téléchargés sont marqués par macOS |

### Premier double-clic sur Windows : « Windows a protégé votre ordinateur »

Même cause que sur Mac : un fichier `.bat` **téléchargé** est bloqué par Microsoft Defender SmartScreen.

- Dans la fenêtre bleue, cliquer sur **Informations complémentaires**, puis sur **Exécuter quand même**.
- Ou, une fois pour toutes : clic droit sur `lancer_windows.bat` > **Propriétés** > cocher **Débloquer** en bas de
  l'onglet **Général** > **OK**.
- Si le ZIP entier est bloqué, faire **Débloquer** sur le fichier ZIP **avant** de l'extraire : tous les fichiers
  extraits seront alors débloqués.

À l'ouverture du classeur, si Excel affiche le bandeau jaune **« Mode protégé »**, cliquer sur
**Activer la modification** : sinon les formules de l'outil ne se calculent pas (Mac et Windows).

## Utilisation en ligne de commande

Environnement activé (`conda activate rush2`, ou `source .venv/bin/activate` / `.venv\Scripts\activate`),
depuis le dossier du projet :

```bash
python main.py --offline
```

Le terminal affiche le chemin du classeur, le nombre de contrôles et les messages clés de la Synthèse.
Pour l'ouvrir : `open deliverables/analyse_ventes_2019-09.xlsx` (Mac) ou `start deliverables\analyse_ventes_2019-09.xlsx` (Windows).

| Option de `main.py` | Rôle |
| --- | --- |
| *(aucune)* | Télécharge la donnée grippe à jour (Sentinelles) ; si le site ne répond pas, la copie locale est utilisée |
| `--offline` | N'utilise que les fichiers du dépôt (c'est ce que fait le lanceur double-clic) |
| `--fin 2019-08` | Refait le classeur d'un mois passé : historique jusqu'à la fin de ce mois seulement |
| `--raw-dir chemin` | Lit les 4 exports dans un autre dossier que `data/raw/` |
| `--output-dir chemin` | Écrit le classeur dans un autre dossier que `deliverables/` |
| `--template chemin` | Utilise un autre modèle Excel que `templates/workbook_template.xlsx` |

`main.py` se lance aussi depuis un autre dossier (`python "/chemin/vers/rush2/main.py" --offline`) : les chemins
sont calculés depuis son emplacement.

### Chaque mois

1. Remplacer les 4 fichiers de `data/raw/` par les nouveaux exports du client (**mêmes noms**, historique complet) :
   `Pharma_Ventes_Hourly.csv`, `Pharma_Ventes_Daily.csv`, `Pharma_Ventes_Weekly.csv`, `Pharma_Ventes_Monthly.csv`.
2. Double-cliquer sur le lanceur (ou `python main.py`).
3. Le dernier mois complet est détecté automatiquement ; le classeur `analyse_ventes_AAAA-MM.xlsx` est créé à partir
   du modèle, contrôlé, puis le classeur du mois précédent est **déplacé tel quel** dans `deliverables/archive/`.
   Si le contrôle échoue, rien n'est déplacé : le classeur en vigueur reste en place.

Les contrôles de cohérence sont refaits à chaque exécution (un nouvel export peut avoir d'autres erreurs) :
journal, écarts et pics sont écrits dans `reports/quality/` et repris dans la feuille **État_des_données**.

### Autres commandes

| Commande (depuis le dossier du projet, environnement activé) | Rôle |
| --- | --- |
| `python -m pytest` | Lance tous les tests |
| `cd src` puis `python -m pharma.cleaning.run` | Nettoyage des 4 exports seulement : tables propres dans `data/processed/`, rapport dans `reports/quality/` |
| `python -c "import sys; sys.path.insert(0, 'src'); from pharma.workbook import template; template.build_template()"` | Recrée le modèle `templates/workbook_template.xlsx` depuis le code (seulement si la mise en page change) |
| `python scripts/update_note_prevision.py` | Met à jour les tableaux de résultats de la note de prévision (`docs/note_prevision_jeanne.md`) |

### En cas d'erreur

| Message | Solution |
| --- | --- |
| Lanceur : « Aucun environnement Python trouvé » | Faire l'installation : un environnement conda nommé `rush2`, ou un dossier `.venv` à la racine du projet |
| `No module named pandas` (ou autre bibliothèque) | En ligne de commande : l'environnement n'est pas activé. Avec le lanceur : `pip install -r requirements.txt` dans l'environnement |
| `No module named 'pharma…'` | Un fichier manque dans `src/pharma/` : `git pull`, ou recopier le dossier `src` complet |
| `can't open file '…/main.py'` | Mauvais dossier, ou chemin avec espaces sans guillemets |
| `unrecognized arguments: -offline` | Les options prennent deux tirets : `--offline` |
| `PackagesNotFoundError` (conda) | Ajouter `-c conda-forge` à la commande `conda create` |
| `Modèle absent : templates/workbook_template.xlsx` ou « Zones absentes du modèle » | Recopier le dossier `templates/`, ou recréer le modèle (commande ci-dessus) |
| `Export manquant : data/raw/…` | Les 4 CSV doivent être dans `data/raw/` avec leurs noms d'origine |
| Le classeur s'ouvre mais les cellules de l'outil sont vides | Cliquer sur **Activer la modification** (bandeau « Mode protégé ») |

## Le classeur

11 feuilles, de la lecture stratégique jusqu'aux données brutes :

| Feuille | Contenu |
| --- | --- |
| Synthèse | Message clé, chiffres clés, ce qu'il faut retenir, verdict de prévision, recommandations, limites |
| Outil | Sélection de groupes et d'une période : ventes, même période N-1, répartition par heure, détail dans le temps |
| Stats_Groupes | Poids de chaque groupe, saisonnalité, mois forts et faibles, cumul de l'année, volumes annuels |
| Stats_Calendrier | Jours de la semaine, heures, carte d'affluence |
| Stats_Mensuel | Série mensuelle recalculée depuis l'horaire, graphique des 60 derniers mois |
| Environnement | Effet de la grippe (Réseau Sentinelles) à saison égale : association, levier, causalité |
| Prévision | Prévision du mois suivant, valeur métier, régularité de la demande, backtest, détail |
| Confidentialité | Risque de ré-identification selon le niveau de détail, décision sur le partage |
| État_des_données | Quel export pour quoi, contrôles, écarts, pics |
| Données_Jour, Données_Heure | Ventes de chaque jour et de chaque heure (base de l'outil) |

Les 4 règles de mise à jour :

1. **Toujours repartir du modèle.** `templates/workbook_template.xlsx` est copié vers un nouveau fichier daté ;
   le classeur d'un autre mois n'est jamais modifié, il est **déplacé tel quel dans `deliverables/archive/`**.
2. **Le code n'écrit que dans des zones déclarées** : tableaux Excel nommés (`T_Jour`…) et cellules nommées.
3. **Les formules suivent les données** : références structurées (`T_Jour[Date]`) ; graphiques sur une fenêtre de taille fixe.
4. **Contrôle automatique** : après chaque mise à jour, le classeur est comparé au modèle ; tout écart bloque la livraison.

Le classeur est **généré** : il n'est pas versionné dans Git, chacun le recrée avec le lanceur.
Détail des zones : [`docs/data_contract.md`](docs/data_contract.md).

## Structure du dépôt

```
rush2/
├── README.md                    installation, utilisation, qui a fait quoi
├── requirements.txt             dépendances, versions fixées
├── .gitignore                   exclut l'environnement et les fichiers générés
├── main.py                      mise à jour complète en une commande           (Adelaida)
├── lancer_mac.command           double-clic Mac                                (Adelaida)
├── lancer_windows.bat           double-clic Windows                            (Adelaida)
│
├── data/
│   ├── raw/                     les 4 exports, jamais modifiés
│   ├── external/                donnée grippe Sentinelles (copie locale)       (Ihman)
│   └── processed/               tables propres (générées, non versionnées)
├── templates/
│   └── workbook_template.xlsx   modèle du classeur client                      (Adelaida)
│
├── src/pharma/
│   ├── config.py                chemins, groupes ATC, seuils                   (socle)
│   ├── atc.py                   familles des codes ATC                         (Ihman)
│   ├── pipeline.py              enchaîne les 3 couches                         (Adelaida)
│   ├── cleaning/                COUCHE 1 · lire et fiabiliser les exports
│   │   ├── loading.py           lecture des exports                            (socle)
│   │   ├── checks.py            les contrôles communs                          (socle)
│   │   ├── hourly.py            export horaire (la référence)                  (Adelaida)
│   │   ├── daily.py             export journalier                              (Ihman)
│   │   ├── weekly.py            export hebdomadaire                            (Ihman)
│   │   ├── monthly.py           export mensuel                                 (Jeanne)
│   │   └── run.py               assemble les 4, écrit l'état des données       (Adelaida)
│   ├── analysis/                COUCHE 2 · calculer
│   │   ├── descriptive.py       statistiques, saisonnalité                     (Ihman)
│   │   ├── environment.py       effet de la grippe                             (Ihman)
│   │   ├── profiles.py          jours et heures                                (Adelaida)
│   │   ├── privacy.py           ré-identification, RGPD                        (Adelaida)
│   │   ├── forecast.py          test de prévision                              (Jeanne)
│   │   └── summary.py           contenu de la Synthèse                         (Adelaida · Jeanne)
│   └── workbook/                COUCHE 3 · dessiner, remplir et contrôler le classeur
│       ├── styles.py            couleurs, polices de la charte                 (Ihman)
│       ├── sheets_tool.py       Outil, Données_Jour, Données_Heure             (Ihman)
│       ├── sheets_sales.py      Stats_Groupes, Stats_Mensuel, Environnement    (Ihman)
│       ├── sheets_summary.py    Synthèse, Prévision                            (Adelaida · Jeanne)
│       ├── sheets_data.py       Stats_Calendrier, Confidentialité, État des données (Adelaida)
│       └── tables.py · template.py · update.py · verify.py                     (Adelaida)
│
├── notebooks/                   nettoyage pas à pas dans Jupyter (un par export)
├── scripts/
│   └── update_note_prevision.py tableaux de la note de prévision               (Jeanne)
├── tests/                       un fichier de tests par module, même responsable
├── docs/
│   ├── data_contract.md         fichiers, colonnes, zones du classeur          (Adelaida)
│   ├── user_guide.md            mode d'emploi du pharmacien                    (Ihman)
│   ├── note_prevision_jeanne.md note, partie 1 : la prévision                  (Jeanne)
│   └── deck_manager_jeanne.md   texte et oral du deck manager                  (Jeanne)
├── reports/                     rapports de contrôle (générés, non versionnés)
└── deliverables/
    ├── analyse_ventes_AAAA-MM.xlsx       classeur du mois (généré par main.py, non versionné)
    ├── archive/                          classeurs des mois précédents, intacts
    ├── deck_manager_jeanne.pdf · .pptx   deck manager                          (Jeanne)
    ├── notes_orales_deck_manager_jeanne.md                                     (Jeanne)
    ├── deck_pharmacien.pdf               deck pharmacien acheteur              (Ihman)
    ├── guide_pharmacien.pdf              mode d'emploi du classeur             (Ihman)
    └── deck_proprietaire.pdf             deck propriétaire                     (Adelaida)
```

Les dépendances vont dans un seul sens : `cleaning` → `analysis` → `workbook`.
Noms de dossiers et de fichiers de code en anglais (convention Python) ; tout ce que lisent le client et le manager est en français.

## Nettoyage dans Jupyter

Chaque export a son notebook dans `notebooks/` : on y explore et on montre le nettoyage étape par étape.
La version définitive de chaque étape est dans le module correspondant de `src/pharma/cleaning/`,
car c'est lui que `main.py` relance chaque mois (le notebook n'est pas relancé automatiquement).

| Notebook | Export | Module | Responsable |
| --- | --- | --- | --- |
| `01_nettoyage_horaire_adelaida.ipynb` | horaire | `cleaning/hourly.py` | Adelaida |
| `02_nettoyage_journalier_iman.ipynb` | journalier | `cleaning/daily.py` | Ihman |
| `03_nettoyage_hebdomadaire_iman.ipynb` | hebdomadaire | `cleaning/weekly.py` | Ihman |
| `04_nettoyage_mensuel_jeanne.ipynb` | mensuel | `cleaning/monthly.py` | Jeanne |

Dans VS Code : installer l'extension **Jupyter**, ouvrir le notebook, choisir le noyau Python du projet (« Python (rush2) » avec conda, ou `.venv`), puis **Run All**.

## Qui a fait quoi

| Membre | Bloc | Code | Tests | Autres livrables |
| --- | --- | --- | --- | --- |
| Adelaida | **data** : données, classeur, Synthèse, partage des données | `cleaning/hourly.py`, `cleaning/run.py`, `analysis/profiles.py`, `analysis/privacy.py`, `analysis/summary.py` (Synthèse), `workbook/sheets_data.py`, `workbook/sheets_summary.py` (Synthèse), `workbook/tables.py`, `workbook/template.py`, `workbook/update.py`, `workbook/verify.py`, `pipeline.py`, `main.py`, lanceurs | `test_cleaning_hourly.py`, `test_cleaning_run.py`, `test_workbook.py` | Deck propriétaire, note partie 2, `docs/data_contract.md` |
| Ihman | **sales** : ventes, environnement, outil | `cleaning/daily.py`, `cleaning/weekly.py`, `analysis/descriptive.py`, `analysis/environment.py`, `atc.py`, `workbook/styles.py`, `workbook/sheets_sales.py`, `workbook/sheets_tool.py` | `test_cleaning_daily.py`, `test_cleaning_weekly.py`, `test_descriptive.py`, `test_environment.py`, `test_atc.py` | Deck pharmacien, guide du pharmacien, `docs/user_guide.md`, donnée grippe |
| Jeanne | **forecast** : prévision | `cleaning/monthly.py`, `analysis/forecast.py`, `analysis/summary.py` (verdict, limites de la prévision), `workbook/sheets_summary.py` (Prévision), `scripts/update_note_prevision.py` | `test_monthly.py`, `test_forecast.py` | Deck manager et notes orales, note partie 1 |

Socle commun, créé au lancement : `config.py`, `cleaning/loading.py`, `cleaning/checks.py`, `requirements.txt`.

## Donnée externe

Réseau Sentinelles (Inserm, Sorbonne Université) : incidence hebdomadaire des syndromes grippaux en France,
<https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv>. Copie dans `data/external/`, mise à jour par `main.py`
(sans `--offline`) quand le site répond.

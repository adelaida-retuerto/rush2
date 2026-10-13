# Rush 2 – Analyse des ventes d'une pharmacie

Analyse de près de six ans de ventes (janvier 2014 - octobre 2019) pour 8 groupes de médicaments (codes ATC),
à partir des 4 exports du logiciel de caisse. Chaque mois, une commande produit un classeur Excel daté que le
pharmacien utilise seul, sans Python ni macro.

## Installation (une seule fois)

Prérequis : **Python 3.14** et une connexion internet pour installer les bibliothèques.
Deux méthodes au choix, qui donnent exactement le même résultat : **conda** (utilisée par l'équipe) ou **venv**.
Dans tous les cas, ne jamais envoyer l'environnement sur GitHub (`.venv/` est déjà dans `.gitignore`).

> Évitez les espaces dans le chemin du dossier (ex. `Rush2` plutôt que `Rush 2`). Sinon, mettez le chemin
> entre guillemets dans le terminal : `cd "…/Rush 2/rush2"`.

### Option A · conda

Installer **Miniconda** (docs.anaconda.com/miniconda ; sur Mac, version Apple Silicon ou Intel selon la machine).

**Mac** (application Terminal) ou **Windows** (Anaconda Prompt) :

```bash
cd chemin/vers/rush2
conda env create -f environment.yml     # crée l'environnement rush2 : Python 3.14.8 + bibliothèques
conda activate rush2
python --version                        # doit afficher Python 3.14.8
python -m pytest                        # 28 passed = installation correcte
```

Sans le fichier `environment.yml`, les mêmes étapes à la main :

```bash
conda create -n rush2 -c conda-forge python=3.14.8
conda activate rush2
pip install -r requirements.txt
```

### Option B · venv

Installer **Python 3.14** depuis python.org (Windows : cocher « Add python.exe to PATH »).

**Mac** (Terminal) :

```bash
cd chemin/vers/rush2
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                        # 28 passed
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

### Pour les notebooks (Jupyter)

Une seule fois, environnement activé :

```bash
python -m ipykernel install --user --name rush2 --display-name "Python (rush2)"
```

Puis `jupyter lab` depuis le dossier du projet, et choisir le noyau **Python (rush2)** dans chaque notebook.

## Utilisation (à chaque fois)

**Le plus simple : double-cliquer sur `lancer_mac.command` (Mac) ou `lancer_windows.bat` (Windows)**, à la racine du projet : il trouve l'environnement conda `rush2` (sinon `.venv`), lance `main.py --offline`, ouvre le classeur du mois dans Excel et garde la fenêtre ouverte pour lire les messages. Sinon, en ligne de commande :

| Étape | conda | venv (Mac) | venv (Windows) |
| --- | --- | --- | --- |
| 1. Activer l'environnement | `conda activate rush2` | `source .venv/bin/activate` | `.venv\Scripts\activate` |
| 2. Aller dans le projet | `cd chemin/vers/rush2` | idem | `cd chemin\vers\rush2` |
| 3. Produire le classeur | `python main.py --offline` | idem | idem |

Le terminal affiche à la fin le chemin du classeur : `deliverables/analyse_ventes_AAAA-MM.xlsx`
(Mac : `open deliverables/analyse_ventes_2019-09.xlsx` ; Windows : `start deliverables\analyse_ventes_2019-09.xlsx`).

- `--offline` : utilise la copie locale de la donnée grippe. Sans cette option, `main.py` télécharge la version à jour.
- **Depuis un autre dossier** : donner le chemin complet, entre guillemets s'il contient des espaces :
  `python "/chemin/vers/rush2/main.py" --offline`. Les données sont toujours lues dans `rush2/data/raw/` et le
  classeur écrit dans `rush2/deliverables/` (les chemins sont calculés depuis l'emplacement de `main.py`).
- **Autres dossiers d'entrée ou de sortie** : `--raw-dir chemin/des/exports` et `--output-dir chemin/de/sortie`.

### En cas d'erreur

| Message | Solution |
| --- | --- |
| `No module named pandas` (ou autre bibliothèque) | L'environnement n'est pas activé : étape 1 |
| `No module named 'pharma.cleaning.monthly'` (ou autre fichier du projet) | Un fichier manque dans `src/pharma/` : `git pull`, ou recopier le dossier `src` complet (30 fichiers `.py`) |
| `can't open file '…/main.py'` | Mauvais dossier, ou chemin avec espaces sans guillemets |
| `unrecognized arguments: -offline` | Les options prennent deux tirets : `--offline` |
| `PackagesNotFoundError` (conda) | Ajouter `-c conda-forge`, ou utiliser `environment.yml` |
| `Modèle absent : templates/workbook_template.xlsx` | Recopier le dossier `templates/`, ou lancer `python scripts/build_template.py` |
| `Export manquant : data/raw/…` | Les 4 CSV doivent être dans `data/raw/` avec leurs noms d'origine |

**Chaque mois** : remplacer les 4 fichiers de `data/raw/` par les nouveaux exports du client (mêmes noms,
historique complet), puis lancer `python main.py`. Le dernier mois complet est détecté automatiquement,
le nouveau classeur `analyse_ventes_AAAA-MM.xlsx` est créé et contrôlé, puis celui du mois précédent part dans
`deliverables/archive/`. Si le contrôle échoue, rien n'est déplacé : le classeur en vigueur reste en place.

| Commande | Rôle |
| --- | --- |
| `python scripts/clean_data.py` | Nettoyage des 4 exports et rapport de qualité seulement |
| `python scripts/preview.py sales\|data\|forecast` | Feuilles d'un seul bloc, pour travailler sans attendre les autres |
| `python scripts/build_template.py` | Recrée le modèle Excel (seulement si la mise en page change) |
| `python scripts/check_workbook.py deliverables/analyse_ventes_2019-09.xlsx` | Contrôle un classeur livré |
| `python main.py --fin 2019-08` | Refait le classeur d'un mois passé (historique jusqu'à la fin de ce mois) |

## Structure du dépôt

```
rush2-pharma/
├── README.md                    installation, utilisation, qui a fait quoi
├── requirements.txt             dépendances, versions fixées
├── environment.yml              environnement conda (Python 3.14.8)
├── pyproject.toml               description du paquet + config des tests
├── .gitignore                   exclut les fichiers générés
├── .github/                     tests automatiques, modèles d'issue et de PR   (Jeanne)
├── main.py                      mise à jour complète en une commande           (Adelaida)
│
├── data/
│   ├── raw/                     les 4 exports, jamais modifiés                 (chacune le sien)
│   ├── external/                donnée grippe Sentinelles                      (Iman)
│   └── processed/               tables propres (générées, non versionnées)
├── templates/
│   └── workbook_template.xlsx   modèle du classeur client                      (Adelaida)
│
├── src/pharma/
│   ├── config.py                chemins, groupes ATC, seuils                   (socle)
│   ├── pipeline.py              enchaîne les 3 couches                         (Adelaida)
│   ├── cleaning/                COUCHE 1 · lire et fiabiliser les exports
│   │   ├── loading.py           lecture des exports                            (socle)
│   │   ├── checks.py            les 9 contrôles communs                        (socle)
│   │   ├── hourly.py            export horaire                                 (Adelaida)
│   │   ├── daily.py             export journalier                              (Iman)
│   │   ├── weekly.py            export hebdomadaire                            (Iman)
│   │   ├── monthly.py           export mensuel                                 (Jeanne)
│   │   └── run.py               assemble les 4, écrit l'état des données       (Adelaida)
│   ├── analysis/                COUCHE 2 · calculer
│   │   ├── descriptive.py       statistiques, saisonnalité                     (Iman)
│   │   ├── environment.py       effet de la grippe                             (Iman)
│   │   ├── profiles.py          jours et heures                                (Adelaida)
│   │   ├── privacy.py           réidentification, RGPD                         (Adelaida)
│   │   ├── forecast.py          test de prévision                              (Jeanne)
│   │   └── summary.py           synthèse : chiffres clés, insights, recommandations, limites (Jeanne)
│   └── workbook/                COUCHE 3 · remplir le classeur et le contrôler
│       ├── styles.py            couleurs, polices                              (Iman)
│       ├── sheets_sales.py      feuilles de statistiques                       (Iman)
│       ├── sheets_tool.py       outil de sélection                             (Iman)
│       ├── sheets_summary.py    Synthèse, Prévision                            (Jeanne)
│       ├── sheets_data.py       État des données, Confidentialité              (Adelaida)
│       └── tables.py · template.py · update.py · verify.py                     (Adelaida)
│
├── notebooks/                   nettoyage pas à pas dans Jupyter
│   ├── 01_nettoyage_horaire_adelaida.ipynb                                     (Adelaida)
│   ├── 02_nettoyage_journalier_iman.ipynb                                      (Iman)
│   ├── 03_nettoyage_hebdomadaire_iman.ipynb                                    (Iman)
│   └── 04_nettoyage_mensuel_jeanne.ipynb                                       (Jeanne)
├── scripts/                     clean_data.py · preview.py · build_template.py · check_workbook.py
├── tests/                       test_<module>.py, même responsable que le module
├── docs/
│   ├── data_contract.md         fichiers, colonnes, zones du classeur          (Adelaida)
│   └── user_guide.md            mode d'emploi du pharmacien                    (Iman)
├── reports/                     rapports de contrôle (générés, non versionnés)
└── deliverables/                classeur daté, note PDF, 3 decks
    ├── analyse_ventes_2019-09.xlsx      ← le mois en vigueur, le seul à ouvrir
    └── archive/
        └── analyse_ventes_2019-08.xlsx  ← intact
```

Les dépendances vont dans un seul sens : `cleaning` → `analysis` → `workbook`.
Noms de dossiers et de fichiers de code en anglais (convention Python) ; tout ce que lisent le client et le manager est en français.

## Le classeur : 4 règles de mise à jour

1. **Toujours repartir du modèle.** `templates/workbook_template.xlsx` est copié vers un nouveau fichier daté.
   Le classeur d'un autre mois n'est jamais modifié : une fois le nouveau classeur contrôlé, l'ancien est
   **déplacé tel quel dans `deliverables/archive/`**. `deliverables/` ne contient donc que le classeur en vigueur.
2. **Le code n'écrit que dans des zones déclarées** : tableaux Excel nommés (`T_Jour`…) et cellules nommées.
3. **Les formules suivent les données** : références structurées (`T_Jour[Date]`) ; graphiques sur une fenêtre de taille fixe.
4. **Contrôle automatique** : après chaque mise à jour, le classeur est comparé au modèle ; tout écart bloque la livraison.

Détail des zones : [`docs/data_contract.md`](docs/data_contract.md).

## Nettoyage dans Jupyter

Chaque export a son notebook dans `notebooks/` : on y explore et on montre le nettoyage étape par étape.
La version définitive de chaque étape est recopiée dans le module correspondant de `src/pharma/cleaning/`,
car c'est lui que `main.py` relance chaque mois (le notebook n'est pas relancé automatiquement).

| Notebook | Export | Module | Responsable |
| --- | --- | --- | --- |
| `01_nettoyage_horaire_adelaida.ipynb` | horaire | `cleaning/hourly.py` | Adelaida |
| `02_nettoyage_journalier_iman.ipynb` | journalier | `cleaning/daily.py` | Iman |
| `03_nettoyage_hebdomadaire_iman.ipynb` | hebdomadaire | `cleaning/weekly.py` | Iman |
| `04_nettoyage_mensuel_jeanne.ipynb` | mensuel | `cleaning/monthly.py` | Jeanne |

Dans VS Code : installer l'extension **Jupyter**, ouvrir le notebook, choisir le noyau Python du projet (« Python (rush2) » avec conda, ou `.venv`), puis **Run All**.

## Qui a fait quoi

| Membre | Bloc | Code | Tests | Autres livrables |
| --- | --- | --- | --- | --- |
| Adelaida | **data** : données, classeur, partage des données | `cleaning/hourly.py`, `cleaning/run.py`, `analysis/profiles.py`, `analysis/privacy.py`, `workbook/tables.py`, `workbook/template.py`, `workbook/update.py`, `workbook/verify.py`, `workbook/sheets_data.py`, `pipeline.py`, `main.py` | `test_cleaning_hourly.py`, `test_cleaning_run.py`, `test_workbook.py` | Note partie 2, deck propriétaire, `docs/data_contract.md` |
| Iman | **sales** : ventes, environnement, outil | `cleaning/daily.py`, `cleaning/weekly.py`, `analysis/descriptive.py`, `analysis/environment.py`, `workbook/styles.py`, `workbook/sheets_sales.py`, `workbook/sheets_tool.py` | `test_cleaning_daily.py`, `test_cleaning_weekly.py`, `test_descriptive.py`, `test_environment.py` | Deck pharmacien, `docs/user_guide.md`, donnée grippe |
| Jeanne | **forecast** : prévision, synthèse, dépôt | `cleaning/monthly.py`, `analysis/forecast.py`, `analysis/summary.py`, `workbook/sheets_summary.py`, `.github/` | `test_cleaning_monthly.py`, `test_forecast.py` | Note partie 1, deck manager |

Socle commun, créé au lancement : `config.py`, `cleaning/loading.py`, `cleaning/checks.py`, `requirements.txt`, `pyproject.toml`.

## Donnée externe

Réseau Sentinelles (Inserm, Sorbonne Université) : incidence hebdomadaire des syndromes grippaux en France,
<https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv>. Copie dans `data/external/`.
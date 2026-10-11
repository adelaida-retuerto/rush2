# Rush 2 : analyse des ventes pharmaceutiques

Analyse de près de 6 ans de ventes (janvier 2014 à octobre 2019) de 8 groupes de médicaments (codes ATC) pour une pharmacie indépendante : classeur Excel, prévision, présentations et note sur le partage des données.

## Installation

Version de référence du groupe : **Python 3.14** (vérifier avec `python3 --version`).
- Mac : `brew install python@3.14`
- Windows : installateur 3.14 sur [python.org](https://www.python.org/downloads/), en cochant « Add python.exe to PATH » (puis utiliser `python` à la place de `python3`)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer le code

*À compléter.*

## Arborescence

```
rush2-pharma/
├── README.md                    utilisation, qui a fait quoi
├── requirements.txt             dépendances, versions fixées
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
│   │   └── summary.py           synthèse, besoins, limites                     (Jeanne)
│   └── workbook/                COUCHE 3 · remplir le classeur et le contrôler
│       ├── styles.py            couleurs, polices                              (Iman)
│       ├── sheets_sales.py      feuilles de statistiques                       (Iman)
│       ├── sheets_tool.py       outil de sélection                             (Iman)
│       ├── sheets_summary.py    Synthèse, Cadrage, Prévision                   (Jeanne)
│       ├── sheets_data.py       État des données, Confidentialité              (Adelaida)
│       └── tables.py · template.py · update.py · verify.py                     (Adelaida)
│
├── scripts/                     clean_data.py · preview.py · build_template.py · check_workbook.py
├── tests/                       test_<module>.py, même responsable que le module
├── docs/
│   ├── data_contract.md         fichiers, colonnes, zones du classeur          (Adelaida)
│   └── user_guide.md            mode d'emploi du pharmacien                    (Iman)
├── reports/                     rapports de contrôle (générés, non versionnés)
└── deliverables/                classeur daté, note PDF, 3 decks
    ├── analyse_ventes_2019-10.xlsx      ← le mois en vigueur, le seul à ouvrir
    └── archive/
        ├── analyse_ventes_2019-08.xlsx
        └── analyse_ventes_2019-09.xlsx  ← intacts
```

## Qui a fait quoi

| Rôle | Périmètre | Livrables | Qui |
|------|-----------|-----------|-----|
| P1 Données & prévision | Script Python, contrôles, test de prévision, dépôt Git | Deck manager, note partie 1 | *à compléter* |
| P2 Excel & achats | Classeur, outil de sélection, statistiques saisonnières | Deck pharmacien | *à compléter* |
| P3 Environnement & conformité | Source externe, RGPD, recommandations | Deck propriétaire, note partie 2 | *à compléter* |

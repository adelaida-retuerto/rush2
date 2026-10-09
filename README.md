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
data/        les 4 exports CSV du client (+ la source externe)
src/         le code Python (config.py = chemins, noms ATC, couleurs)
output/      le classeur Excel généré
decks/       les 3 présentations (PDF)
note/        la note PDF
```

## Qui a fait quoi

| Rôle | Périmètre | Livrables | Qui |
|------|-----------|-----------|-----|
| P1 Données & prévision | Script Python, contrôles, test de prévision, dépôt Git | Deck manager, note partie 1 | *à compléter* |
| P2 Excel & achats | Classeur, outil de sélection, statistiques saisonnières | Deck pharmacien | *à compléter* |
| P3 Environnement & conformité | Source externe, RGPD, recommandations | Deck propriétaire, note partie 2 | *à compléter* |

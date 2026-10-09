# Rush 2 : analyse des ventes pharmaceutiques

Analyse de près de 6 ans de ventes (janvier 2014 à octobre 2019) de 8 groupes de médicaments (codes ATC) pour une pharmacie indépendante : classeur Excel, prévision, présentations et note sur le partage des données.

## Installation

Il faut **Python 3.12 ou plus récent** (`python3 --version`). Sur Mac, si la version est trop ancienne : `brew install python@3.12`, puis utiliser `python3.12` à la place de `python3` ci-dessous.

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

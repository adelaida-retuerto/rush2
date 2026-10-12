# Contrat des données

Fixé ensemble au démarrage. On ne change pas ce format seule : toute modification passe par une pull request relue par l'équipe.
Tant que chacune respecte ce contrat, les trois blocs s'emboîtent sans que personne attende personne.

## Règles communes

- Les 8 groupes s'appellent toujours `M01AB, M01AE, N02BA, N02BE, N05B, N05C, R03, R06` (liste dans `src/pharma/config.py`).
- Les quantités sont dans l'unité du logiciel de caisse, non documentée : on écrit « quantités », jamais « boîtes » ni « euros ».
- L'export horaire est la référence. Jour, semaine et mois sont recalculés depuis lui ; l'export mensuel, faux sur une partie des mois, n'est jamais utilisé pour l'analyse.
- Semaine = lundi -> dimanche, datée du dimanche. Mois = daté du dernier jour du mois.
- Chaque bloc écrit ses propres feuilles du classeur ; personne ne modifie le module d'une autre.

## Nettoyage : un module par export (`src/pharma/cleaning/`)

| Module | Export | Responsable | Fonction |
| --- | --- | --- | --- |
| `hourly.py` | `data/raw/Pharma_Ventes_Hourly.csv` | Adelaida | `clean_hourly(export, derived, rows) -> HourlyResult` |
| `daily.py` | `data/raw/Pharma_Ventes_Daily.csv` | Iman | `clean_daily(export, derived, daily_all, complete_day, rows) -> (daily, ecarts)` |
| `weekly.py` | `data/raw/Pharma_Ventes_Weekly.csv` | Iman | `clean_weekly(export, derived, daily_all, complete_day, rows) -> (weekly, ecarts)` |
| `monthly.py` | `data/raw/Pharma_Ventes_Monthly.csv` | Jeanne | `clean_monthly(export, derived, daily_all, complete_day, rows) -> (monthly, ecarts)` |
| `run.py` | les 4 | Adelaida | `run_cleaning()` : lance les 4, écrit les tables propres et le rapport |

Socle commun, créé au lancement : `loading.py` (lecture des exports) et `checks.py` (les contrôles partagés).

Pour travailler sans attendre le nettoyage de l'horaire :

```python
from pharma.cleaning import checks, loading
daily_all, complete_day = checks.reference_daily(loading.load_export("hourly"))
```

### Les 9 contrôles, identiques pour les 4 exports

1. Périmètre (nombre de lignes, première et dernière date)
2. Doublons de date
3. Valeurs manquantes
4. Valeurs négatives
5. Périodes manquantes dans la suite
6. Colonnes dérivées (`Year`, `Month`, `Hour`, `Weekday Name`) cohérentes avec la date
7. Périodes incomplètes au début et à la fin : exclues
8. Pics inhabituels : signalés, jamais supprimés
9. Comparaison avec l'horaire agrégé au même niveau

Format d'une ligne du journal : `Contrôle, Export, Statut (OK / ANOMALIE), Détail, Décision`.
Format d'un écart : `Export, Période, Groupe, Valeur export, Valeur recalculée (horaire), Écart, Écart %`.

## Tables propres (`python scripts/clean_data.py`)

| Fichier | Une ligne = | Colonnes | Périodes |
| --- | --- | --- | --- |
| `data/processed/ventes_heure.csv` | une heure | `date`, `jour`, `heure` (0-23), `jour_semaine` (1 = lundi), 8 groupes, `total` | Toutes les heures |
| `data/processed/ventes_jour.csv` | un jour | `date`, `jour_semaine`, `mois`, `annee`, 8 groupes, `total` | Jours complets |
| `data/processed/ventes_semaine.csv` | une semaine | `fin_semaine`, `debut_semaine`, 8 groupes, `total` | Semaines complètes |
| `data/processed/ventes_mois.csv` | un mois | `mois` (AAAA-MM), `nb_jours`, 8 groupes, `total` | Mois complets |

```python
from pharma.cleaning.run import load_processed
jour = load_processed("daily")      # index = date, colonnes = 8 groupes
```

Traçabilité dans `reports/quality/` : `journal_controles.csv`, `ecarts_exports.csv`, `pics_signales.csv`, `rapport_qualite.md`.
Ces fichiers et `data/processed/` sont régénérés à chaque exécution : ils ne sont pas versionnés.

## Classeur (modèle `templates/workbook_template.xlsx`)

Le code n'écrit que dans les zones ci-dessous. Un tableau qui change de colonnes, une zone supprimée ou une formule
modifiée hors de ces zones bloque la livraison (`src/pharma/workbook/verify.py`).

| Bloc | Module (`src/pharma/workbook/`) | Tableaux Excel | Cellules nommées |
| --- | --- | --- | --- |
| forecast · Jeanne | `sheets_summary.py` | T_Messages, T_Chiffres_Cles, T_Verdict, T_Besoins, T_Criteres, T_Limites, T_Decisions, T_Risques, T_Prevision, T_Valeur, T_Regularite, T_Backtest, T_Detail_Backtest | txt_sous_titre, txt_prevision_note |
| sales · Iman | `sheets_tool.py` | T_Jour, T_Heure | periode_debut, periode_fin, note_outil |
| sales · Iman | `sheets_sales.py` | T_Groupes, T_Saisonnalite, T_Mois_Forts, T_Cumul, T_Annees, T_Mensuel, T_Grille_Liens, T_Grippe_Effet, T_Grippe_Serie | txt_cumul_titre, txt_grippe_source, txt_grippe_note |
| data · Adelaida | `sheets_data.py` | T_Sources, T_Journal, T_Ecarts, T_Pics, T_Jours, T_Heures, T_Affluence, T_Petits_Comptages, T_Conformite | txt_run_info |

Règles de mise en page du modèle :

- Un tableau de taille fixe (8 groupes, 12 mois, 7 jours, 24 heures) peut avoir une zone en dessous.
- Un tableau qui grandit chaque mois est en bas de sa feuille, ou côte à côte avec un autre tableau qui grandit.
- Les formules pointent sur les tableaux par leur nom (`T_Jour[Date]`), jamais sur une plage fixe.

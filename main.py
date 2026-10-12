"""Mise à jour mensuelle complète : nettoyage -> analyses -> classeur daté, contrôlé.

Usage :
    python main.py                  # télécharge la donnée grippe à jour (sinon copie locale)
    python main.py --offline        # n'utilise que les fichiers du dépôt
    python main.py --fin 2019-08    # refait le classeur d'un mois passé (historique jusqu'à fin août 2019)

Prérequis : le modèle templates/workbook_template.xlsx (créé une fois par scripts/build_template.py).
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pharma import config, pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Mise à jour mensuelle de l'analyse des ventes de la pharmacie")
    parser.add_argument("--offline", action="store_true", help="ne pas télécharger la donnée externe")
    parser.add_argument("--raw-dir", type=Path, default=config.RAW_DIR, help="dossier des 4 exports du mois")
    parser.add_argument("--output-dir", type=Path, default=config.OUTPUT_DIR, help="dossier des classeurs livrés")
    parser.add_argument("--template", type=Path, default=config.TEMPLATE_PATH, help="modèle Excel")
    parser.add_argument("--fin", metavar="AAAA-MM", help="analyser l'historique jusqu'à la fin de ce mois seulement")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    res = pipeline.run(args.offline, args.raw_dir, args.output_dir, args.template, args.fin)
    print(f"\nClasseur du mois : {res.workbook}")
    print(f"Contrôles du classeur : {len(res.checks.checks)} vérifications, toutes conformes au modèle.")
    print(f"Dernier mois complet : {res.clean.last_complete_month:%m/%Y}\n")
    for _, m in res.tables["messages"].iterrows():
        print(f" - {m['Thème']} : {m['Message']}")


if __name__ == "__main__":
    main()

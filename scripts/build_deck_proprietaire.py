"""Génère le deck du propriétaire : deliverables/deck_proprietaire.pdf (5 slides).   [Adelaida]

Usage :
    python scripts/build_deck_proprietaire.py             # télécharge la donnée grippe à jour
    python scripts/build_deck_proprietaire.py --offline   # n'utilise que les fichiers du dépôt

Les chiffres viennent des mêmes analyses que le classeur (nettoyage, profils, confidentialité,
grippe) : relancer après chaque nouvel export suffit à mettre le deck à jour.
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharma import config, pipeline  # noqa: E402
from pharma.cleaning import run as cleaning_run  # noqa: E402
from pharma.decks import proprietaire  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Deck du propriétaire de la pharmacie (PDF)")
    parser.add_argument("--offline", action="store_true", help="ne pas télécharger la donnée externe")
    parser.add_argument("--raw-dir", type=Path, default=config.RAW_DIR, help="dossier des 4 exports")
    parser.add_argument("--output", type=Path, default=proprietaire.DECK_PATH, help="fichier PDF produit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    c = cleaning_run.run_cleaning(args.raw_dir, write=False)   # couche 1 : données propres
    t = pipeline.analyse_sales(c, args.offline)                # grippe, cumul de l'année
    t.update(pipeline.analyse_data(c))                         # confidentialité
    path = proprietaire.build_deck(c, t, args.output)
    print(f"\nDeck propriétaire : {path}")


if __name__ == "__main__":
    main()

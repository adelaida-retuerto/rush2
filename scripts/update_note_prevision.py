from pathlib import Path
import sys
import pandas as pd

racine = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine / "src"))

from pharma.cleaning.run import run_cleaning
from pharma.pipeline import base_tables, analyse_forecast

note = racine / "docs" / "note_prevision_jeanne.md"
texte = note.read_text(encoding="utf-8")

c = run_cleaning(write=False)
t = base_tables(c, 70)
t.update(analyse_forecast(c, t))

bilan = t["fc_summary"]
valeur = t["value"].set_index("Groupe")

resultats = pd.DataFrame({
    "Méthode testée sélectionnée":
        bilan["Méthode choisie avant validation"],
    "Méthode recommandée": valeur["Méthode recommandée"],
    "MAE méthode testée": bilan["MAE méthode"],
    "MAE référence": bilan["MAE référence"],
    "Gain (%)": bilan["Gain (%)"],
    "Erreur relative (%)": bilan["Erreur relative (%)"]
}).rename_axis("Groupe").reset_index()

previsions = t["fc_next"][[
    "Groupe", "Quantité prévue",
    "Borne basse indicative", "Borne haute indicative"
]]

marqueur = "## Résultats détaillés générés"
introduction = texte.split(marqueur)[0].rstrip()

sections = [
    introduction,
    marqueur,
    "Les scores portent sur la méthode sélectionnée avant validation. "
    "La méthode recommandée peut différer après le repli vers la référence.",
    resultats.to_markdown(index=False, floatfmt=".2f"),
    "### Prévisions d’octobre 2019",
    "Fourchettes indicatives, sans garantie de couverture.",
    previsions.to_markdown(index=False, floatfmt=".2f")
]

note.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
print("Note complétée : résultats et prévisions des huit groupes.")

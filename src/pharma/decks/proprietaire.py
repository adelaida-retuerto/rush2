"""Deck du propriétaire (titulaire de la pharmacie) : 5 slides en PDF.   [Adelaida]

Message : les données de vente sont un actif. Ne pas les céder au laboratoire au niveau
détaillé (risque de ré-identification des clients), et s'en servir nous-mêmes, avec la
donnée publique grippe, pour piloter le stock.

Toutes les phrases chiffrées sont calculées à partir des analyses du classeur : on relance
chaque mois et le deck se met à jour. La charte (couleurs, polices) vient de workbook/styles.py.

Lancer :  python scripts/build_deck_proprietaire.py --offline
"""
from __future__ import annotations

import datetime as dt
import logging
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas de fenêtre : on écrit directement le PDF
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from .. import atc, config  # noqa: E402
from ..analysis.descriptive import NOMS_MOIS, family_volumes  # noqa: E402
from ..workbook import styles as S  # noqa: E402

log = logging.getLogger(__name__)

DECK_PATH = config.OUTPUT_DIR / "deck_proprietaire.pdf"
NB_SLIDES = 5
LARGEUR, HAUTEUR = 13.333, 7.5  # pouces : format 16:9, comme le deck pharmacien

# --- Couleurs de la charte (styles.py les écrit sans « # » pour Excel) ----------------------
SAPIN, SAUGE, CREME, BRUME = "#" + S.SAPIN, "#" + S.SAUGE, "#" + S.CREME, "#" + S.BRUME
ENCRE, GRIS, AMBRE = "#" + S.ENCRE, "#" + S.GRIS, "#" + S.AMBRE
COULEUR_GROUPE = {g: "#" + couleur for g, couleur in S.COULEURS_ATC.items()}
# Une famille prend la teinte foncée de ses groupes (le dernier de la liste : M01AE, N02BE, N05C, R03)
COULEUR_FAMILLE = {atc.famille(g): COULEUR_GROUPE[g] for g in config.GROUP_CODES}


def choisir_police(voulue: str, repli: str) -> str:
    """Police de la charte si elle est installée sur le poste, sinon une police livrée avec matplotlib."""
    installees = {f.name for f in font_manager.fontManager.ttflist}
    if voulue in installees:
        return voulue
    log.warning("Police « %s » absente du poste : remplacée par %s. L'installer (Google Fonts) puis relancer.",
                voulue, repli)
    return repli


# --- Petits outils d'écriture ------------------------------------------------------------------
def pct(valeur: float, signe: bool = False) -> str:
    """Pourcentage à la française : 0,56 -> « 56 % », +0,113 -> « +11 % »."""
    texte = f"{valeur:+.0%}" if signe else f"{valeur:.0%}"
    return texte.replace("%", " %")  # espace insécable avant %, comme en français


def nom_groupe(g: str) -> str:
    """Charte : toujours le code ATC avec son nom. « N02BE · Antalgiques (paracétamol) »."""
    libelle = config.GROUPS[g]
    if " (" not in libelle:
        return f"{g} · {libelle}"
    base, detail = libelle.split(" (", 1)
    exemple = detail.split("ex. ")[-1].rstrip(")") if "ex. " in detail else ""
    return f"{g} · {base} ({exemple})" if exemple else f"{g} · {base}"


def liste_fr(mots: list[str]) -> str:
    """« a, b et c »."""
    return mots[0] if len(mots) == 1 else ", ".join(mots[:-1]) + " et " + mots[-1]


# --- Gabarit commun des slides ----------------------------------------------------------------
class Deck:
    """Dessine les slides avec la même mise en page et les ajoute au PDF."""

    def __init__(self, pdf: PdfPages, periode: str):
        self.pdf = pdf
        self.periode = periode
        self.numero = 0
        self.titre_police = choisir_police(S.POLICE_TITRE, "DejaVu Serif")
        self.texte_police = choisir_police(S.POLICE_TEXTE, "DejaVu Sans")
        plt.rcParams["font.family"] = self.texte_police

    def texte(self, fig, x, y, contenu, taille=13, couleur=ENCRE, largeur=None, **options):
        """Texte courant (Lato), coupé en lignes de `largeur` caractères si besoin."""
        if largeur:
            contenu = "\n".join(textwrap.fill(p, largeur) for p in contenu.split("\n"))
        return fig.text(x, y, contenu, fontsize=taille, color=couleur, va="top",
                        linespacing=1.45, **options)

    def etiquette(self, fig, x, y, mot, fond=SAPIN, couleur="white"):
        """Pastille en haut à gauche (« PROPRIÉTAIRE »), comme le deck pharmacien."""
        fig.text(x, y, mot.upper(), fontsize=10, fontweight="bold", color=couleur, va="center",
                 bbox=dict(boxstyle="round,pad=0.55,rounding_size=0.9", fc=fond, ec="none"))

    def slide(self, titre: str, sous_titre: str = "", source: str = ""):
        """Nouvelle slide de contenu : fond crème, pastille, titre-message, sous-titre, source."""
        self.numero += 1
        fig = plt.figure(figsize=(LARGEUR, HAUTEUR), facecolor=CREME)
        self.etiquette(fig, 0.045, 0.925, "Propriétaire")
        lignes = textwrap.wrap(titre, 62)
        fig.text(0.045, 0.875, "\n".join(lignes), fontsize=25, fontweight="bold", color=SAPIN,
                 fontfamily=self.titre_police, va="top", linespacing=1.15)
        # self.haut = où commence le contenu, juste sous le titre et le sous-titre (1 ou 2 lignes chacun)
        self.haut = 0.875 - 0.068 * len(lignes) - 0.02
        if sous_titre:
            lignes_sous_titre = textwrap.wrap(sous_titre, 125)
            self.texte(fig, 0.045, self.haut, "\n".join(lignes_sous_titre), taille=13, couleur=SAUGE)
            self.haut -= 0.045 * len(lignes_sous_titre)
        self.haut -= 0.04
        if source:
            self.texte(fig, 0.045, 0.085, source, taille=9, couleur=GRIS, largeur=170)
        fig.text(0.955, 0.035, f"{self.numero} / {NB_SLIDES}", fontsize=9, color=GRIS, ha="right")
        return fig

    def graphique(self, fig, rect):
        """Zone de graphique sobre : pas de cadre, pas d'axe vertical, étiquettes directes."""
        ax = fig.add_axes(rect, facecolor=CREME)
        for cote in ("top", "right", "left"):
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color("#D9DEDC")
        ax.tick_params(colors=GRIS, labelsize=11, length=0)
        return ax

    def ajouter(self, fig):
        self.pdf.savefig(fig, facecolor=fig.get_facecolor())
        plt.close(fig)


# --- Les 5 slides -------------------------------------------------------------------------------
def slide_couverture(d: Deck, chiffres: dict) -> None:
    d.numero += 1
    fig = plt.figure(figsize=(LARGEUR, HAUTEUR), facecolor=SAPIN)
    d.etiquette(fig, 0.065, 0.76, "Propriétaire", fond=CREME, couleur=SAPIN)
    fig.text(0.065, 0.67, "Vos données de vente :", fontsize=42, fontweight="bold", color=CREME,
             fontfamily=d.titre_police, va="top")
    fig.text(0.065, 0.55, "un actif à protéger", fontsize=42, fontweight="bold", fontstyle="italic",
             color=CREME, fontfamily=d.titre_police, va="top")
    d.texte(fig, 0.065, 0.40,
            f"Ne pas céder l'export détaillé au laboratoire : {pct(chiffres['part_heure_n05c'])} des heures "
            "avec un hypnotique vendu permettent de reconnaître le client. Et s'en servir nous-mêmes, "
            "avec la donnée publique grippe, pour piloter le stock.",
            taille=15, couleur="#D9E4E1", largeur=95)
    d.texte(fig, 0.065, 0.12, f"Rush 2 · Analyse des ventes pharmaceutiques · {d.periode}",
            taille=10, couleur="#B8C7C3")
    # Bandeau des 8 couleurs ATC en bas, comme sur le deck pharmacien
    for i, g in enumerate(config.GROUP_CODES):
        fig.add_artist(plt.Rectangle((i / 8, 0), 1 / 8, 0.035, transform=fig.transFigure,
                                     color=COULEUR_GROUPE[g], lw=0))
    d.ajouter(fig)


def slide_activite(d: Deck, c, t: dict) -> None:
    familles = family_volumes(c)
    top = familles.iloc[0]
    # Évolution du cumul de l'année par famille (janvier -> dernier mois complet, face à l'an passé)
    cumul = t["year_to_date"].copy()
    cumul["Famille"] = cumul["Groupe"].map(atc.famille)
    par_famille = cumul.groupby("Famille")[["Cumul année en cours", "Cumul année précédente"]].sum()
    evolution = (par_famille["Cumul année en cours"] / par_famille["Cumul année précédente"] - 1).sort_values()
    total = cumul["Cumul année en cours"].sum() / cumul["Cumul année précédente"].sum() - 1
    meilleure = evolution.index[-1]
    annee = c.last_complete_month.year

    fig = d.slide(
        f"{top['Famille']} : {pct(top['Part du volume'])} des volumes ; la famille "
        f"{meilleure.lower()} progresse le plus en {annee} ({pct(evolution.iloc[-1], True)})",
        f"Sur l'ensemble des 8 groupes, le cumul {t['year_to_date'].attrs['periode']} évolue de {pct(total, True)}.",
        f"Source : exports du logiciel de caisse, recalculés depuis l'export horaire ({d.periode_donnees}). "
        f"Quantités dans l'unité du logiciel, non documentée. Évolution : cumul {t['year_to_date'].attrs['periode']}.")

    # Gauche : poids de chaque famille sur toute la période
    ax = d.graphique(fig, [0.20, 0.34, 0.26, d.haut - 0.43])
    ordre = familles.iloc[::-1]
    ax.barh(ordre["Famille"], ordre["Part du volume"], color=[COULEUR_FAMILLE[f] for f in ordre["Famille"]],
            height=0.6)
    for i, v in enumerate(ordre["Part du volume"]):
        ax.text(v + 0.01, i, pct(v), va="center", fontsize=12, color=ENCRE, fontweight="bold")
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=12, labelcolor=ENCRE)
    d.texte(fig, 0.045, d.haut, "Part de chaque famille dans les volumes", taille=13, fontweight="bold")

    # Droite : évolution sur un an, par famille
    ax = d.graphique(fig, [0.67, 0.34, 0.27, d.haut - 0.43])
    ax.barh(evolution.index, evolution.values, color=[COULEUR_FAMILLE[f] for f in evolution.index], height=0.6)
    ax.axvline(0, color=GRIS, lw=0.8)
    for i, v in enumerate(evolution.values):
        ax.text(v + (0.005 if v >= 0 else -0.005), i, pct(v, True), va="center",
                ha="left" if v >= 0 else "right", fontsize=12, color=ENCRE, fontweight="bold")
    ax.set_xticks([])
    ax.set_xlim(min(evolution.min(), 0) - 0.06, max(evolution.max(), 0) + 0.06)
    ax.tick_params(axis="y", labelsize=12, labelcolor=ENCRE)
    d.texte(fig, 0.53, d.haut, f"Évolution {annee} face à {annee - 1}, même période", taille=13, fontweight="bold")

    d.texte(fig, 0.045, 0.26,
            "À retenir : le volume repose d'abord sur les antalgiques, dont le paracétamol en vente libre ; "
            "c'est là que le stock et la mise en avant comptent. Les psycholeptiques (N05B, N05C) sont sur "
            "ordonnance : on les suit, on ne les promeut pas.", taille=12, largeur=140)
    d.ajouter(fig)


def slide_grippe(d: Deck, t: dict) -> None:
    effet = t["flu_effect"].set_index("Groupe")
    hausse = (effet["Hiver : ventes sem. forte grippe / autres"] - 1).sort_values()
    top = hausse.index[-1]
    seuil_lecture = 0.10  # même seuil que environment.SEUIL_HAUSSE_HIVER (+10 %)
    au_dessus = [g for g in hausse.index[::-1] if hausse[g] >= seuil_lecture]
    n_significatifs = int((effet["Lien significatif (p<0,01)"] == "Oui").sum())
    attrs = t["flu_effect"].attrs

    fig = d.slide(
        f"Quand la grippe est forte, {nom_groupe(top)} se vend {pct(hausse[top], True)} "
        "de plus qu'un hiver ordinaire",
        f"Donnée publique intégrée : incidence Sentinelles croisée avec vos ventes sur {attrs['n_weeks']} semaines, "
        "à mois égal (un janvier de forte grippe face aux autres janviers).",
        t["flu_source"] + " Forte grippe : incidence ≥ "
        f"{attrs['threshold']:.0f} cas pour 100 000 (15 % des semaines les plus hautes). Limite : ventes 7 j/7 "
        "de 7 h à 22 h, peu typique d'une officine française ; le croisement reste indicatif.")

    ax = d.graphique(fig, [0.33, 0.20, 0.27, d.haut - 0.22])
    ax.barh([nom_groupe(g) for g in hausse.index], hausse.values,
            color=[COULEUR_GROUPE[g] for g in hausse.index], height=0.62)
    ax.axvline(0, color=GRIS, lw=0.8)
    ax.axvline(seuil_lecture, color=GRIS, lw=1, ls=(0, (4, 3)))
    ax.text(seuil_lecture, -1.1, f"repère {pct(seuil_lecture, True)}", fontsize=10, color=GRIS, ha="center")
    for i, v in enumerate(hausse.values):
        ax.text(v + (0.006 if v >= 0 else -0.006), i, pct(v, True), va="center",
                ha="left" if v >= 0 else "right", fontsize=11, color=ENCRE, fontweight="bold")
    ax.set_xticks([])
    ax.set_xlim(hausse.min() - 0.08, hausse.max() + 0.07)
    ax.tick_params(axis="y", labelsize=11, labelcolor=ENCRE)

    d.texte(fig, 0.67, d.haut, "Ce que cela permet", taille=14, fontweight="bold", couleur=SAPIN)
    d.texte(fig, 0.67, d.haut - 0.05,
            f"Suivre le bulletin Sentinelles chaque semaine. Au-dessus de {attrs['threshold']:.0f} cas "
            f"pour 100 000 : renforcer le stock de {liste_fr(au_dessus)}.\n"
            "Mise en avant réservée aux médicaments sans ordonnance ; promotions sur la parapharmacie "
            "d'hiver associée (mouchoirs, thermomètres, sérum physiologique).",
            taille=12, largeur=42)
    d.texte(fig, 0.67, 0.24,
            f"Signal à surveiller, pas une preuve : {attrs['n_hivers']} hivers observés, "
            f"{n_significatifs} groupe(s) avec un lien significatif (p < 0,01).",
            taille=11, couleur=GRIS, largeur=46, fontstyle="italic")
    d.ajouter(fig)


def slide_reidentification(d: Deck, t: dict) -> None:
    seuil = config.SMALL_COUNT_THRESHOLD
    colonne = f"Part ≤ {seuil} unités"
    comptages = t["privacy"]
    sensibles = comptages[comptages["Groupe"].isin(config.SENSITIVE_GROUPS)]
    tableau = sensibles.pivot(index="Niveau", columns="Groupe", values=colonne)
    niveaux = ["Heure", "Jour", "Semaine", "Mois"]
    tableau = tableau.loc[niveaux]
    regles = t["compliance"].set_index("Étape")["Contenu"]

    fig = d.slide(
        f"Au détail horaire, {pct(tableau.loc['Heure', 'N05C'])} des heures avec un hypnotique vendu "
        f"comptent {seuil} unités ou moins : assez pour reconnaître le client",
        "Un voisin, un employé ou un proche qui a vu la personne au comptoir peut relier la vente à elle. "
        "Plus le détail est fin, plus le risque est grand.",
        f"Part des cellules avec au moins une vente qui comptent ≤ {seuil} unités, par niveau de détail. "
        f"Source : export horaire du logiciel de caisse ({d.periode_donnees}).")

    ax = d.graphique(fig, [0.06, 0.20, 0.50, d.haut - 0.22])
    largeur_barre = 0.36
    for k, g in enumerate(config.SENSITIVE_GROUPS):
        positions = [i + (k - 0.5) * largeur_barre for i in range(len(niveaux))]
        ax.bar(positions, tableau[g], width=largeur_barre, color=COULEUR_GROUPE[g])
        for x, v in zip(positions, tableau[g]):
            ax.text(x, v + 0.02, pct(v), ha="center", fontsize=11, fontweight="bold",
                    color=AMBRE if v >= 0.5 else ENCRE)  # ambre = alerte : plus d'une cellule sur deux
        # Étiquette directe de la série, écrite dans sa première barre (pas de légende)
        ax.text(positions[0], 0.03, f"{g} · {config.GROUPS[g].split(' et ')[0]}", rotation=90, ha="center", va="bottom",
                fontsize=10, color="white", fontweight="bold")
    ax.set_xticks(range(len(niveaux)))
    ax.set_xticklabels(["Horaire", "Journalier", "Hebdomadaire", "Mensuel"], fontsize=12, color=ENCRE)
    ax.set_yticks([])
    ax.set_ylim(0, 1.1)

    d.texte(fig, 0.62, d.haut, "Pourquoi c'est un risque", taille=14, fontweight="bold", couleur=SAPIN)
    d.texte(fig, 0.62, d.haut - 0.05, f"Règle. {regles['Règle']}.\n\nConséquence. {regles['Conséquence']}.\n\n"
            f"Au-delà du RGPD. {regles['Au-delà du RGPD']}.", taille=11.5, largeur=52)
    d.ajouter(fig)


def slide_decision(d: Deck, t: dict) -> None:
    seuil = config.SMALL_COUNT_THRESHOLD
    comptages = t["privacy"]
    sensibles = comptages[comptages["Groupe"].isin(config.SENSITIVE_GROUPS)]
    pire = sensibles.groupby("Niveau")[f"Part ≤ {seuil} unités"].max()  # le groupe sensible le plus exposé
    actions = t["compliance"].set_index("Étape")["Contenu"]

    fig = d.slide(
        "Notre recommandation : refuser l'export détaillé, ne discuter que de totaux mensuels",
        "La remise proposée ne compense pas un risque porté par la pharmacie, responsable de traitement.",
        "Ce deck n'est pas un avis juridique : la contrepartie doit être validée par un juriste ou l'Ordre "
        "avant toute signature.")

    # Gauche : une ligne par niveau de détail, avec la décision
    haut = d.haut
    d.texte(fig, 0.05, haut, "Niveau de détail", taille=12, fontweight="bold", couleur=SAPIN)
    d.texte(fig, 0.20, haut, f"Ventes ≤ {seuil} unités", taille=12, fontweight="bold", couleur=SAPIN)
    d.texte(fig, 0.36, haut, "Décision", taille=12, fontweight="bold", couleur=SAPIN)
    lignes = [("Horaire", "Heure"), ("Journalier", "Jour"), ("Hebdomadaire", "Semaine"), ("Mensuel", "Mois")]
    for i, (libelle, niveau) in enumerate(lignes):
        y = haut - 0.08 - i * 0.095
        refuser = pire[niveau] > 0  # au moins une cellule sensible minuscule : on refuse ce niveau
        fig.add_artist(plt.Rectangle((0.04, y - 0.06), 0.555, 0.08, transform=fig.transFigure,
                                     color=BRUME if i % 2 == 0 else CREME, lw=0))
        d.texte(fig, 0.05, y - 0.005, libelle, taille=13)
        d.texte(fig, 0.20, y - 0.005, f"jusqu'à {pct(pire[niveau])}" if refuser else "aucune", taille=13,
                fontweight="bold", couleur=AMBRE if pire[niveau] >= 0.5 else ENCRE)
        d.texte(fig, 0.36, y - 0.005, "Refuser" if refuser else "Totaux seuls, sans N05B ni N05C",
                taille=13, fontweight="bold", couleur=SAPIN if refuser else SAUGE)
    d.texte(fig, 0.05, haut - 0.47, f"Pire des deux groupes sensibles (N05B, N05C) : part des cellules "
            f"avec une vente qui comptent ≤ {seuil} unités.", taille=10, couleur=GRIS)

    # Droite : conditions si une négociation a lieu malgré tout
    d.texte(fig, 0.62, haut, "Si l'on négocie malgré tout", taille=14, fontweight="bold", couleur=SAPIN)
    conditions = [actions["Action 2"], actions["Action 3"], actions["Action 4"], actions["Action 5"]]
    d.texte(fig, 0.62, haut - 0.06, "\n\n".join(f"{i}. {textwrap.fill(a, 44, subsequent_indent='    ')}"
                                                 for i, a in enumerate(conditions, 1)), taille=12)
    d.ajouter(fig)


# --- Assemblage ---------------------------------------------------------------------------------
def build_deck(c, t: dict, path: Path = DECK_PATH) -> Path:
    """Écrit le deck propriétaire (5 slides) à partir du nettoyage `c` et des tables d'analyse `t`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    aujourd_hui = dt.date.today()
    with PdfPages(path, metadata={"Title": "Deck propriétaire — Rush 2"}) as pdf:
        d = Deck(pdf, f"{NOMS_MOIS[aujourd_hui.month - 1]} {aujourd_hui.year}")
        d.periode_donnees = f"jours complets du {c.daily.index.min():%d/%m/%Y} au {c.daily.index.max():%d/%m/%Y}"
        comptages = t["privacy"].set_index(["Niveau", "Groupe"])
        chiffres = {"part_heure_n05c": comptages.loc[("Heure", "N05C"), f"Part ≤ {config.SMALL_COUNT_THRESHOLD} unités"]}
        slide_couverture(d, chiffres)
        slide_activite(d, c, t)
        slide_grippe(d, t)
        slide_reidentification(d, t)
        slide_decision(d, t)
    log.info("Deck propriétaire écrit : %s", path)
    return path

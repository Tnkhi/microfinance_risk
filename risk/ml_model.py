"""
Moteur de scoring de risque crédit — MicroFinance Risk Cameroun
===============================================================
Deux niveaux de décision :

1. RÈGLES MÉTIER DISQUALIFIANTES (bloquantes, avant tout calcul ML)
   - Crédit en cours non soldé       → refus automatique
   - Mensualité > 40% du revenu net  → refus automatique
   - Ratio endettement global > 2    → refus automatique
   - Antécédent de défaut            → refus automatique

2. SCORING ML (RandomForestClassifier)
   Utilisé uniquement si toutes les règles métier sont passées.
   Features enrichies avec les indicateurs de capacité de remboursement.
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'risk_model.pkl')

# ── Paramètres métier ──────────────────────────────────────────────────────────
# Taux d'effort maximum : la mensualité ne doit pas dépasser ce % du revenu net
TAUX_EFFORT_MAX = 0.40          # 40 %

# Ratio endettement global maximum : montant total / revenu annuel
RATIO_ENDETTEMENT_MAX = 2.0

# Montant maximum accordable en multiple du revenu mensuel (toutes durées)
MULTIPLE_REVENU_MAX = 18        # ex: revenu 200k → max 3 600 000 FCFA sur 36 mois

# ── Encodage secteur ───────────────────────────────────────────────────────────
SECTEUR_ENCODING = {
    'commerce': 0,
    'agriculture': 1,
    'transport': 2,
    'artisanat': 3,
    'services': 4,
    'salarie': 5,
    'autre': 6,
}


# ── Génération de données d'entraînement ──────────────────────────────────────

def _generate_training_data(n=2000, seed=42):
    """
    Dataset synthétique calibré pour la microfinance camerounaise.

    Features (9) :
      0  age
      1  revenu_mensuel (FCFA)
      2  nb_credits_anterieurs (soldés)
      3  nb_retards_anterieurs
      4  ratio_endettement  (montant / revenu_annuel)
      5  taux_effort        (mensualité / revenu_mensuel)
      6  secteur_encoded
      7  duree_mois
      8  multiple_revenu    (montant / revenu_mensuel)

    Target : 0 = bon payeur, 1 = défaut de paiement
    """
    rng = np.random.default_rng(seed)

    age = rng.integers(20, 65, n).astype(float)

    revenu = rng.choice(
        [50_000, 80_000, 100_000, 150_000, 200_000, 300_000, 500_000],
        n,
        p=[0.15, 0.20, 0.20, 0.20, 0.15, 0.07, 0.03]
    ).astype(float) + rng.normal(0, 4_000, n)
    revenu = np.clip(revenu, 20_000, 800_000)

    # Crédits antérieurs = uniquement les crédits SOLDÉS (règle métier)
    nb_credits = rng.integers(0, 7, n).astype(float)
    nb_retards = np.where(
        nb_credits == 0, 0,
        np.clip(rng.binomial(nb_credits.astype(int), 0.20), 0, nb_credits)
    ).astype(float)

    duree_mois = rng.choice([6, 12, 18, 24, 36], n).astype(float)

    # Montant cohérent : on respecte déjà les plafonds dans la génération
    # pour que le modèle apprenne sur des données réalistes
    multiple_max = np.minimum(MULTIPLE_REVENU_MAX, duree_mois * TAUX_EFFORT_MAX)
    multiple = rng.uniform(0.5, multiple_max, n)
    montant = revenu * multiple

    mensualite = montant / duree_mois
    taux_effort = mensualite / revenu
    ratio_endettement = montant / (revenu * 12)
    multiple_revenu = montant / revenu

    secteur = rng.integers(0, 7, n).astype(float)

    # Probabilité de défaut — logique métier
    prob_defaut = (
        0.04
        + 0.35 * (nb_retards / (nb_credits + 1))          # historique retards
        + 0.25 * np.clip(taux_effort - 0.25, 0, 1)        # pression mensuelle
        + 0.15 * np.clip(ratio_endettement - 0.4, 0, 2)   # endettement global
        - 0.08 * np.clip((revenu - 80_000) / 420_000, 0, 1)
        - 0.04 * np.clip((age - 20) / 40, 0, 1)
        + 0.04 * rng.uniform(0, 1, n)
    )
    prob_defaut = np.clip(prob_defaut, 0.02, 0.95)
    y = rng.binomial(1, prob_defaut)

    X = np.column_stack([
        age, revenu, nb_credits, nb_retards,
        ratio_endettement, taux_effort, secteur,
        duree_mois, multiple_revenu,
    ])
    return X, y


def train_and_save_model():
    """Entraîne le modèle et le sauvegarde sur disque."""
    X, y = _generate_training_data(n=3000)
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42,
        ))
    ])
    model.fit(X, y)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    return model


def load_model():
    """Charge le modèle depuis le disque, le crée s'il n'existe pas."""
    if not os.path.exists(MODEL_PATH):
        return train_and_save_model()
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)


# ── Règles métier disqualifiantes ─────────────────────────────────────────────

def verifier_regles_metier(revenu_mensuel, montant_demande, duree_mois,
                            a_credit_en_cours, a_antecedent_defaut,
                            nb_retards_anterieurs):
    """
    Vérifie les règles métier bloquantes AVANT le scoring ML.

    Returns:
        (ok: bool, blocages: list[dict])
        blocages = liste de {'code', 'message', 'valeur', 'plafond'}
    """
    blocages = []

    mensualite = montant_demande / max(duree_mois, 1)
    taux_effort = mensualite / max(revenu_mensuel, 1)
    ratio_endettement = montant_demande / max(revenu_mensuel * 12, 1)
    multiple_revenu = montant_demande / max(revenu_mensuel, 1)

    # Règle 1 — Crédit en cours
    if a_credit_en_cours:
        blocages.append({
            'code': 'CREDIT_EN_COURS',
            'message': "Le client a un crédit en cours non soldé.",
            'detail': "Un client ne peut pas obtenir un nouveau crédit tant que le précédent n'est pas intégralement remboursé.",
            'valeur': None,
            'plafond': None,
        })

    # Règle 2 — Antécédent de défaut
    if a_antecedent_defaut:
        blocages.append({
            'code': 'ANTECEDENT_DEFAUT',
            'message': "Le client a un antécédent de défaut de paiement.",
            'detail': "Un historique de défaut disqualifie automatiquement toute nouvelle demande.",
            'valeur': None,
            'plafond': None,
        })

    # Règle 3 — Taux d'effort (mensualité / revenu)
    if taux_effort > TAUX_EFFORT_MAX:
        blocages.append({
            'code': 'TAUX_EFFORT',
            'message': f"Mensualité trop élevée par rapport au revenu.",
            'detail': (
                f"La mensualité serait de {mensualite:,.0f} FCFA, "
                f"soit {taux_effort*100:.1f}% du revenu mensuel ({revenu_mensuel:,.0f} FCFA). "
                f"Le plafond autorisé est de {TAUX_EFFORT_MAX*100:.0f}%."
            ),
            'valeur': round(taux_effort * 100, 1),
            'plafond': TAUX_EFFORT_MAX * 100,
        })

    # Règle 4 — Ratio endettement global
    if ratio_endettement > RATIO_ENDETTEMENT_MAX:
        blocages.append({
            'code': 'RATIO_ENDETTEMENT',
            'message': "Montant demandé excessif par rapport au revenu annuel.",
            'detail': (
                f"Le montant de {montant_demande:,.0f} FCFA représente "
                f"{ratio_endettement:.2f}x le revenu annuel ({revenu_mensuel*12:,.0f} FCFA). "
                f"Le maximum autorisé est {RATIO_ENDETTEMENT_MAX}x le revenu annuel."
            ),
            'valeur': round(ratio_endettement, 2),
            'plafond': RATIO_ENDETTEMENT_MAX,
        })

    # Règle 5 — Multiple revenu absolu
    if multiple_revenu > MULTIPLE_REVENU_MAX:
        blocages.append({
            'code': 'MULTIPLE_REVENU',
            'message': "Montant demandé dépassant le plafond absolu.",
            'detail': (
                f"Le montant de {montant_demande:,.0f} FCFA représente "
                f"{multiple_revenu:.1f}x le revenu mensuel. "
                f"Le plafond absolu est de {MULTIPLE_REVENU_MAX}x le revenu mensuel "
                f"(soit {revenu_mensuel * MULTIPLE_REVENU_MAX:,.0f} FCFA pour ce client)."
            ),
            'valeur': round(multiple_revenu, 1),
            'plafond': MULTIPLE_REVENU_MAX,
        })

    return len(blocages) == 0, blocages


def montant_maximum_accordable(revenu_mensuel, duree_mois):
    """
    Calcule le montant maximum qu'on peut accorder selon les règles métier.
    Prend le minimum entre le plafond taux d'effort et le plafond endettement global.
    """
    # Via taux d'effort : mensualité max = revenu * 40%
    max_via_effort = revenu_mensuel * TAUX_EFFORT_MAX * duree_mois
    # Via ratio endettement global
    max_via_ratio = revenu_mensuel * 12 * RATIO_ENDETTEMENT_MAX
    # Via multiple absolu
    max_via_multiple = revenu_mensuel * MULTIPLE_REVENU_MAX
    return min(max_via_effort, max_via_ratio, max_via_multiple)


# ── Scoring ML principal ───────────────────────────────────────────────────────

def predict_risk(age, revenu_mensuel, nb_credits_anterieurs,
                 nb_retards_anterieurs, montant_demande,
                 secteur_activite, duree_mois,
                 a_credit_en_cours=False, a_antecedent_defaut=False):
    """
    Évalue le risque crédit en deux étapes :
      1. Règles métier bloquantes
      2. Scoring ML (si règles OK)

    Returns:
        dict avec :
          eligible        : bool
          blocages        : list (vide si éligible)
          score_fiabilite : float 0–100 (None si non éligible)
          probabilite_defaut : float 0–1 (None si non éligible)
          niveau_risque   : 'faible'|'moyen'|'eleve'|'refuse'
          recommandation  : str
          mensualite      : float
          taux_effort     : float
          ratio_endettement : float
          montant_max_accordable : float
    """
    mensualite = montant_demande / max(duree_mois, 1)
    taux_effort = mensualite / max(revenu_mensuel, 1)
    ratio_endettement = montant_demande / max(revenu_mensuel * 12, 1)
    montant_max = montant_maximum_accordable(revenu_mensuel, duree_mois)

    # ── Étape 1 : règles métier ────────────────────────────────────────────────
    eligible, blocages = verifier_regles_metier(
        revenu_mensuel=revenu_mensuel,
        montant_demande=montant_demande,
        duree_mois=duree_mois,
        a_credit_en_cours=a_credit_en_cours,
        a_antecedent_defaut=a_antecedent_defaut,
        nb_retards_anterieurs=nb_retards_anterieurs,
    )

    if not eligible:
        raisons = " | ".join(b['message'] for b in blocages)
        return {
            'eligible': False,
            'blocages': blocages,
            'score_fiabilite': None,
            'probabilite_defaut': None,
            'niveau_risque': 'refuse',
            'recommandation': f"Dossier refusé automatiquement. Raison(s) : {raisons}",
            'mensualite': round(mensualite),
            'taux_effort': round(taux_effort * 100, 1),
            'ratio_endettement': round(ratio_endettement, 3),
            'montant_max_accordable': round(montant_max),
        }

    # ── Étape 2 : scoring ML ──────────────────────────────────────────────────
    model = load_model()
    secteur_enc = SECTEUR_ENCODING.get(secteur_activite, 6)
    multiple_revenu = montant_demande / max(revenu_mensuel, 1)

    features = np.array([[
        float(age),
        float(revenu_mensuel),
        float(nb_credits_anterieurs),
        float(nb_retards_anterieurs),
        float(ratio_endettement),
        float(taux_effort),
        float(secteur_enc),
        float(duree_mois),
        float(multiple_revenu),
    ]])

    proba = model.predict_proba(features)[0]
    prob_defaut = float(proba[1])
    score_fiabilite = round((1 - prob_defaut) * 100, 1)

    if prob_defaut < 0.25:
        niveau = 'faible'
        recommandation = (
            f"Profil fiable. Crédit de {montant_demande:,.0f} FCFA approuvé. "
            f"Mensualité : {mensualite:,.0f} FCFA/mois ({taux_effort*100:.1f}% du revenu). "
            f"Score de fiabilité : {score_fiabilite}/100."
        )
    elif prob_defaut < 0.55:
        niveau = 'moyen'
        montant_conseille = round(min(montant_demande * 0.65, montant_max) / 10_000) * 10_000
        mensualite_cons = montant_conseille / duree_mois
        recommandation = (
            f"Risque modéré. Réduire le montant à {montant_conseille:,.0f} FCFA "
            f"(mensualité : {mensualite_cons:,.0f} FCFA/mois) "
            f"ou exiger une garantie (caution solidaire, nantissement). "
            f"Score : {score_fiabilite}/100."
        )
    else:
        niveau = 'eleve'
        recommandation = (
            f"Risque élevé ({prob_defaut*100:.0f}% de probabilité de défaut). "
            f"Crédit déconseillé. Proposer un micro-crédit d'essai "
            f"≤ {revenu_mensuel*3:,.0f} FCFA sur 6 mois pour établir un historique. "
            f"Score : {score_fiabilite}/100."
        )

    return {
        'eligible': True,
        'blocages': [],
        'score_fiabilite': score_fiabilite,
        'probabilite_defaut': prob_defaut,
        'niveau_risque': niveau,
        'recommandation': recommandation,
        'mensualite': round(mensualite),
        'taux_effort': round(taux_effort * 100, 1),
        'ratio_endettement': round(ratio_endettement, 3),
        'montant_max_accordable': round(montant_max),
    }

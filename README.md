# MicroFinance Risk — Analyse de Risque Crédit

Application Django de scoring de risque crédit pour la microfinance,
développée dans le contexte camerounais / Afrique de l'Ouest.

## Stack technique
- **Backend** : Python 3.10+ / Django 4.2
- **ML** : Scikit-Learn (RandomForestClassifier, Pipeline, StandardScaler)
- **Base de données** : SQLite (incluse, zéro configuration)
- **Frontend** : HTML/CSS pur (pas de framework JS)

---

## Installation rapide

### 1. Prérequis
Python 3.10 ou supérieur + pip

### 2. Installer les dépendances
```bash
cd microfinance_risk
pip install -r requirements.txt
```

### 3. Initialiser le projet
```bash
python setup.py
```
Ce script : migre la DB, entraîne le modèle ML, crée le compte admin, insère les données de démo.

### 4. Lancer le serveur
```bash
python manage.py runserver
```

### 5. Ouvrir dans le navigateur
- Application : **http://127.0.0.1:8000**
- Admin Django : **http://127.0.0.1:8000/admin**
- Identifiants : `admin` / `admin123`

---

## Logique de décision — Architecture à deux niveaux

### Niveau 1 — Règles métier disqualifiantes (bloquantes)
Ces règles sont vérifiées **avant** tout calcul ML. Si l'une d'elles échoue,
le dossier est **automatiquement refusé**, quelle que soit la qualité du profil.

| Règle | Condition | Raison métier |
|-------|-----------|---------------|
| **Crédit en cours** | Client a ≥ 1 crédit non soldé | Un client ne peut cumuler deux crédits actifs |
| **Antécédent de défaut** | Client a eu un crédit en défaut | Historique de non-remboursement = risque éliminatoire |
| **Taux d'effort** | Mensualité > 40% du revenu | Seuil de soutenabilité : au-delà, le client ne peut plus vivre |
| **Ratio d'endettement** | Montant > 2× le revenu annuel | Montant hors proportion avec la capacité de remboursement |
| **Plafond absolu** | Montant > 18× le revenu mensuel | Protection absolue contre les montants aberrants |

**Exemple concret** :
- Revenu = 220 000 FCFA/mois
- Demande = 3 000 000 FCFA sur 6 mois
- Mensualité = 500 000 FCFA → 227% du revenu → **REFUSÉ** (taux d'effort)
- Montant max accordable sur 6 mois = 220 000 × 40% × 6 = **528 000 FCFA**

### Niveau 2 — Scoring ML (RandomForestClassifier)
Appliqué **uniquement si toutes les règles métier sont passées**.

**Features (9) :**
1. Âge du client
2. Revenu mensuel (FCFA)
3. Nombre de crédits antérieurs soldés
4. Nombre de retards sur crédits soldés
5. Ratio d'endettement (montant / revenu annuel)
6. Taux d'effort (mensualité / revenu mensuel)
7. Secteur d'activité (encodé)
8. Durée demandée (mois)
9. Multiple du revenu (montant / revenu mensuel)

**Résultat :**
- Score de fiabilité : 0–100
- Probabilité de défaut : 0–100%
- Niveau : Faible (< 25%), Moyen (25–55%), Élevé (> 55%)
- Recommandation automatique avec montant conseillé si risque moyen

---

## Calcul du montant maximum accordable

```
montant_max = min(
    revenu_mensuel × 40% × duree_mois,   # contrainte taux d'effort
    revenu_mensuel × 12 × 2,              # contrainte ratio endettement
    revenu_mensuel × 18                   # plafond absolu
)
```

L'interface affiche ce montant en temps réel lors de la saisie du formulaire.

---

## Données de démonstration

Le script `setup.py` crée 5 clients représentatifs :

| Client | Revenu | Situation | Statut |
|--------|--------|-----------|--------|
| Jean Mbala | 250 000 FCFA | 2 crédits soldés, 1 retard mineur | ✅ Éligible |
| Marie Ngono | 180 000 FCFA | 1 crédit soldé, aucun retard | ✅ Éligible |
| Paul Foko | 120 000 FCFA | **Crédit en cours actif** | 🚫 Bloqué |
| Sandrine Mboua | 95 000 FCFA | **Antécédent de défaut** | ⛔ Bloquée |
| Robert Talla | 320 000 FCFA | 1 crédit soldé, aucun retard | ✅ Éligible |

---

## Architecture du projet

```
microfinance_risk/
├── manage.py
├── setup.py                    ← Lancer en premier
├── requirements.txt
├── microfinance_risk/
│   ├── settings.py
│   └── urls.py
├── risk/
│   ├── models.py               ← Client, Credit, PredictionRisque
│   ├── ml_model.py             ← Règles métier + scoring RandomForest
│   ├── views.py                ← Vues Django + détection crédit en cours
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   ├── risk_model.pkl          ← Généré par setup.py
│   └── templates/risk/
│       ├── dashboard.html
│       ├── client_list.html
│       ├── client_form.html
│       ├── client_detail.html  ← Alertes blocage + calculateur temps réel
│       └── resultat.html       ← Détail du refus ou du score ML
└── templates/
    └── base.html
```

---

## Pour aller plus loin

- **PostgreSQL** : modifier `DATABASES` dans `settings.py`
- **Vraies données** : importer un CSV historique via `pandas` pour réentraîner le modèle
- **Export PDF** : ajouter `weasyprint` pour générer des rapports de décision
- **API REST** : exposer `predict_risk()` via Django REST Framework
- **Déploiement** : Railway, Render ou un VPS (Contabo, HostAfrica)

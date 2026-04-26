#!/usr/bin/env python
"""
Script de démarrage rapide — MicroFinance Risk
Initialise la base de données, entraîne le modèle ML et insère des données de démo.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'microfinance_risk.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from risk.models import Client, Credit
from datetime import date

print("=" * 58)
print("  MicroFinance Risk — Setup initial")
print("=" * 58)

print("\n[1/4] Application des migrations...")
call_command('migrate', verbosity=0)
print("      ✓ Base de données prête (SQLite)")

print("\n[2/4] Entraînement du modèle ML (3000 exemples)...")
# Supprime l'ancien modèle pour forcer le réentraînement
import os as _os
model_path = _os.path.join(_os.path.dirname(__file__), 'risk', 'risk_model.pkl')
if _os.path.exists(model_path):
    _os.remove(model_path)
from risk.ml_model import train_and_save_model
train_and_save_model()
print("      ✓ RandomForest entraîné (9 features, class_weight=balanced)")

print("\n[3/4] Création du compte admin...")
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@mfr.cm', 'admin123')
    print("      ✓ Superuser créé : admin / admin123")
else:
    print("      ✓ Admin déjà existant")

print("\n[4/4] Données de démonstration...")
if Client.objects.count() == 0:
    clients_data = [
        # Client avec bon profil — pas de crédit en cours
        dict(nom="Mbala", prenom="Jean", age=38, sexe="M", ville="Douala",
             telephone="+237 699 123 456", secteur_activite="commerce",
             revenu_mensuel=250_000),
        # Cliente avec crédit soldé propre
        dict(nom="Ngono", prenom="Marie", age=31, sexe="F", ville="Yaoundé",
             telephone="+237 677 234 567", secteur_activite="services",
             revenu_mensuel=180_000),
        # Client avec crédit EN COURS — bloqué pour nouveau crédit
        dict(nom="Foko", prenom="Paul", age=45, sexe="M", ville="Bafoussam",
             telephone="+237 655 345 678", secteur_activite="agriculture",
             revenu_mensuel=120_000),
        # Cliente avec antécédent de défaut — bloquée
        dict(nom="Mboua", prenom="Sandrine", age=29, sexe="F", ville="Douala",
             telephone="+237 690 456 789", secteur_activite="artisanat",
             revenu_mensuel=95_000),
        # Client salarié, profil solide
        dict(nom="Talla", prenom="Robert", age=42, sexe="M", ville="Garoua",
             telephone="+237 666 567 890", secteur_activite="salarie",
             revenu_mensuel=320_000),
    ]

    credits_data = [
        # Jean Mbala — deux crédits soldés sans retard → éligible
        (0, dict(montant=300_000, duree_mois=12, date_debut=date(2022, 3, 1),
                 statut='solde', nb_retards=0, jours_retard_max=0)),
        (0, dict(montant=500_000, duree_mois=12, date_debut=date(2023, 4, 1),
                 statut='solde', nb_retards=1, jours_retard_max=8)),
        # Marie Ngono — un crédit soldé sans retard → éligible
        (1, dict(montant=200_000, duree_mois=12, date_debut=date(2023, 1, 1),
                 statut='solde', nb_retards=0, jours_retard_max=0)),
        # Paul Foko — crédit EN COURS → bloqué
        (2, dict(montant=400_000, duree_mois=24, date_debut=date(2024, 1, 1),
                 statut='en_cours', nb_retards=2, jours_retard_max=20)),
        # Sandrine Mboua — crédit en DÉFAUT → bloquée
        (3, dict(montant=150_000, duree_mois=6, date_debut=date(2023, 2, 1),
                 statut='defaut', nb_retards=5, jours_retard_max=60)),
        # Robert Talla — crédit soldé + aucun retard → éligible
        (4, dict(montant=1_000_000, duree_mois=24, date_debut=date(2022, 1, 1),
                 statut='solde', nb_retards=0, jours_retard_max=0)),
    ]

    clients = [Client.objects.create(**d) for d in clients_data]
    for idx, credit_kwargs in credits_data:
        Credit.objects.create(client=clients[idx], **credit_kwargs)

    print(f"      ✓ {len(clients)} clients créés :")
    print("        - Jean Mbala    : 2 crédits soldés → ÉLIGIBLE")
    print("        - Marie Ngono   : 1 crédit soldé   → ÉLIGIBLE")
    print("        - Paul Foko     : crédit EN COURS  → BLOQUÉ")
    print("        - Sandrine Mboua: crédit DÉFAUT    → BLOQUÉE")
    print("        - Robert Talla  : crédit soldé     → ÉLIGIBLE")
else:
    print("      ✓ Données déjà présentes")

print("\n" + "=" * 58)
print("  ✅ Setup terminé ! Lancez le serveur :")
print()
print("     python manage.py runserver")
print()
print("  Ouvrir : http://127.0.0.1:8000")
print("  Admin  : http://127.0.0.1:8000/admin  (admin / admin123)")
print("=" * 58 + "\n")

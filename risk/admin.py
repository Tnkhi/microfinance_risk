from django.contrib import admin
from .models import Client, Credit, PredictionRisque


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'age', 'ville', 'secteur_activite', 'revenu_mensuel', 'date_creation']
    search_fields = ['nom', 'prenom', 'ville', 'telephone']
    list_filter = ['secteur_activite', 'sexe', 'ville']


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ['client', 'montant', 'duree_mois', 'statut', 'nb_retards', 'date_debut']
    list_filter = ['statut']
    search_fields = ['client__nom', 'client__prenom']


@admin.register(PredictionRisque)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['client', 'score_fiabilite', 'niveau_risque', 'probabilite_defaut', 'date_prediction']
    list_filter = ['niveau_risque']
    readonly_fields = ['date_prediction']

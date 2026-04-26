from django import forms
from .models import Client, Credit


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'age', 'sexe', 'ville',
                  'telephone', 'secteur_activite', 'revenu_mensuel']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'prenom': forms.TextInput(attrs={'placeholder': 'Prénom'}),
            'age': forms.NumberInput(attrs={'min': 18, 'max': 80}),
            'telephone': forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX'}),
            'ville': forms.TextInput(attrs={'placeholder': 'Ex: Douala, Yaoundé...'}),
            'revenu_mensuel': forms.NumberInput(attrs={
                'placeholder': 'Revenu mensuel en FCFA',
                'min': 10000,
                'step': 5000
            }),
        }
        labels = {
            'nom': 'Nom',
            'prenom': 'Prénom',
            'age': 'Âge',
            'sexe': 'Sexe',
            'ville': 'Ville',
            'telephone': 'Téléphone',
            'secteur_activite': "Secteur d'activité",
            'revenu_mensuel': 'Revenu mensuel (FCFA)',
        }


class EvaluationForm(forms.Form):
    client_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    montant_demande = forms.FloatField(
        label='Montant demandé (FCFA)',
        min_value=10000,
        max_value=50000000,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex: 500000',
            'step': 10000,
            'id': 'id_montant_demande',
        })
    )
    duree_mois = forms.ChoiceField(
        label='Durée du remboursement',
        choices=[
            (6, '6 mois'),
            (12, '12 mois'),
            (18, '18 mois'),
            (24, '24 mois'),
            (36, '36 mois'),
        ],
        widget=forms.Select(attrs={'id': 'id_duree_mois'}),
    )
    nb_credits_anterieurs = forms.IntegerField(widget=forms.HiddenInput, initial=0)
    nb_retards_anterieurs = forms.IntegerField(widget=forms.HiddenInput, initial=0)


class CreditForm(forms.ModelForm):
    class Meta:
        model = Credit
        fields = ['montant', 'duree_mois', 'taux_interet', 'date_debut',
                  'statut', 'nb_retards', 'jours_retard_max']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'montant': forms.NumberInput(attrs={'step': 10000, 'min': 10000}),
        }
        labels = {
            'montant': 'Montant (FCFA)',
            'duree_mois': 'Durée (mois)',
            'taux_interet': 'Taux mensuel (%)',
            'date_debut': 'Date de début',
            'statut': 'Statut',
            'nb_retards': 'Nombre de retards',
            'jours_retard_max': 'Retard max (jours)',
        }

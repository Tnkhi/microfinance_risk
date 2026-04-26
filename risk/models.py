from django.db import models


class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    age = models.IntegerField()
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    ville = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    secteur_activite = models.CharField(max_length=100, choices=[
        ('commerce', 'Commerce'),
        ('agriculture', 'Agriculture'),
        ('transport', 'Transport'),
        ('artisanat', 'Artisanat'),
        ('services', 'Services'),
        ('salarie', 'Salarié'),
        ('autre', 'Autre'),
    ])
    revenu_mensuel = models.FloatField(help_text="En FCFA")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Credit(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='credits')
    montant = models.FloatField(help_text="Montant du crédit en FCFA")
    duree_mois = models.IntegerField(help_text="Durée en mois")
    taux_interet = models.FloatField(default=2.5, help_text="Taux mensuel en %")
    date_debut = models.DateField()
    statut = models.CharField(max_length=20, choices=[
        ('en_cours', 'En cours'),
        ('solde', 'Soldé'),
        ('defaut', 'Défaut de paiement'),
    ], default='en_cours')
    nb_retards = models.IntegerField(default=0, help_text="Nombre de retards de paiement")
    jours_retard_max = models.IntegerField(default=0, help_text="Retard maximum en jours")

    def __str__(self):
        return f"Crédit {self.id} – {self.client}"

    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"


class PredictionRisque(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='predictions')
    date_prediction = models.DateTimeField(auto_now_add=True)

    # Résultat principal
    eligible = models.BooleanField(default=True, help_text="Passe toutes les règles métier")
    score_fiabilite = models.FloatField(null=True, blank=True, help_text="Score ML entre 0 et 100 (null si refusé)")
    niveau_risque = models.CharField(max_length=20, choices=[
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('eleve', 'Élevé'),
        ('refuse', 'Refusé'),
    ])
    probabilite_defaut = models.FloatField(null=True, blank=True, help_text="Probabilité de défaut (null si refusé)")
    recommandation = models.TextField()
    blocages_json = models.TextField(default='[]', help_text="Règles bloquantes sérialisées JSON")

    # Paramètres de la demande
    montant_demande = models.FloatField(help_text="Montant demandé en FCFA")
    duree_mois_input = models.IntegerField(default=12)
    mensualite = models.FloatField(default=0, help_text="Mensualité calculée en FCFA")
    taux_effort = models.FloatField(default=0, help_text="Mensualité / revenu en %")
    ratio_endettement = models.FloatField(default=0)
    montant_max_accordable = models.FloatField(default=0)

    # Profil utilisé pour l'audit
    age_input = models.IntegerField()
    revenu_input = models.FloatField()
    nb_credits_anterieurs = models.IntegerField()
    nb_retards_anterieurs = models.IntegerField()

    class Meta:
        verbose_name = "Prédiction de risque"
        verbose_name_plural = "Prédictions de risque"
        ordering = ['-date_prediction']

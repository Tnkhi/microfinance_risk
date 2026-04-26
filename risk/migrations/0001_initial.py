from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('age', models.IntegerField()),
                ('sexe', models.CharField(choices=[('M', 'Masculin'), ('F', 'Féminin')], max_length=1)),
                ('ville', models.CharField(max_length=100)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('secteur_activite', models.CharField(choices=[
                    ('commerce', 'Commerce'), ('agriculture', 'Agriculture'),
                    ('transport', 'Transport'), ('artisanat', 'Artisanat'),
                    ('services', 'Services'), ('salarie', 'Salarié'), ('autre', 'Autre'),
                ], max_length=100)),
                ('revenu_mensuel', models.FloatField()),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Client', 'verbose_name_plural': 'Clients'},
        ),
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.FloatField()),
                ('duree_mois', models.IntegerField()),
                ('taux_interet', models.FloatField(default=2.5)),
                ('date_debut', models.DateField()),
                ('statut', models.CharField(choices=[
                    ('en_cours', 'En cours'), ('solde', 'Soldé'), ('defaut', 'Défaut de paiement'),
                ], default='en_cours', max_length=20)),
                ('nb_retards', models.IntegerField(default=0)),
                ('jours_retard_max', models.IntegerField(default=0)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='risk.client')),
            ],
            options={'verbose_name': 'Crédit', 'verbose_name_plural': 'Crédits'},
        ),
        migrations.CreateModel(
            name='PredictionRisque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_prediction', models.DateTimeField(auto_now_add=True)),
                ('score_fiabilite', models.FloatField()),
                ('niveau_risque', models.CharField(choices=[
                    ('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Élevé'),
                ], max_length=20)),
                ('probabilite_defaut', models.FloatField()),
                ('recommandation', models.TextField()),
                ('montant_demande', models.FloatField()),
                ('age_input', models.IntegerField()),
                ('revenu_input', models.FloatField()),
                ('nb_credits_anterieurs', models.IntegerField()),
                ('nb_retards_anterieurs', models.IntegerField()),
                ('ratio_endettement', models.FloatField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='risk.client')),
            ],
            options={'verbose_name': 'Prédiction de risque', 'verbose_name_plural': 'Prédictions de risque', 'ordering': ['-date_prediction']},
        ),
    ]

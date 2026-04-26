from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictionrisque',
            name='eligible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='predictionrisque',
            name='blocages_json',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='predictionrisque',
            name='duree_mois_input',
            field=models.IntegerField(default=12),
        ),
        migrations.AddField(
            model_name='predictionrisque',
            name='mensualite',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='predictionrisque',
            name='taux_effort',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='predictionrisque',
            name='montant_max_accordable',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='predictionrisque',
            name='score_fiabilite',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='predictionrisque',
            name='probabilite_defaut',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='predictionrisque',
            name='niveau_risque',
            field=models.CharField(max_length=20, choices=[
                ('faible', 'Faible'), ('moyen', 'Moyen'),
                ('eleve', 'Élevé'), ('refuse', 'Refusé'),
            ]),
        ),
    ]

# Generated by Django 4.2.13 on 2024-07-05 15:44

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnneeScolaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('nom', models.CharField(max_length=100)),
                ('nom_bref', models.CharField(default='', max_length=10)),
                ('date_initiale', models.DateField(blank=True)),
                ('date_finale', models.DateField(blank=True)),
                ('actuel', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Classe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('nom', models.CharField(max_length=10)),
                ('legacy_id', models.CharField(blank=True, db_index=True, max_length=100, null=True, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Ecole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('nom', models.CharField(max_length=100)),
                ('ville', models.CharField(max_length=100)),
                ('nom_du_referent', models.CharField(max_length=100)),
                ('prenom_du_referent', models.CharField(max_length=100)),
                ('email_du_referent', models.CharField(max_length=100)),
                ('telephone_du_referent', models.CharField(max_length=100)),
                ('note', models.TextField()),
                ('externe', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Eleve',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('nom', models.CharField(max_length=34)),
                ('prenom', models.CharField(max_length=34)),
                ('date_enquete', models.DateField(blank=True, null=True)),
                ('condition_eleve', models.CharField(choices=[('CONF', 'CONF'), ('ABAN', 'ABAN'), ('PROP', 'PROP')], max_length=4)),
                ('sex', models.CharField(choices=[('F', 'F'), ('M', 'M')], max_length=1)),
                ('date_naissance', models.DateField(blank=True, null=True)),
                ('cs_py', models.CharField(choices=[('C', 'CS'), ('E', 'EXTRA'), ('P', 'PY'), ('A', 'ACC'), ('B', 'BRAVO')], default='C', max_length=7)),
                ('hand', models.CharField(blank=True, choices=[('DA', 'DA'), ('DM', 'DM'), ('DL', 'DL'), ('DV', 'DV')], max_length=2, null=True)),
                ('annee_inscr', models.SmallIntegerField(blank=True, null=True)),
                ('parent', models.CharField(blank=True, max_length=100, null=True)),
                ('tel_parent', models.CharField(blank=True, max_length=100, null=True)),
                ('note_eleve', models.TextField(blank=True, default='-', null=True)),
                ('legacy_id', models.CharField(blank=True, db_index=True, max_length=100, null=True, unique=True)),
            ],
            options={
                'verbose_name': 'Eleve',
                'verbose_name_plural': 'Eleves',
            },
        ),
        migrations.CreateModel(
            name='Inscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('date_inscription', models.DateTimeField(default=django.utils.timezone.now)),
                ('nombre_uniformes', models.IntegerField(default=0)),
                ('annee_scolaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scuelo.anneescolaire')),
                ('classe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scuelo.classe')),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scuelo.eleve')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TypeClasse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('nom', models.CharField(max_length=100)),
                ('ordre', models.IntegerField(default=0)),
                ('type_ecole', models.CharField(choices=[('M', 'MATERNELLE'), ('P', 'PRIMAIRE'), ('S', 'SECONDAIRE'), ('L', 'LYCEE')], db_index=True, max_length=1)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tarif',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('causal', models.CharField(choices=[('INS', 'Inscription'), ('SCO1', 'Scolarite 1'), ('SCO2', 'Scolarite 2'), ('SCO3', 'Scolarite 3'), ('TEN', 'Tenue'), ('CAN', 'Cantine')], db_index=True, max_length=5)),
                ('montant', models.PositiveBigIntegerField()),
                ('date_expiration', models.DateField(verbose_name="Date d'expiration")),
                ('annee_scolaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scuelo.anneescolaire')),
                ('classe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scuelo.classe')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Mouvement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('type', models.CharField(choices=[('R', 'Revenus'), ('D', 'Dépenses')], db_index=True, max_length=1)),
                ('destination', models.CharField(choices=[('A', 'A'), ('B', 'B')], db_index=True, max_length=1)),
                ('causal', models.CharField(blank=True, choices=[('INS', 'Inscription'), ('SCO', 'Scolarite'), ('TEN', 'Tenue'), ('CAN', 'Cantine')], db_index=True, max_length=5, null=True)),
                ('montant', models.PositiveBigIntegerField()),
                ('date_paye', models.DateField(db_index=True, default='')),
                ('note', models.CharField(blank=True, max_length=200, null=True)),
                ('legacy_id', models.CharField(blank=True, db_index=True, max_length=100, null=True, unique=True)),
                ('inscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scuelo.inscription')),
            ],
            options={
                'verbose_name': 'Mouvement',
                'verbose_name_plural': 'Mouvements',
                'ordering': ['-date_paye'],
            },
        ),
        migrations.AddField(
            model_name='classe',
            name='ecole',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scuelo.ecole'),
        ),
        migrations.AddField(
            model_name='classe',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scuelo.typeclasse'),
        ),
    ]
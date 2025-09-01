from django.core.management.base import BaseCommand
from scuelo.models import Classe, AnneeScolaire, Ecole
from django.utils import timezone
from cash.models import Tarif
from datetime import datetime
import openpyxl
from openpyxl.styles import Font
import io


ECOLES_MANUELLES_NAMES = {
    'M': "École Maternelle Centre social de Nasara",
    'P': "École primaire Centre social de Nasara",
    'L': "École Secondaire Centre social de Nasara",
}


class Command(BaseCommand):
    help = "Uploader les tarifs dans les classes de l'année scolaire actuelle et simuler un export Excel."

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Faire une simulation et exporter un fichier Excel sans créer les tarifs en base.',
        )

    def handle(self, *args, **options):
        simulate = options['simulate']

        # Récupérer l'année scolaire actuelle
        try:
            annee_scolaire = AnneeScolaire.objects.get(actuel=True)
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Aucune année scolaire actuelle trouvée."))
            return

        ec_list = Ecole.objects.filter(nom__in=ECOLES_MANUELLES_NAMES.values())
        if not ec_list.exists():
            self.stdout.write(self.style.ERROR("Aucune école trouvée avec les noms spécifiés."))
            return

        expiration_dates = {
            'SCO1': datetime(annee_scolaire.date_initiale.year, 11, 30),
            'SCO2': datetime(annee_scolaire.date_initiale.year + 1, 1, 31),
            'SCO3': datetime(annee_scolaire.date_initiale.year + 1, 2, 28),
        }

        simulations = []

        for ecole in ec_list:
            classes = Classe.objects.filter(ecole=ecole)
            if not classes.exists():
                self.stdout.write(self.style.WARNING(f"Aucune classe dans l'école {ecole.nom}"))
                continue

            for classe in classes:
                tarifs = self.tarifs_par_classe(classe.nom)
                if not tarifs:
                    self.stdout.write(self.style.WARNING(f'Pas de tarifs définis pour la classe {classe.nom}'))
                    continue

                if simulate:
                    simulations.append({
                        'classe': classe,
                        'annee_scolaire': annee_scolaire,
                        'tarifs': tarifs,
                    })
                else:
                    self.create_class_tariffs(classe, tarifs, annee_scolaire, expiration_dates)
                    self.stdout.write(self.style.SUCCESS(f'Tarifs ajoutés à la classe {classe.nom} de l\'école {ecole.nom}'))

        if simulate:
            stream = self.exporter_simulation_excel(simulations)
            filename = 'simulation_tarifs.xlsx'
            with open(filename, 'wb') as f:
                f.write(stream.read())
            self.stdout.write(self.style.SUCCESS(f"Simulation exportée dans {filename}"))

    def tarifs_par_classe(self, class_name):
        tarifs_init = {
            # Tarif spécial pour la 6ème
            '6me': {'SCO1': 32000, 'SCO2': 15000, 'SCO3': 15000},
            # Autres classes exemple initial
            'CP1': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CP2-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE1-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE2-Nas_Pri': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM1': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM2': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'PS': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
            'MS-Nas_Mat': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
            'GS-Nas_Mat': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
        }
        return tarifs_init.get(class_name)

    def create_class_tariffs(self, classe, tariffs, annee_scolaire, expiration_dates):
        # Tarif d'inscription
        Tarif.objects.get_or_create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal='INS',
            defaults={
                'montant': 500,
                'date_expiration': timezone.now() + timezone.timedelta(days=90)
            }
        )
        for causal, montant in tariffs.items():
            if causal not in ['TEN', 'CAN']:
                Tarif.objects.get_or_create(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    causal=causal,
                    defaults={
                        'montant': montant,
                        'date_expiration': expiration_dates.get(causal, timezone.now() + timezone.timedelta(days=90)).date()
                    }
                )
            else:
                Tarif.objects.get_or_create(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    causal=causal,
                    defaults={
                        'montant': montant,
                        'date_expiration': (timezone.now() + timezone.timedelta(days=90)).date()
                    }
                )

    def exporter_simulation_excel(self, simulations):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Simulation Tarifs"

        headers = ['Classe', 'Année Scolaire', 'SCO1', 'SCO2', 'SCO3', 'TEN', 'CAN', 'INS']
        ws.append(headers)

        bold_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = bold_font

        for sim in simulations:
            classe = sim['classe']
            annee = sim['annee_scolaire']
            tarifs = sim.get('tarifs', {})
            row = [
                classe.nom,
                annee.nom,
                tarifs.get('SCO1', ''),
                tarifs.get('SCO2', ''),
                tarifs.get('SCO3', ''),
                tarifs.get('TEN', ''),
                tarifs.get('CAN', ''),
                tarifs.get('INS', 500),
            ]
            ws.append(row)

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

from django.core.management.base import BaseCommand
from django.utils import timezone
from scuelo.models import Classe, AnneeScolaire, Tarif

class Command(BaseCommand):
    help = 'Registers deadlines for different types of fees'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to register deadlines...')

        # Sample data structure: (type, amount, class_name, year_name, deadline)
        deadlines = [
            # Primary School
            ('INS', 15000, 'CP1', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CP1', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CP1', '2023-2024', '2024-01-31'),

            ('INS', 15000, 'CP2', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CP2', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CP2', '2023-2024', '2024-01-31'),

            ('INS', 15000, 'CE1', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CE1', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CE1', '2023-2024', '2024-01-31'),

            ('INS', 15000, 'CE2', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CE2', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CE2', '2023-2024', '2024-01-31'),

            ('INS', 17500, 'CM1', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CM1', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CM1', '2023-2024', '2024-01-31'),

            ('INS', 17500, 'CM2', '2023-2024', '2023-10-01'),
            ('SCO1', 7500, 'CM2', '2023-2024', '2023-11-30'),
            ('SCO2', 7500, 'CM2', '2023-2024', '2024-01-31'),

            ('TEN', 4500, 'CP1', '2023-2024', '2023-11-01'),
            ('TEN', 4500, 'CP2', '2023-2024', '2023-11-01'),
            ('TEN', 4500, 'CE1', '2023-2024', '2023-11-01'),
            ('TEN', 4500, 'CE2', '2023-2024', '2023-11-01'),
            ('TEN', 4500, 'CM1', '2023-2024', '2023-11-01'),
            ('TEN', 4500, 'CM2', '2023-2024', '2023-11-01'),

            # Preschool (Maternelle)
            ('INS', 500, 'PS', '2023-2024', '2023-09-23'),
            ('SCO1', 10000, 'PS', '2023-2024', '2023-11-30'),
            ('SCO2', 8000, 'PS', '2023-2024', '2023-01-31'),
            ('SCO3', 7000, 'PS', '2023-2024', '2024-01-31'),
            ('TEN', 4000, 'PS', '2023-2024', '2023-11-01'),
            ('CAN', 4000, 'PS', '2023-2024', '2023-12-01'),

            ('INS', 500, 'MS', '2023-2024', '2023-09-23'),
            ('SCO1', 10000, 'MS', '2023-2024', '2023-11-30'),
            ('SCO2', 8000, 'MS', '2023-2024', '2023-01-31'),
            ('SCO3', 7000, 'MS', '2023-2024', '2024-01-31'),
            ('TEN', 4000, 'MS', '2023-2024', '2023-11-01'),
            ('CAN', 4000, 'MS', '2023-2024', '2023-12-01'),

            ('INS', 500, 'GS', '2023-2024', '2023-09-23'),
            ('SCO1', 10000, 'GS', '2023-2024', '2023-11-30'),
            ('SCO2', 8000,'GS', '2023-2024', '2023-01-31'),
            ('SCO3', 7000, 'GS', '2023-2024', '2024-01-31'),
            ('TEN', 4000, 'GS', '2023-2024', '2023-11-01'),
            ('CAN', 4000, 'GS' , '2023-2024', '2023-12-01'),
        ]

        for causal, montant, class_name, year_name, deadline in deadlines:
            try:
                classe = Classe.objects.get(nom=class_name)
                annee_scolaire, created = AnneeScolaire.objects.get_or_create(
                    nom=year_name,
                    defaults={
                        'date_initiale': timezone.now(),
                        'date_finale': timezone.now() + timezone.timedelta(days=365),
                        'actuel': False
                    }
                )
                tarif, created = Tarif.objects.get_or_create(
                    causal=causal,
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    defaults={
                        'montant': montant,
                        'date_expiration': deadline
                    }
                )
                if not created:
                    tarif.montant = montant
                    tarif.date_expiration = deadline
                    tarif.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully registered/updated {causal} for {class_name} in {year_name}'))
            except Classe.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Class {class_name} does not exist'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error registering {causal} for {class_name} in {year_name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Finished registering deadlines'))

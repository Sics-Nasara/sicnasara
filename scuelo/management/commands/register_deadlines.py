from django.core.management.base import BaseCommand
from django.utils import timezone
from scuelo.models import Classe, AnneeScolaire, Tarif

class Command(BaseCommand):
    help = 'Registers deadlines for different types of fees'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to register deadlines...')

        # Sample data structure: (type, amount, class_name, year_name, deadline)
        deadlines = [
            ('INS', 10000, 'CP1', '2023-2024', '2023-10-01'),
            ('SCO1', 20000, 'CP2', '2023-2024', '2023-12-01'),
            ('SCO2', 15000, 'CE1', '2023-2024', '2024-02-01'),
            ('SCO3', 12000, 'CE2', '2023-2024', '2024-04-01'),
            ('TEN', 5000, 'CM1', '2023-2024', '2023-11-01'),
            ('CAN', 7000, 'CM2', '2023-2024', '2024-01-01'),
            # Add more as needed
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

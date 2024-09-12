from django.core.management.base import BaseCommand
from scuelo.models import Classe, Tarif, AnneeScolaire
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = "Upload tariffs into classes for the 2023-2024 school year."

    def handle(self, *args, **options):
        # Get the current school year
        try:
            annee_scolaire = AnneeScolaire.objects.get(nom='Année scolaire 2023-24')
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Année scolaire 2023-24 not found."))
            return

        # Define primary school tariffs with specific expiration dates
        primary_tariffs = {
            'CP1': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CP2': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CE1': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CE2': {'scolarite_1': 15000, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CM1': {'scolarite_1': 17500, 'scolarite_2': 7500, 'scolarite_3': 7500},
            'CM2': {'scolarite_1': 17500, 'scolarite_2': 7500, 'scolarite_3': 7500},
        }

        # Dates for each payment
        expiration_dates = {
            'SCO1': datetime(2024, 11, 30),
            'SCO2': datetime(2025, 1, 31),
            'SCO3': datetime(2025, 2, 28)
        }

        # Upload tariffs for primary classes
        for class_name, tarifs in primary_tariffs.items():
            try:
                classe = Classe.objects.filter(nom=class_name).first()

                if not classe:
                    self.stdout.write(self.style.ERROR(f'Class {class_name} not found'))
                    continue

                # Create tariff entries for each type of payment
                self.create_tarif(classe, 'INS', 500, annee_scolaire, None)  # Inscription fee is 500 for all
                self.create_tarif(classe, 'SCO1', tarifs['scolarite_1'], annee_scolaire, expiration_dates['SCO1'])
                self.create_tarif(classe, 'SCO2', tarifs['scolarite_2'], annee_scolaire, expiration_dates['SCO2'])
                self.create_tarif(classe, 'SCO3', tarifs['scolarite_3'], annee_scolaire, expiration_dates['SCO3'])

                # Log the result
                self.stdout.write(self.style.SUCCESS(f'Tariffs uploaded for {class_name}'))

            except Classe.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(f'Multiple classes found with the name {class_name}, please refine the query'))

    def create_tarif(self, classe, causal, montant, annee_scolaire, expiration_date):
        """Helper function to create a Tarif entry for a class"""
        Tarif.objects.get_or_create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal=causal,
            defaults={
                'montant': montant,
                'date_expiration': expiration_date or timezone.now() + timezone.timedelta(days=90)
            }
        )

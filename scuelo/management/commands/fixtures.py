# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User, Permission
from scuelo.models import Ecole, Classe, AnneeScolaire, TypeClasse

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,  # Log INFO and above
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("class_setup.log"),  # Save logs to file
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger(__name__)

def attribuer_tous_autorisations(groups, modelli):
    """Assign all permissions for models to specific groups."""
    if not isinstance(groups, list):
        groups = [groups]
    for group in groups:
        for permesso in modelli:
            for p in Permission.objects.filter(content_type__app_label=permesso['app_label'],
                                               content_type__model=permesso['model']):
                if p not in group.permissions.all():
                    group.permissions.add(p)

class Command(BaseCommand):
    help = '''Inserts class data'''

    def handle(self, *args, **options):
        try:
          

            # Insert school years
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2024-25', date_initiale='2024-09-01', date_finale='2025-06-01', actuel=True)
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2023-24', date_initiale='2023-09-01', date_finale='2024-06-01', actuel=False)
            
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2019-20', date_initiale='2019-09-01', date_finale='2020-06-01', actuel=False)
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2020-21', date_initiale='2020-09-01', date_finale='2021-06-01', actuel=False)
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2021-22', date_initiale='2021-09-01', date_finale='2022-06-01', actuel=False)
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2022-23', date_initiale='2022-09-01', date_finale='2023-06-01', actuel=False)
            AnneeScolaire.objects.get_or_create(nom='NULL', date_initiale=None, date_finale=None, actuel=False)
            AnneeScolaire.objects.get_or_create(
                nom='NULL',
                date_initiale='1900-01-01',  # Placeholder date
                date_finale='1900-01-01',     # Placeholder date
                actuel=False
            )

            logger.info("School years created successfully.")

            # Create groups and users
            gr_operateur, _ = Group.objects.get_or_create(name='Opérateur')

            # Create superuser
            superuser, _ = User.objects.get_or_create(username='superuser', defaults={
                'first_name': 'Super',
                'last_name': 'User',
                'is_superuser': True,
                'is_staff': True, 
                'email': 'davide@c4k.it'
            })
            superuser.set_password('3g3rKD8naG')
            superuser.save()

            logger.info("Superuser created successfully.")

            # Create operator
            operateur, _ = User.objects.get_or_create(username='operateur', defaults={
                'first_name': 'Operateur',
                'last_name': 'Sics Nassara',
                'is_staff': True,
                'email': 'davide@c4k.it'
            })
            operateur.set_password('3g3rKD8naG')
            operateur.groups.add(gr_operateur)
            operateur.save()

            logger.info("Operator created successfully.")

            # Set permissions
            modelli_autorisations_complet = [
                {'app_label': 'scuelo', 'model': 'classe'},
                {'app_label': 'scuelo', 'model': 'eleve'},
                {'app_label': 'scuelo', 'model': 'anneescolaire'},
                {'app_label': 'scuelo', 'model': 'inscription'},
                {'app_label': 'scuelo', 'model': 'paiement'}
            ]
            groupes_autorisations_complet = [gr_operateur]
            attribuer_tous_autorisations(groupes_autorisations_complet, modelli_autorisations_complet)

            logger.info("Permissions assigned successfully.")

        except Exception as ex:
            logger.error(f'Error during fixture setup: {str(ex)}')
            self.stdout.write(self.style.ERROR(f"Error: {str(ex)}"))

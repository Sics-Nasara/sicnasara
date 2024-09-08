# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User, Permission

from scuelo.models import Ecole, Classe, AnneeScolaire, TypeClasse

logger = logging.getLogger(__name__)


def attribuer_tous_autorisations(groups, modelli):
    if not type(groups) is list:
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
            # TODO set appropriate type_ecole, mine is just a guess
            ps, _ = TypeClasse.objects.get_or_create(nom='PS', ordre=1, type_ecole='M')
            ms, _ = TypeClasse.objects.get_or_create(nom='MS', ordre=2, type_ecole='M')
            gs, _ = TypeClasse.objects.get_or_create(nom='GS', ordre=3, type_ecole='M')
            cp1, _ = TypeClasse.objects.get_or_create(nom='CP1', ordre=4, type_ecole='P')
            cp2, _ = TypeClasse.objects.get_or_create(nom='CP2', ordre=5, type_ecole='P')
            ce1, _ = TypeClasse.objects.get_or_create(nom='CE1', ordre=6, type_ecole='P')
            ce2, _ = TypeClasse.objects.get_or_create(nom='CE2', ordre=7, type_ecole='P')
            cm1, _ = TypeClasse.objects.get_or_create(nom='CM1', ordre=8, type_ecole='P')
            cm2, _ = TypeClasse.objects.get_or_create(nom='CM2', ordre=9, type_ecole='P')
            me6, _ = TypeClasse.objects.get_or_create(nom='6me', ordre=10, type_ecole='S')
            me5, _ = TypeClasse.objects.get_or_create(nom='5me', ordre=11, type_ecole='S')
            me4, _ = TypeClasse.objects.get_or_create(nom='4me', ordre=12, type_ecole='S')
            me3, _ = TypeClasse.objects.get_or_create(nom='3me', ordre=13, type_ecole='S')
            me2, _ = TypeClasse.objects.get_or_create(nom='2me', ordre=14, type_ecole='L')
            me1, _ = TypeClasse.objects.get_or_create(nom='1me', ordre=15, type_ecole='L')
            term, _ = TypeClasse.objects.get_or_create(nom='Term', ordre=16, type_ecole='L')

            ecole_interne, _ = Ecole.objects.get_or_create(nom= 'Bisongo du coeur', ville='', nom_du_referent='', prenom_du_referent='', email_du_referent='', telephone_du_referent='', note='', externe=False)
            #ecole_externe_1, _ = Ecole.objects.get_or_create(nom= '', ville='', nom_du_referent='', prenom_du_referent='', email_du_referent='', telephone_du_referent='', note='')
            #ecole_externe_2, _ = Ecole.objects.get_or_create(nom= '', ville='', nom_du_referent='', prenom_du_referent='', email_du_referent='', telephone_du_referent='', note='')

            Classe.objects.get_or_create(ecole=ecole_interne, type=ps, nom='PS',  legacy_id= '_PK-PS-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=ms, nom='MS',  legacy_id= '_PK-MS-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=gs, nom='GS',  legacy_id= '_PK-GS-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=cp1, nom='CP1', legacy_id= '_PK-CP1-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=cp2, nom='CP2', legacy_id= '_PK-CP2-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=ce1, nom='CE1', legacy_id= '_PK-CE1-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=ce2, nom='CE2', legacy_id= '_PK-CE2-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=cm1, nom='CM1', legacy_id= '_PK-CM1-Nas')
            Classe.objects.get_or_create(ecole=ecole_interne, type=cm2, nom='CM2', legacy_id= '_PK-CM2-Nas')
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2023-24', date_initiale='2023-09-01',
                                                date_finale='2024-06-01', actuel=False)
            AnneeScolaire.objects.get_or_create(nom='Année scolaire 2024-25', date_initiale='2024-09-01',
                                                date_finale='2025-06-01', actuel=True)
            gr_operateur, _ = Group.objects.get_or_create(name='Opérateur')
            superuser, _ = User.objects.get_or_create(username='superuser',
                                                   first_name='Super',
                                                   last_name='User',
                                                   is_superuser=True,
                                                   is_staff=True,
                                                   email='davide@c4k.it')
            superuser.set_password('3g3rKD8naG')
            superuser.save()
            operateur, _ = User.objects.get_or_create(username='operateur',
                                                   first_name='Operateur',
                                                   last_name='Sics Nassara',
                                                   is_staff=True,
                                                   email='davide@c4k.it')
            operateur.set_password('3g3rKD8naG')
            operateur.groups.add(gr_operateur)
            operateur.save()
            modelli_autorisations_complet = [
                {'app_label': 'scuelo', 'model': 'classe'},
                {'app_label': 'scuelo', 'model': 'eleve'},
                {'app_label': 'scuelo', 'model': 'anneescolaire'},
                {'app_label': 'scuelo', 'model': 'inscription'},
                {'app_label': 'scuelo', 'model': 'paiement'}
            ]
            groupes_autorisations_complet = [
                gr_operateur
            ]
            attribuer_tous_autorisations(groupes_autorisations_complet, modelli_autorisations_complet)

        except Exception as ex:
            logger.error('fixtures: %s' % str(ex))
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from openpyexcel import load_workbook
from pathlib import Path

from scuelo.models import AnneeScolaire, Eleve, Inscription, Classe, Mouvement


class Command(BaseCommand):
    help = '''Imports data from "Export SICS 2.1.75.xlsx" file.'''

    def handle(self, *args, **options):
        BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
        full_path = '%s/export_sics/External students.xlsx' % BASE_DIR
        print('Import SICS START %s' % full_path)
        wb = load_workbook(full_path)
        '''
            Classe   already loaded by fixtures
            Eleve    import first
            Mouvement import second
        '''
        annee_scolaire_actuel = AnneeScolaire.objects.get(actuel=True)
        derniere_annee_scolaire = AnneeScolaire.objects.get(actuel=False)
        ws_scuole = wb.get_sheet_by_name('Scuole')
        for row in ws_scuole:
            try:
                new_c = Classe()
                new_c.nom = row[1].value
                new_c.save()
            except Exception as ex:
                print(str(ex))
        ws_classe = wb.get_sheet_by_name('Classe')
        
        ws_studente = wb.get_sheet_by_name('Studente')
        
        print('Import external students END %s' % full_path)
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from openpyexcel import Workbook, load_workbook
from pathlib import Path
from openpyexcel.styles import Alignment, Font
from openpyexcel.utils.cell import get_column_letter
from openpyexcel.styles.borders import Border, Side, BORDER_THIN, BORDER_THICK
from openpyexcel.worksheet.datavalidation import DataValidation
import openpyexcel.styles.colors

from scuelo.models import AnneeScolaire, Eleve, Inscription, Classe, Mouvement


class Command(BaseCommand):
    help = '''Imports data from "Export SICS 2.1.75.xlsx" file.'''

    def handle(self, *args, **options):
        BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
        full_path = '%s/export_sics/Export SICS 2.1.75.xlsx' % BASE_DIR
        print('Import SICS START %s' % full_path)
        wb = load_workbook(full_path)
        '''
            Classe   already loaded by fixtures
            Eleve    import first
            Mouvement import second
        '''
        annee_scolaire_actuel = AnneeScolaire.objects.get(actuel=True)
        derniere_annee_scolaire = AnneeScolaire.objects.get(actuel=False)
        ws_eleve = wb.get_sheet_by_name('Eleve')
        ws_paiement = wb.get_sheet_by_name('Paiement')
        columns_eleve = {}
        for row in ws_eleve:
            if len(columns_eleve.keys()) == 0:
                for column_index in range(0, len(row)):
                    columns_eleve[row[column_index].value] = column_index
            else:
                try:
                    if Classe.objects.filter(legacy_id=row[columns_eleve['__FK_Classe_ID']].value).exists():
                        new_e = Eleve()
                        new_e.legacy_id = row[columns_eleve['_PK_Eleve_ID']].value
                        new_e.date_enquete = row[columns_eleve['D_enquete']].value
                        new_e.nom = row[columns_eleve['Nom']].value
                        new_e.prenom = row[columns_eleve['Prenom']].value
                        new_e.condition_eleve = row[columns_eleve['Condition_eleve']].value
                        new_e.sex = row[columns_eleve['Sex']].value
                        new_e.date_naissance = row[columns_eleve['Date-Naissance']].value
                        new_e.cs_py = row[columns_eleve['CS_PY']].value
                        new_e.hand = row[columns_eleve['Hand']].value
                        new_e.annee_inscr = row[columns_eleve['A_inscr']].value
                        new_e.parent = row[columns_eleve['Parent']].value
                        new_e.tel_parent = row[columns_eleve['Tel_parent']].value
                        new_e.save()
                        i = Inscription()
                        i.eleve = new_e
                        i.annee_scolaire = derniere_annee_scolaire
                        if Classe.objects.filter(legacy_id=row[columns_eleve['__FK_Classe_ID']].value).exists():
                            i.classe = Classe.objects.get(legacy_id=row[columns_eleve['__FK_Classe_ID']].value)
                        i.save()
                except Exception as ex:
                    print(str(ex))
        columns_paiement = {}
        for row in ws_paiement:
            if len(columns_paiement.keys()) == 0:
                for column_index in range(0, len(row)):
                    columns_paiement[row[column_index].value] = column_index
            else:
                try:
                    new_p = Mouvement()
                    new_p.legacy_id = row[columns_paiement['_PK_Paiement_ID']].value
                    new_p.causal = row[columns_paiement['Causal_Paiement']].value
                    new_p.montant = row[columns_paiement['Montant']].value
                    new_p.date_paye = row[columns_paiement['Date_paiement']].value
                    new_p.note = row[columns_paiement['Note_Paiement']].value
                    eleve = Eleve.objects.get(legacy_id=row[columns_paiement['__FK_Eleve']].value)
                    new_p.inscription = Inscription.objects.get(annee_scolaire=derniere_annee_scolaire, eleve=eleve)
                    new_p.save()
                except Exception as ex:
                    print(str(ex))
        print('Import SICS END %s' % full_path)
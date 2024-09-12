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

from datetime import datetime

def parse_date(date_str):
    if isinstance(date_str, datetime):
        # If the value is already a datetime object, return the date part
        return date_str.date()
    
    if isinstance(date_str, str):
        try:
            # Try the standard YYYY-MM-DD format
            return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try the DD/MM/YYYY format
                return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
            except ValueError:
                # If both formats fail, return None
                return None
    # If it's neither a string nor a datetime object, return None
    return None

class Command(BaseCommand):
    help = '''Imports data from "Export SICS 2.1.75.xlsx" file.'''

    def handle(self, *args, **options):
        BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
        full_path = f'{BASE_DIR}/export_sics/Export SICS 2.1.75 V2.xlsx'
        print(f'Import SICS START {full_path}')
        
        try:
            wb = load_workbook(full_path)
        except FileNotFoundError:
            print(f"File not found: {full_path}")
            return
        
        annee_scolaire_actuel = AnneeScolaire.objects.get(actuel=True)
        derniere_annee_scolaire = AnneeScolaire.objects.filter(actuel=False).order_by('-date_initiale').first()

        if not derniere_annee_scolaire:
            print("No previous school year found.")
            return

        # Load worksheets
        ws_eleve = wb['Eleve']
        ws_paiement = wb['Paiement']

        # Process Eleve
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
                        new_e.date_enquete = parse_date(row[columns_eleve['D_enquete']].value)
                        new_e.nom = row[columns_eleve['Nom']].value
                        new_e.prenom = row[columns_eleve['Prenom']].value
                        new_e.condition_eleve = row[columns_eleve['Condition_eleve']].value
                        new_e.sex = row[columns_eleve['Sex']].value
                        new_e.date_naissance = parse_date(row[columns_eleve['Date-Naissance']].value)
                        new_e.cs_py = row[columns_eleve['CS_PY']].value
                        new_e.hand = row[columns_eleve['Hand']].value
                        new_e.annee_inscr = row[columns_eleve['A_inscr']].value
                        new_e.parent = row[columns_eleve['Parent']].value
                        new_e.tel_parent = row[columns_eleve['Tel_parent']].value
                        new_e.save()

                        # Create inscription
                        i = Inscription()
                        i.eleve = new_e
                        i.annee_scolaire = derniere_annee_scolaire
                        if Classe.objects.filter(legacy_id=row[columns_eleve['__FK_Classe_ID']].value).exists():
                            i.classe = Classe.objects.get(legacy_id=row[columns_eleve['__FK_Classe_ID']].value)
                        i.save()
                except Exception as ex:
                    print(f"Error importing student {new_e.nom}: {str(ex)}")

        # Process Paiement
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
                    new_p.date_paye = parse_date(row[columns_paiement['Date_paiement']].value)
                    new_p.note = row[columns_paiement['Note_Paiement']].value
                    try:
                        eleve = Eleve.objects.get(legacy_id=row[columns_paiement['__FK_Eleve']].value)
                        new_p.inscription = Inscription.objects.get(annee_scolaire=derniere_annee_scolaire, eleve=eleve)
                        new_p.save()
                    except Eleve.DoesNotExist:
                        print(f"Eleve with ID {row[columns_paiement['__FK_Eleve']].value} does not exist.")
                except Exception as ex:
                    print(f"Error importing payment: {str(ex)}")

        print('Import SICS END')

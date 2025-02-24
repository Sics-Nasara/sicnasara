from django.core.management.base import BaseCommand
from django.utils import timezone
from openpyxl import Workbook
from pathlib import Path
from scuelo.models import Eleve
import os

class Command(BaseCommand):
    help = 'Exports students with null annee_inscr to an Excel file'

    def handle(self, *args, **kwargs):
        # Fetch students with null annee_inscr
        students_with_null_annee_inscr = Eleve.objects.filter(annee_inscr__isnull=True)

        if not students_with_null_annee_inscr.exists():
            self.stdout.write(self.style.SUCCESS("No students found with null annee_inscr."))
            return

        # Create a new Excel workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Students with Null Annee Inscr"

        # Define headers for the Excel file
        headers = ['ID', 'Nom', 'Prenom', 'Condition Eleve', 'Sexe', 'Date Naissance', 'CS_PY', 'Hand', 'Parent', 'Tel Parent']
        ws.append(headers)

        # Iterate over the students and add their data to the worksheet
        for student in students_with_null_annee_inscr:
            row = [
                student.id,
                student.nom,
                student.prenom,
                student.condition_eleve,
                student.sex,
                student.date_naissance,
                student.cs_py,
                student.hand,
                student.parent,
                student.tel_parent,
            ]
            ws.append(row)

        # Define the output directory and file name
        output_dir = Path('exports')
        output_dir.mkdir(exist_ok=True)  # Create the exports directory if it doesn't exist
        output_file = output_dir / f"students_null_annee_inscr_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Save the Excel file
        wb.save(output_file)

        # Provide feedback to the user
        self.stdout.write(self.style.SUCCESS(f"Excel file created: {output_file}"))

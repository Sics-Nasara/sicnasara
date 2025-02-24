from django.core.management.base import BaseCommand
from scuelo.models import Eleve
import logging

class Command(BaseCommand):
    help = 'Check if specific students are in the database'

    def handle(self, *args, **kwargs):
        # Set up logging
        logging.basicConfig(filename='students_check.log', level=logging.INFO)
        self.stdout.write(self.style.SUCCESS('Checking students in the database...'))

        # List of students to check
        students = [
            "Kabore Mouhaguidou",
            "Kafando Carine",
            "Ouedraogo Mohamed",
            "Ilboudo Joel",
            "Kafando Salamata Kouka",
            "Kiendrebeogo Elodie",
            "Nacoulma Florentine",
            "Nana Fadilatou",
            "Ouedraogo Faical",
            "Ouedraogo Obed",
            "Sam Abdoul Aquim",
            "Wangrawa Nadia",
            "Zoungrana Issa",
            "Congo Yacouba Robert",
            "Kafando Salif",
            "Yameogo Alassane",
            "Alantinga Anselme",
            "Compaore W.Rene Astrid",
            "Dabone Angele",
            "Kabre Abdoul Nassirou",
            "Nikiema Tatiana",
            "Sandwidi Tatiana",
            "Sinare Mahamoudou",
            "Zangre Abdoul Rachid",
            "Zoungrana Ignace Wendpanga Olivier",
            "Zoungrana Zenabo",
            "Nikiema Mahamadi",
            "Ilboudo Benewendé Naomie",
            "Ilboudo Wendkouni Simplice",
            "Pafanam Natacha Erica",
            "Sawadogo Mimtury Nemata",
            "Kiemtore Théophile",
            "Ouedraogo Yasmina",
            "Compaore Adjaratou",
            "Koanda Pegwendé",
            "Ilboudou Mathias"
        ]

        # Loop through the student list and check if they exist in the database
        not_found = []
        for student_name in students:
            first_name, last_name = student_name.split()[0], student_name.split()[1]
            if Eleve.objects.filter(nom=first_name, prenom=last_name).exists():
                self.stdout.write(self.style.SUCCESS(f'{student_name} exists in the database.'))
                logging.info(f'{student_name} exists in the database.')
            else:
                self.stdout.write(self.style.ERROR(f'{student_name} does NOT exist in the database.'))
                logging.error(f'{student_name} does NOT exist in the database.')
                not_found.append(student_name)

        # Write students not found in the DB to a log file
        with open('students_not_found.log', 'w') as f:
            for student in not_found:
                f.write(student + "\n")

        self.stdout.write(self.style.SUCCESS('Student check completed. Check students_not_found.log for missing students.'))

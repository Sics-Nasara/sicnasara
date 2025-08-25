from django.core.management.base import BaseCommand
from django.utils import timezone
from collections import defaultdict
from openpyxl import Workbook
from scuelo.models import AnneeScolaire, Inscription, Classe, Ecole

class Command(BaseCommand):
    help = 'Promotion pour les écoles externes avec simulation et fichier Excel'

    PROMOTIONS_FIXES = {
        'M': {'PS': 'MS', 'MS': 'GS', 'GS': 'CP1'},
        'P': {'CP1': 'CP2', 'CP2': 'CE1', 'CE1': 'CE2', 'CE2': 'CM1', 'CM1': 'CM2', 'CM2': '6me'},
        'L': {'6me': '5me', '5me': '4me', '4me': '3me', '3me': '2me', '2me': '1ere', '1ere': 'Term', 'Term': None},
    }

    FIN_CYCLE_NOMS = {'M': 'GS', 'P': 'CM2', 'L': 'Term'}

    def get_classe_suivante(self, classe_actuelle):
        type_ecole = classe_actuelle.type.type_ecole
        classe_nom = classe_actuelle.type.nom

        # Handle end of cycle (no next classe)
        fin_cycle = self.FIN_CYCLE_NOMS.get(type_ecole)
        if classe_nom == fin_cycle:
            return None

        nom_suivant = self.PROMOTIONS_FIXES.get(type_ecole, {}).get(classe_nom)
        if not nom_suivant:
            return None

        # Find the next classe in the same external school
        classe_suivante = Classe.objects.filter(
            ecole=classe_actuelle.ecole,
            type__nom=nom_suivant
        ).first()
        return classe_suivante

    def handle(self, *args, **options):
        dry_run = False  # change to False to execute promotion

        annee_actuelle = AnneeScolaire.objects.filter(actuel=True).first()
        if not annee_actuelle:
            self.stderr.write("Aucune année scolaire active")
            return

        annee_suivante = AnneeScolaire.objects.filter(date_initiale__gt=annee_actuelle.date_finale).first()
        if not annee_suivante:
            self.stderr.write("Aucune année scolaire suivante définie")
            return

        inscriptions = Inscription.objects.filter(
            annee_scolaire=annee_actuelle,
            classe__ecole__externe=True  # Filter for external schools only
        ).select_related('classe', 'eleve').exclude(eleve__condition_eleve='ABAN')

        groupes = defaultdict(list)
        for insc in inscriptions:
            groupes[insc.classe].append(insc.eleve)

        wb = Workbook()
        ws = wb.active
        ws.title = "Promotion Externes"

        ws.append([
            "École",
            "Classe actuelle",
            "Nombre élèves dans classe",
            "Nom élève",
            "Prénom élève",
            "Date de naissance",
            "Sexe",
            "Classe suivante",
            "École suivante"
        ])

        for classe_actuelle, eleves in groupes.items():
            classe_suivante = self.get_classe_suivante(classe_actuelle)
            for eleve in eleves:
                ws.append([
                    classe_actuelle.ecole.nom,
                    classe_actuelle.nom,
                    len(eleves),
                    eleve.nom,
                    eleve.prenom,
                    eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else '',
                    eleve.sex,
                    classe_suivante.nom if classe_suivante else "Fin de cycle",
                    classe_suivante.ecole.nom if classe_suivante else "Fin de cycle"
                ])

        if not dry_run:
            for inscription in inscriptions:
                nouvelle_classe = self.get_classe_suivante(inscription.classe)
                if nouvelle_classe:
                    Inscription.objects.create(
                        eleve=inscription.eleve,
                        classe=nouvelle_classe,
                        annee_scolaire=annee_suivante,
                        date_inscription=timezone.now()
                    )
                    self.stdout.write(f"Élève {inscription.eleve} promu de {inscription.classe.nom} à {nouvelle_classe.nom}")
                else:
                    self.stdout.write(f"Élève {inscription.eleve} en fin de cycle")

        filename = f"promotion_externe_{annee_actuelle.nom.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)
        self.stdout.write(f"Fichier Excel créé : {filename}")

        if dry_run:
            self.stdout.write("Simulation terminée.")
        else:
            self.stdout.write("Promotion effective terminée.")

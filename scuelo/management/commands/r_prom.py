from django.core.management.base import BaseCommand
from django.utils import timezone
from collections import defaultdict
from openpyxl import Workbook
from scuelo.models import AnneeScolaire, Inscription, Classe, Ecole

class Command(BaseCommand):
    help = 'Promotion automatique avec option simulation ou exécution réelle'

    ECOLES_MANUELLES_NAMES = {
        'M': "École Maternelle Centre social de Nasara",
        'P': "École primaire Centre social de Nasara",
        'L': "École Secondaire Centre social de Nasara",
    }

    PROMOTIONS_FIXES = {
        'M': {'PS': 'MS', 'MS': 'GS', 'GS': 'CP1'},
        'P': {'CP1': 'CP2', 'CP2': 'CE1', 'CE1': 'CE2', 'CE2': 'CM1', 'CM1': 'CM2', 'CM2': '6me'},
        'L': {'6me': '5me', '5me': '4me', '4me': '3me', '3me': '2me', '2me': '1ere', '1ere': 'Term', 'Term': None},
    }

    FIN_CYCLE_NOMS = {'M': 'GS', 'P': 'CM2', 'L': 'Term'}

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Exécuter la promotion réelle au lieu d\'une simulation'
        )

    def get_ecole_manuelle(self, type_ecole):
        nom = self.ECOLES_MANUELLES_NAMES.get(type_ecole)
        if not nom:
            self.stderr.write(f"École manuelle inconnue pour type {type_ecole}")
            return None
        return Ecole.objects.filter(nom=nom).first()

    def get_classe_suivante_manuel(self, classe_actuelle):
        type_ecole = classe_actuelle.type.type_ecole
        classe_nom = classe_actuelle.type.nom
        fin_cycle = self.FIN_CYCLE_NOMS.get(type_ecole)

        if classe_nom == fin_cycle:
            ecoles_meme_ville = Ecole.objects.filter(
                ville=classe_actuelle.ecole.ville,
                externe=False
            ).exclude(id=classe_actuelle.ecole.id)

            cycle_suivant = None
            if type_ecole == 'M':
                cycle_suivant = 'CP1'
            elif type_ecole == 'P':
                cycle_suivant = '6me'
            elif type_ecole == 'L':
                return None

            if not cycle_suivant:
                return None

            for ecole in ecoles_meme_ville:
                classe_suivante = Classe.objects.filter(
                    ecole=ecole,
                    type__nom=cycle_suivant
                ).first()
                if classe_suivante:
                    self.stdout.write(f"[INFO] Promotion fin cycle : {classe_actuelle.nom} vers {classe_suivante.nom} dans {ecole.nom}")
                    return classe_suivante
            self.stdout.write(f"[WARN] Pas de classe suivante trouvée en fin de cycle pour {classe_actuelle.nom}")
            return None

        nom_suivant = self.PROMOTIONS_FIXES.get(type_ecole, {}).get(classe_nom)
        if not nom_suivant:
            self.stdout.write(f"[WARN] Pas de promotion fixe trouvée pour {classe_nom} de type {type_ecole}")
            return None

        ecole_suivante = self.get_ecole_manuelle(type_ecole)
        if not ecole_suivante:
            self.stderr.write(f"Erreur : école manuelle introuvable pour type {type_ecole}")
            return None

        classe_suivante = Classe.objects.filter(
            ecole=ecole_suivante,
            type__nom=nom_suivant
        ).first()

        if classe_suivante:
            self.stdout.write(f"[INFO] Promotion prévue : {classe_actuelle.nom} vers {classe_suivante.nom} dans {ecole_suivante.nom}")
        else:
            self.stdout.write(f"[WARN] Classe suivante '{nom_suivant}' introuvable dans {ecole_suivante.nom}")

        return classe_suivante

    def handle(self, *args, **options):
        execute = options['execute']
        dry_run = not execute

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
            classe__ecole__externe=False
        ).select_related('classe', 'eleve').exclude(eleve__condition_eleve='ABAN')

        groupes = defaultdict(list)
        for insc in inscriptions:
            groupes[insc.classe].append(insc.eleve)

        wb = Workbook()
        ws = wb.active
        ws.title = "Promotion"

        ws.append([
            "École actuelle",
            "Classe actuelle",
            "Nombre élèves dans classe",
            "Nom de l'élève",
            "Prénom de l'élève",
            "Date enquête",
            "Date de naissance",
            "Sexe",
            "CS/PY",
            "Handicap",
            "Année inscription",
            "Parent/Tuteur",
            "Téléphone Parent/Tuteur",
            "Note élève",
            "Legacy ID",
            "École suivante",
            "Classe suivante"
        ])

        for classe_actuelle, eleves in groupes.items():
            classe_suivante = self.get_classe_suivante_manuel(classe_actuelle)
            ecole_actuelle = self.get_ecole_manuelle(classe_actuelle.type.type_ecole)
            ecole_actuelle_nom = ecole_actuelle.nom if ecole_actuelle else classe_actuelle.ecole.nom
            ecole_suivante_nom = classe_suivante.ecole.nom if classe_suivante else "Fin de cycle"

            for eleve in eleves:
                ws.append([
                    ecole_actuelle_nom,
                    classe_actuelle.nom,
                    len(eleves),
                    eleve.nom,
                    eleve.prenom,
                    eleve.date_enquete.strftime('%d/%m/%y') if eleve.date_enquete else '',
                    eleve.date_naissance.strftime('%d/%m/%y') if eleve.date_naissance else '',
                    eleve.sex,
                    eleve.cs_py,
                    eleve.hand,
                    eleve.annee_inscr,
                    eleve.parent,
                    eleve.tel_parent,
                    eleve.note_eleve,
                    eleve.legacy_id,
                    ecole_suivante_nom,
                    classe_suivante.nom if classe_suivante else "Fin de cycle"
                ])

        if not dry_run:
            for inscription in inscriptions:
                new_classe = self.get_classe_suivante_manuel(inscription.classe)
                if new_classe:
                    Inscription.objects.create(
                        eleve=inscription.eleve,
                        classe=new_classe,
                        annee_scolaire=annee_suivante,
                        date_inscription=timezone.now()
                    )
                    self.stdout.write(f"Élève {inscription.eleve} promu de {inscription.classe.nom} à {new_classe.nom}.")
                else:
                    self.stdout.write(f"Élève {inscription.eleve} est en fin de cycle.")

        filename = f"promotion_{annee_actuelle.nom.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)
        self.stdout.write(f"Fichier Excel créé : {filename}")

        if dry_run:
            self.stdout.write("Simulation terminée sans modification.")
        else:
            self.stdout.write("Promotion effective terminée.")

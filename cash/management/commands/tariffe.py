from django.core.management.base import BaseCommand
from scuelo.models import Classe, AnneeScolaire, Ecole
from cash.models import Tarif
from django.utils import timezone
from datetime import datetime, timedelta


ECOLES_MANUELLES_NAMES = {
    'M': "École Maternelle Centre social de Nasara",
    'P': "École primaire Centre social de Nasara",
    'L': "École Secondaire Centre social de Nasara",
}


class Command(BaseCommand):
    help = "Supprime et recrée tous les tarifs de l'année scolaire actuelle avec dates corrigées"

    def handle(self, *args, **options):
        try:
            annee_scolaire = AnneeScolaire.objects.get(actuel=True)
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Aucune année scolaire actuelle trouvée."))
            return

        # Supprimer tous les tarifs de l'année scolaire actuelle
        count, _ = Tarif.objects.filter(annee_scolaire=annee_scolaire).delete()
        self.stdout.write(f"Suppression de {count} tarifs de l'année {annee_scolaire.nom}")

        ec_list = Ecole.objects.filter(nom__in=ECOLES_MANUELLES_NAMES.values())
        if not ec_list.exists():
            self.stdout.write(self.style.ERROR("Aucune école trouvée avec les noms spécifiés."))
            return

        # Dates corrigées pour échéances, INS et CAN ont la même date que SCO1
        expiration_dates = {
            'INS': datetime(annee_scolaire.date_initiale.year, 9, 20),
            'SCO1': datetime(annee_scolaire.date_initiale.year, 9, 20),
            'SCO2': datetime(annee_scolaire.date_initiale.year, 11, 30),
            'SCO3': datetime(annee_scolaire.date_initiale.year + 1, 1, 31),
            'CAN': datetime(annee_scolaire.date_initiale.year, 9, 20),
            'TEN': datetime(annee_scolaire.date_initiale.year, 12, 31),
        }

        for ecole in ec_list:
            classes = Classe.objects.filter(ecole=ecole)
            if not classes.exists():
                self.stdout.write(self.style.WARNING(f"Aucune classe dans l'école {ecole.nom}"))
                continue

            for classe in classes:
                tarifs = self.tarifs_par_classe(classe.nom)
                if not tarifs:
                    self.stdout.write(self.style.WARNING(f"Pas de tarifs définis pour la classe {classe.nom}"))
                    continue

                self.create_class_tariffs(classe, tarifs, annee_scolaire, expiration_dates)
                self.stdout.write(self.style.SUCCESS(f"Tarifs recréés pour la classe {classe.nom} de l'école {ecole.nom}"))

    def tarifs_par_classe(self, class_name):
        tarifs_init = {
            '6me': {'SCO1': 32000, 'SCO2': 15000, 'SCO3': 15000},
            'CP1': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CP2': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE1': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CE2': {'SCO1': 15000, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM1': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'CM2': {'SCO1': 17500, 'SCO2': 7500, 'SCO3': 7500, 'TEN': 4500},
            'PS': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
            'MS': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
            'GS': {'SCO1': 10000, 'SCO2': 8000, 'SCO3': 7000, 'TEN': 4500, 'CAN': 8000},
        }
        return tarifs_init.get(class_name)

    def create_class_tariffs(self, classe, tariffs, annee_scolaire, expiration_dates):
        ins_montant = tariffs.get('INS', tariffs.get('SCO1', 0))
        can_montant = tariffs.get('CAN', ins_montant)

        # Créer tarif inscription (INS)
        Tarif.objects.create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal='INS',
            montant=ins_montant,
            date_expiration=expiration_dates.get('INS', timezone.now() + timedelta(days=90)).date()
        )
        # Créer tarif CAN
        Tarif.objects.create(
            classe=classe,
            annee_scolaire=annee_scolaire,
            causal='CAN',
            montant=can_montant,
            date_expiration=expiration_dates.get('CAN', timezone.now() + timedelta(days=90)).date()
        )
        for causal, montant in tariffs.items():
            if causal not in ['INS', 'CAN']:
                Tarif.objects.create(
                    classe=classe,
                    annee_scolaire=annee_scolaire,
                    causal=causal,
                    montant=montant,
                    date_expiration=expiration_dates.get(causal, timezone.now() + timedelta(days=90)).date()
                )

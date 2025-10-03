from django.core.management.base import BaseCommand
from scuelo.models import Ecole, Classe

class_order = ['PS', 'MS', 'GS', 'CP1', 'CP2', 'CE1', 'CE2', 'CM1', 'CM2', '6me']
order_map = {name: i for i, name in enumerate(class_order)}

class Command(BaseCommand):
    help = 'Liste les écoles et leurs classes triées selon class_order'

    def handle(self, *args, **options):
        ecoles = Ecole.objects.filter(externe=False)
        for ecole in ecoles:
            self.stdout.write(f"École : {ecole.nom}")
            classes = list(Classe.objects.filter(ecole=ecole))
            classes.sort(key=lambda c: order_map.get(c.nom, len(class_order)))
            for classe in classes:
                self.stdout.write(f"  Classe : {classe.nom}")
            self.stdout.write("")  # Ligne vide entre écoles

import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from scuelo.models import Eleve, Inscription, AnneeScolaire
from cash.models import Mouvement
class Command(BaseCommand):
    help = "Met à jour le statut des élèves (option simulation) et exporte les changements."

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulate',
            action='store_true',
            help="Simule l'exécution sans enregistrer les changements en base"
        )

    def handle(self, *args, **options):
        simulate = options['simulate']

        try:
            annee_courante = AnneeScolaire.objects.get(actuel=True)
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Aucune année scolaire courante définie."))
            return

        inscriptions_courantes = Inscription.objects.filter(annee_scolaire=annee_courante)
        premier_paiement = Mouvement.objects.filter(inscription=OuterRef('pk'))

        eleves_a_prop = Eleve.objects.filter(
            inscriptions__in=inscriptions_courantes
        ).exclude(condition_eleve__in=['PROP', 'CONF']).exclude(cs_py='C').distinct()

        modifications = []

        # Préparer modifications PROP
        for eleve in eleves_a_prop:
            ancien_statut = eleve.condition_eleve
            if not simulate:
                eleve.condition_eleve = 'PROP'
                eleve.save()
            modifications.append({
                'eleve_id': eleve.id,
                'nom': eleve.nom,
                'prenom': eleve.prenom,
                'ancien_statut': ancien_statut,
                'nouveau_statut': 'PROP'
            })

        inscriptions_avec_paiement = inscriptions_courantes.annotate(
            a_paye=Exists(premier_paiement)
        ).filter(a_paye=True)

        eleves_a_conf = Eleve.objects.filter(
            inscriptions__in=inscriptions_avec_paiement,
            condition_eleve='PROP'
        ).exclude(cs_py='C').distinct()

        # Préparer modifications CONF
        for eleve in eleves_a_conf:
            ancien_statut = eleve.condition_eleve
            if not simulate:
                eleve.condition_eleve = 'CONF'
                eleve.save()
            modifications.append({
                'eleve_id': eleve.id,
                'nom': eleve.nom,
                'prenom': eleve.prenom,
                'ancien_statut': ancien_statut,
                'nouveau_statut': 'CONF'
            })

        if not modifications:
            self.stdout.write("Aucune modification de statut appliquée.")
            return

        df = pd.DataFrame(modifications)
        fichier = f"statuts_eleves_{annee_courante.nom}_{'simulation' if simulate else 'reel'}.xlsx"
        df.to_excel(fichier, index=False)

        self.stdout.write(self.style.SUCCESS(
            f"{len(modifications)} modifications {'simulées' if simulate else 'appliquées'} et exportées dans {fichier}"
        ))

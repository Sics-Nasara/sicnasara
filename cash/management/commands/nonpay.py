import csv
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from scuelo.models import Eleve, Inscription, AnneeScolaire 
from cash.models import Mouvement   
class Command(BaseCommand):
    help = "Liste les élèves non CS, non abandonnés, sans paiement, change statut en PROP et exporte en CSV."

    def handle(self, *args, **kwargs):
        try:
            annee_courante = AnneeScolaire.objects.get(actuel=True)
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Aucune année scolaire courante définie."))
            return

        inscriptions_courantes = Inscription.objects.filter(annee_scolaire=annee_courante)
        paiement_existant = Mouvement.objects.filter(inscription=OuterRef('pk'))

        # Éléves hors cs_py='C' et hors 'ABAN'
        eleves = Eleve.objects.filter(
            inscriptions__in=inscriptions_courantes,
        ).exclude(condition_eleve='ABAN').exclude(cs_py='C').distinct()

        inscriptions_sans_paiement = inscriptions_courantes.annotate(
            a_paye=Exists(paiement_existant)
        ).filter(a_paye=False)

        eleves_sans_paiement = eleves.filter(inscriptions__in=inscriptions_sans_paiement).distinct()

        if not eleves_sans_paiement.exists():
            self.stdout.write("Tous les élèves ont effectué au moins un paiement.")
            return

        # Changer le statut des élèves sélectionnés en PROP
        for eleve in eleves_sans_paiement:
            eleve.condition_eleve = "PROP"
            eleve.save()

        filename = f"eleves_sans_paiement_{annee_courante.nom}.csv"

        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Nom', 'Prénom', 'Condition', 'CS/PY', 'Date Naissance', 'Classe', 'Ecole'])

            for eleve in eleves_sans_paiement:
                inscription = eleve.inscriptions.filter(annee_scolaire=annee_courante).first()
                classe_nom = inscription.classe.nom if inscription and inscription.classe else ''
                ecole_nom = inscription.classe.ecole.nom if inscription and inscription.classe and inscription.classe.ecole else ''

                writer.writerow([
                    eleve.id,
                    eleve.nom,
                    eleve.prenom,
                    eleve.condition_eleve,
                    eleve.cs_py,
                    eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else '',
                    classe_nom,
                    ecole_nom
                ])

        self.stdout.write(self.style.SUCCESS(f"{eleves_sans_paiement.count()} élèves mis à PROP et exportés dans {filename}"))

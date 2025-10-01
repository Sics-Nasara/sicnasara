import csv
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from scuelo.models import Eleve, Inscription, AnneeScolaire
from cash.models import Mouvement
class Command(BaseCommand):
    help = "Exporte en CSV les élèves non CS, non abandonnés, n'ayant pas encore payé l'année scolaire actuelle"

    def handle(self, *args, **kwargs):
        try:
            annee_courante = AnneeScolaire.objects.get(actuel=True)
        except AnneeScolaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Aucune année scolaire courante définie."))
            return

        inscriptions_courantes = Inscription.objects.filter(annee_scolaire=annee_courante)

        # Sous-requête pour vérifier si un paiement existe pour l'inscription
        paiement_existant = Mouvement.objects.filter(inscription=OuterRef('pk'))

        # Élèves inscrits à l'année courante (hors CS et hors ABAN)
        eleves = Eleve.objects.filter(
            inscriptions__in=inscriptions_courantes,
            inscriptions__classe__ecole__externe=False  # Filtre écoles internes
        ).exclude(condition_eleve='ABAN').exclude(cs_py='C').distinct()


        # Garder uniquement ceux qui n'ont pas de paiement enregistré 
        inscriptions_sans_paiement = inscriptions_courantes.annotate(
            a_paye=Exists(paiement_existant)
        ).filter(a_paye=False)

        eleves_sans_paiement = eleves.filter(inscriptions__in=inscriptions_sans_paiement).distinct()

        if not eleves_sans_paiement.exists():
            self.stdout.write("Tous les élèves ont effectué au moins un paiement.")
            return

        filename = f"eleves_sans_paiement_{annee_courante.nom}.csv"

    # ... partie initiale inchangée

        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # En-tête avec classe et école
            writer.writerow(['ID', 'Nom', 'Prénom', 'Condition', 'CS/PY', 'Date Naissance', 'Classe', 'Ecole'])

            for eleve in eleves_sans_paiement:
                # Récupérer la première inscription courante pour l'élève
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


        self.stdout.write(self.style.SUCCESS(f"{eleves_sans_paiement.count()} élèves sans paiement exportés dans {filename}"))

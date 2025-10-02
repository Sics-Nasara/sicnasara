import csv
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from scuelo.models import Eleve, Inscription , AnneeScolaire
from cash.models import Mouvement
class Command(BaseCommand):
    help = "Met à PROP les élèves sans paiement pour l'année en cours, les liste dans un CSV."

    def handle(self, *args, **kwargs):
        # Récupérer l'année scolaire actuelle
        annee_courante = AnneeScolaire.objects.filter(actuel=True).first()
        if not annee_courante:
            self.stdout.write(self.style.ERROR("Aucune année scolaire courante définie."))
            return

        # Requête pour inscriptions à l'année courante
        inscriptions_courantes = Inscription.objects.filter(annee_scolaire=annee_courante)

        # Sous-requête : Mouvement de paiement pour une inscription donnée
        paiement_existant = Mouvement.objects.filter(inscription=OuterRef('pk'))

        # Identifier les inscriptions sans paiements
        inscriptions_sans_paiement = inscriptions_courantes.annotate(
            a_paye=Exists(paiement_existant)
        ).filter(a_paye=False)

        # Élèves liés à ces inscriptions sans paiement, hors cs_py='C' et hors 'ABAN'
        eleves_sans_paiement = Eleve.objects.filter(
            inscriptions__in=inscriptions_sans_paiement
        ).exclude(cs_py='C').exclude(condition_eleve='ABAN').distinct()

        # Aucun à traiter : message et retour
        if not eleves_sans_paiement.exists():
            self.stdout.write("Tous les élèves ont déjà effectué un paiement.")
            return

        # Mettre à jour statut en PROP
        for eleve in eleves_sans_paiement:
            eleve.condition_eleve = 'PROP'
            eleve.save()

        # Création du fichier CSV
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

        self.stdout.write(self.style.SUCCESS(
            f"{eleves_sans_paiement.count()} élèves mis à PROP et exportés dans {filename}"
        ))

from django.db import models
from django.utils  import timezone
from django.db.models import Q  , Max ,  Sum , Count

CONDITION_ELEVE = (
    ("CONF", "CONF"),
    ("ABAN", "ABAN"),
    ("PROP", "PROP"),
)

HAND = (
    ("DA", "DA"),
    ("DM", "DM"),
    ("DL", "DL"),
    ("DV", "DV"),

)
CS_PY = (
    ("C", "CS"),
    ("E", "EXTRA"),
    ("P", "PY"),
    ("A", "ACC"),
    ("B", "BRAVO"),
)

SEX = (
    ("F", "F"),
    ("M", "M"),
)

TYPE_ECOLE = (
    ("M", "MATERNELLE"),
    ("P", "PRIMAIRE"),
)


class Classe(models.Model):
    type_ecole = models.CharField(max_length=1, choices=TYPE_ECOLE, db_index=True)
    nom = models.CharField(max_length=10, null=False)
    ordre = models.IntegerField(blank=True, null=True)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    
    def __str__(self):
        return '%s %s' % (self.nom, self.get_type_ecole_display())

class Eleve(models.Model):
    nom = models.CharField(max_length=34, null=False)
    prenom = models.CharField(max_length=34, null=False)
    date_enquete = models.DateField(null=True, blank=True)  # is  added right after
    condition_eleve = models.CharField(
        max_length=4,
        choices=CONDITION_ELEVE
    )
    sex = models.CharField(max_length=1, choices=SEX)
    
    date_naissance = models.DateField(blank=True, null=True)
    cs_py = models.CharField(max_length=7, choices=CS_PY, default="C" )
    hand = models.CharField(max_length=2, choices=HAND, null=True, blank=True)
    annee_inscr = models.SmallIntegerField(blank=True, null=True)
    parent = models.CharField(max_length=100, blank=True, null=True)
    tel_parent = models.CharField(max_length=100, blank=True, null=True)
    note_eleve = models.TextField(blank=True, null=True, default='-')
    #tenues = models.CharField(choices=3   ,  max_length=2 blank=True , null = True)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    #current_classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, blank=True, null=True, related_name='current_students')
    
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.legacy_id})"
    
    @property
    def an_insc(self):
        return self.annee_inscr.year

    @property
    def current_class(self):
        # Assuming there's a ForeignKey from Inscription to Classe called 'classe'
        current_year = AnneeScolaire.objects.get(actuel=True)
        try:
            # Get the latest inscription for the current year
            inscription = Inscription.objects.filter(eleve=self, annee_scolaire=current_year).latest('date_inscription')
            return inscription.classe
        except Inscription.DoesNotExist:
            return None
    
 
    def get_queryset(self, request):
        # Group students by nom_classe
        queryset = Eleve.objects.all().prefetch_related('nom_classe')  # Prefetch for efficiency
        grouped_queryset = {}
        for eleve in queryset:
            classe = eleve.nom_classe.pk  # Get the primary key of nom_classe
            if classe not in grouped_queryset:
                grouped_queryset[classe] = []
            grouped_queryset[classe].append(eleve)
        return grouped_queryset
    
    def tenu_count(self):
        # Count the number of uniform payments for this student based on the defined conditions
        return self.paiement_set.filter(
            Q(causal='TEN') &
            (
                Q(montant=4000) | Q(montant=4500) | Q(montant=2250) | Q(montant=2000)
            )
        ).count()
    
    class Meta:
        verbose_name = 'Eleve'
        verbose_name_plural = 'Eleves'


class AnneeScolaire(models.Model):
    nom = models.CharField(max_length=100)
    nom_bref = models.CharField(max_length=10 , default='')
    date_initiale = models.DateField(blank=True)
    date_finale = models.DateField(blank=True)
    actuel = models.BooleanField(default=False)
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.actuel:
            AnneeScolaire.objects.filter(actuel=True).exclude(pk=self.pk).update(actuel=False)


class Inscription(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, blank=True, null=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    date_inscription = models.DateTimeField(default=timezone.now  )  # Add this field
    
    def __str__(self):
        return '%s - %s - %s' % (self.annee_scolaire.nom_bref, self.classe, self.eleve)

    def save(self, *args, **kwargs):
        # Ensure only one inscription for the current year
        if self.annee_scolaire.actuel:
            Inscription.objects.filter(eleve=self.eleve, annee_scolaire__actuel=True).exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)
        
class Paiement(models.Model):
    CAUSAL = (
        ("INS", "Inscription"),
        ("SCO", "Scolarite"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
    causal = models.CharField(max_length=5, choices=CAUSAL, db_index=True)
    montant = models.PositiveBigIntegerField()
    date_paye = models.DateField(db_index=True ,default="")
    note = models.CharField(max_length=200, null=True, blank=True)
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, blank=True, null=True)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    
    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ["-date_paye"]
    
    def __str__(self):
        return f"{self.causal} {self.montant}"
    

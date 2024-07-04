from django.db import models

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
    cs_py = models.CharField(max_length=7, choices=CS_PY)
    hand = models.CharField(max_length=2, choices=HAND, null=True, blank=True)
    annee_inscr = models.SmallIntegerField(blank=True, null=True)
    parent = models.CharField(max_length=50, blank=True, null=True)
    tel_parent = models.CharField(max_length=24, blank=True, null=True)
    note_eleve = models.TextField(blank=True, null=True, default='-')
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.legacy_id})"
    
    @property
    def an_insc(self):
        return self.annee_inscr.year
    
    '''
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        messages.success(request, f'vous avez enregister l\'eleve {self.nom} {self.prenom} de la classe  de  {self.nom_classe}') 
    '''
    
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
    
    class Meta:
        verbose_name = 'Eleve'
        # order_by = 'nom_classe'
        
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

    def __str__(self):
        return '%s - %s - %s' % (self.annee_scolaire.nom_bref, self.classe, self.eleve)


class Paiement(models.Model):
    CAUSAL = (
        ("INS", "Inscription"),
        ("SCO", "Scolarite"),
        ("TEN", "Tenue"),
        ("CAN", "Cantine"),
    )
    causal = models.CharField(max_length=5, choices=CAUSAL, db_index=True)
    montant = models.PositiveBigIntegerField()
    date_paye = models.DateField(db_index=True)
    note = models.CharField(max_length=200, null=True, blank=True)
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, blank=True, null=True)
    legacy_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    
    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ["-date_paye"]
    
    def __str__(self):
        return f"{self.causal} {self.montant}"
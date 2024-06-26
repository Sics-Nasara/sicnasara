from django.contrib import admin
from .models import Classe, Eleve, AnneeScolaire, Inscription, Paiement
from django.contrib.auth.models import User, Group


class SicAdminArea(admin.AdminSite):
    site_header = 'SICS NASSARA'
    site_title = 'SICS NASSARA'
    index_title = 'SICS NASSARA'


sics_site = SicAdminArea(name='SICS NASSARA')


class PaimentInline(admin.TabularInline):
    model = Paiement
    extra = 0
    classes = ['collapse']


class InscriptionInline(admin.TabularInline):
    model = Inscription
    #list_display = [''
    autocomplete_fields = ['eleve']
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # obj è il MediciZone
        formset = super(InscriptionInline, self).get_formset(request, obj, **kwargs)
        # formset.form.base_fields['a'].queryset
        self.eleve = obj
        return formset

    def get_queryset(self, request):
        qs = super(InscriptionInline, self).get_queryset(request)
        return qs
        # return qs.filter(annee_scolaire__actuel=True)


class EleveAdmin(admin.ModelAdmin):
    fieldsets = (
        ('INFORMATIONS DE  BASE', {
            'fields': ('nom', 'prenom', 'sex',
                       'date_naissance'
                       ),
        }
         ),
        ('INFORMATION SOCIALE', {
            'fields': ('condition_eleve', 'cs_py', 'hand'
                       , 'date_enquete'),
        }
         ),
        ('INFORMATION PARENT', {
            'fields': ('parent', 'tel_parent',
                       ),
        }
         )
    )
    list_display = ['id', 'nom', 'prenom', 'condition_eleve', 'sex', 'date_naissance', 'tot_pag' , 'tenues' , 'cs_py' , 'hand'] #
    search_fields = ['nom', 'prenom' , 'cs_py']
    inlines = [InscriptionInline]

    def tot_pag(self, instance):
        return 'tot pag'
  
    tot_pag.short_description = "Tot pag"

    def tenues(self, instance):
        return 'What is it?'

    tenues.short_description = "Tenues"


class PaiementAdmin(admin.ModelAdmin):
    list_display = [
        'get_causal_display', 'montant',
        'date_paye', 'inscription'
    ]
    search_fields = ['inscription__eleve__nom', 'inscription__eleve__prenom']
    list_select_related = ['inscription']
    list_filter = ['inscription__annee_scolaire', 'causal']

    def get_causal_display(self, obj):
        return obj.get_causal_display()

    get_causal_display.short_description = 'Causal'


class InscriptionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['eleve']

sics_site.register(Paiement, PaiementAdmin)
sics_site.register(Eleve, EleveAdmin)
sics_site.register(Classe)
sics_site.register(AnneeScolaire)
sics_site.register(Inscription, InscriptionAdmin)
sics_site.register(User)
sics_site.register(Group)
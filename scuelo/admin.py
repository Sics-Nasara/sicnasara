from django.contrib import admin
from .models import ( Classe, Eleve, AnneeScolaire, 
                     Inscription , StudentLog , 
                     UniformReservation , Ecole )
from django.contrib.auth.models import User, Group


class SicAdminArea(admin.AdminSite):
    site_header = 'SICS NASSARA'
    site_title = 'SICS NASSARA'
    index_title = 'SICS NASSARA'


sics_site = SicAdminArea(name='SICS NASSARA')


from django.contrib import admin
from .models import (
    TypeClasse, Ecole, Classe, Eleve, AnneeScolaire,
    Inscription, UniformReservation, Rang, StudentLog
)



@admin.register(TypeClasse, site=sics_site)
class TypeClasseAdmin(admin.ModelAdmin):
    list_display = ("nom", "ordre", "type_ecole")
    list_filter = ("type_ecole",)
    search_fields = ("nom",)


@admin.register(Ecole, site=sics_site)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "nom_du_referent", "telephone_du_referent", "externe")
    search_fields = ("nom", "ville", "nom_du_referent", "prenom_du_referent")
    list_filter = ("ville", "externe")


class InscriptionInline(admin.TabularInline):
    model = Inscription
    extra = 1
    autocomplete_fields = ("classe", "annee_scolaire")


@admin.register(Classe, site=sics_site)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "ecole", "legacy_id", "confirmed_py_count")
    list_filter = ("type__type_ecole", "ecole")
    search_fields = ("nom", "legacy_id")
    inlines = [InscriptionInline]


@admin.register(Eleve, site=sics_site)
class EleveAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "condition_eleve", "cs_py", "sex", "annee_inscr", "legacy_id")
    list_filter = ("condition_eleve", "sex", "cs_py")
    search_fields = ("nom", "prenom", "legacy_id")
    inlines = [InscriptionInline]
    readonly_fields = ("formatted_date_enquete", "formatted_date_naissance")


@admin.register(AnneeScolaire, site=sics_site)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ("nom", "nom_bref", "date_initiale", "date_finale", "actuel")
    list_filter = ("actuel",)
    search_fields = ("nom", "nom_bref")
    ordering = ("-date_initiale",)


@admin.register(Inscription, site=sics_site)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("eleve", "classe", "annee_scolaire", "nombre_uniformes", "formatted_date_inscription")
    list_filter = ("annee_scolaire", "classe__type__type_ecole")
    search_fields = ("eleve__nom", "eleve__prenom", "classe__nom")


@admin.register(UniformReservation, site=sics_site)
class UniformReservationAdmin(admin.ModelAdmin):
    list_display = ("student", "student_type", "quantity", "cost_per_uniform", "status", "school_year", "date_reserved")
    list_filter = ("status", "school_year")
    search_fields = ("student__nom", "student__prenom")


@admin.register(Rang, site=sics_site)
class RangAdmin(admin.ModelAdmin):
    list_display = ("eleve", "classe", "annee_scolaire", "rang1", "rang2", "rang3", "rang_annuelle")
    list_filter = ("annee_scolaire", "classe")
    search_fields = ("eleve__nom", "eleve__prenom")


@admin.register(StudentLog, site=sics_site)
class StudentLogAdmin(admin.ModelAdmin):
    list_display = ("student", "user", "action", "formatted_timestamp")
    list_filter = ("timestamp", "user")
    search_fields = ("student__nom", "student__prenom", "action")
    readonly_fields = ("formatted_timestamp",)

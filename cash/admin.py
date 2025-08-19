from django.contrib import admin
from .models import Cashier, Tarif, Mouvement, Expense, Transfer
from scuelo.admin import sics_site  # import the custom admin site


@admin.register(Cashier, site=sics_site)
class CashierAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_default", "note")
    list_filter = ("type", "is_default")
    search_fields = ("name", "note")


@admin.register(Tarif, site=sics_site)
class TarifAdmin(admin.ModelAdmin):
    list_display = ("causal", "montant", "classe", "annee_scolaire", "date_expiration")
    list_filter = ("causal", "annee_scolaire", "classe__type__type_ecole")
    search_fields = ("classe__nom",)
    ordering = ("-annee_scolaire",)


@admin.register(Mouvement, site=sics_site)
class MouvementAdmin(admin.ModelAdmin):
    list_display = ("causal", "montant", "date_paye", "inscription", "tarif", "cashier", "annee_scolaire")
    list_filter = ("causal", "annee_scolaire", "cashier")
    search_fields = ("inscription__eleve__nom", "inscription__eleve__prenom")
    date_hierarchy = "date_paye"
    autocomplete_fields = ("inscription", "tarif", "cashier")


@admin.register(Expense, site=sics_site)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "date", "cashier", "annee_scolaire")
    list_filter = ("annee_scolaire", "cashier")
    search_fields = ("description", "note")
    date_hierarchy = "date"


@admin.register(Transfer, site=sics_site)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("amount", "date", "from_cashier", "to_cashier", "note")
    list_filter = ("date", "from_cashier", "to_cashier")
    search_fields = ("note",)
    date_hierarchy = "date"

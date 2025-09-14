# =============================
# Authentication & Permissions
# =============================
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth.decorators import login_required
# =============================
# Django Shortcuts & Utilities
# =============================
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.db import models, connection, IntegrityError

# =============================
# Generic & Class-Based Views
# =============================
from django.views.generic import DetailView, ListView, CreateView, TemplateView
from django.views.generic.edit import UpdateView, DeleteView

# =============================
# ORM & Query Helpers
# =============================
from django.db.models import (
    Q, Sum, Prefetch, Count, F, Case, When, Value
)
from django.db.models.functions import TruncDay

# =============================
# Forms
# =============================
from .forms import (
    PaiementPerStudentForm, MouvementForm, TarifForm,
    ExpenseForm, TransferForm, CashierForm
)
from scuelo.forms import (
    EleveUpdateForm, EleveCreateForm, EcoleCreateForm, ClasseCreateForm,
    ClassUpgradeForm, SchoolChangeForm, UniformReservationForm
)

# =============================
# Models
# =============================
from .models import (
    Expense, Cashier, Mouvement, Tarif, Transfer
)
from scuelo.models import (
    Eleve, Classe, Inscription, StudentLog,
    AnneeScolaire, Ecole, UniformReservation
)

# =============================
# Other Python & Third-Party Libs
# =============================
from datetime import timedelta, datetime, date
import csv
import io
import base64
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns

# =======================
# 4. Payment Management
# =======================

@login_required
def add_payment(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    inscription = Inscription.objects.filter(eleve=student).last()

    if inscription:
        school_name = inscription.classe.ecole.nom if inscription.classe else "Unknown School"
        class_type = inscription.classe.type.nom if inscription.classe else "Unknown Class"
        class_pk = inscription.classe.pk if inscription.classe else None
    else:
        school_name = "Unknown School"
        class_type = "Unknown Class"
        class_pk = None

    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.inscription = inscription  # Ensure inscription is set
            mouvement.causal = form.cleaned_data['causal']

            if inscription:
                mouvement.save()
                print(f"Payment saved for {student.nom} {student.prenom}")  # Debug: Confirm payment saved
                StudentLog.objects.create(
                    student=student,
                    user=request.user,
                    action="Added Payment",
                    old_value="",
                    new_value=f"Payment - {mouvement.montant} - {mouvement.note} - {mouvement.date_paye}"
                )
                
                # Redirect to the class detail view
                if class_pk:
                    return redirect('class_detail', pk=class_pk)
                else:
                    # Handle the case where no class is found
                    return redirect('student_detail', pk=student.pk)
            else:
                form.add_error(None, "No active inscription found for this student.")
        else:
            print(form.errors)  # Debug: Print form errors

    else:
        form = PaiementPerStudentForm()

    return render(request, 'cash/paiements/add_payment.html', {
        'form': form,
        'student': student,
        'school_name': school_name,
        'class_type': class_type,
        'page_identifier': 'S07'
    })

@login_required
def update_paiement(request, pk):
    paiement = get_object_or_404(Mouvement, pk=pk)
    student = paiement.inscription.eleve
    school_name = paiement.inscription.classe.ecole.nom if paiement.inscription.classe else "Unknown School"
    class_type = paiement.inscription.classe.type.nom if paiement.inscription.classe else "Unknown Class"
    
    # Get class PK for redirect
    classe_pk = paiement.inscription.classe.pk if paiement.inscription.classe else None

    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()  # Save the form, updates paiement directly
            
            # Redirect to class detail if class exists, else to student detail
            if classe_pk:
                return redirect('class_detail', pk=classe_pk)
            else:
                return redirect('student_detail', pk=student.pk)
    else:
        form = PaiementPerStudentForm(instance=paiement)  # Instance form

    return render(request, 'cash/paiements/updatepaiment.html', {
        'form': form,
        'student': student,
        'school_name': school_name,
        'class_type': class_type,
        'page_identifier': 'S07'
    })
@method_decorator(login_required, name='dispatch')
class UniformPaymentListView(ListView):
    model = Mouvement
    template_name = 'scuelo/uniforms/uniform_payments.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Mouvement.objects.filter(causal='TEN').select_related('inscription__classe', 'inscription__eleve')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()

        # Group payments by class
        classes = {}
        total_uniforms_across_classes = 0
        total_amount_across_classes = 0  # Initialize total amount across all classes

        for payment in payments:
            classe = payment.inscription.classe.nom
            student = payment.inscription.eleve
            school_type = payment.inscription.classe.type.type_ecole  # Assuming you have this attribute for school type
            cs_py = student.cs_py  # Assuming 'cs_py' contains 'CS' for Caisse Scolaire

            if classe not in classes:
                classes[classe] = {
                    'students': {},
                    'total_uniforms': 0,
                    'total_amount': 0
                }

            if student not in classes[classe]['students']:
                classes[classe]['students'][student] = {
                    'nom': student.nom,
                    'prenom': student.prenom,
                    'uniform_count': 0,
                    'total_amount': 0,
                    'amount_paid': 0,  # Initialize amount paid
                    'condition_eleve': student.condition_eleve,  # Add condition_eleve
                }

            # Determine uniform count based on payment amount, school type, and CS status
            uniform_count = 0
            if cs_py == 'C':
                # For students with 'CS' status
                if school_type == 'P' and payment.montant == 2250:
                    uniform_count = 1
                elif school_type == 'M' and payment.montant == 2000:
                    uniform_count = 1
            else:
                # For other students without 'CS' status
                if school_type in ['P', 'S', 'L']:  # Primaire, Secondaire, Lycée
                    if payment.montant == 4500:
                        uniform_count = 2
                    elif payment.montant == 2250:
                        uniform_count = 1
                elif school_type == 'M':  # Maternelle
                    if payment.montant == 4000:
                        uniform_count = 2
                    elif payment.montant == 2000:
                        uniform_count = 1

            # Update student and class data
            classes[classe]['students'][student]['uniform_count'] += uniform_count
            classes[classe]['students'][student]['total_amount'] += payment.montant
            classes[classe]['students'][student]['amount_paid'] += payment.montant  # Update amount paid
            classes[classe]['total_uniforms'] += uniform_count
            classes[classe]['total_amount'] += payment.montant
            total_uniforms_across_classes += uniform_count
            total_amount_across_classes += payment.montant  # Add to total amount across all classes

        # Pass the context to the template
        context['classes'] = classes  
        context['page_identifier'] = 'S20'  # Example page identifier
        context['total_uniforms'] = total_uniforms_across_classes
        context['total_amount_across_classes'] = total_amount_across_classes  # Add total amount across all classes
        return context
def student_search(request):
    """API endpoint for filtering students by name."""
    term = request.GET.get('q', '')
    students = Eleve.objects.filter(nom__icontains=term)[:10]  # Limits results for performance
    student_list = [{'id': student.id, 'text': f"{student.nom} {student.prenom}"} for student in students]
    return JsonResponse({'results': student_list})    


class UniformReservationListView(TemplateView):
    template_name = "cash/reservations/uniform_reservation_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prefetch related data
        reservations = UniformReservation.objects.prefetch_related(
            Prefetch(
                'student__inscriptions',
                queryset=Inscription.objects.select_related('classe').filter(annee_scolaire__actuel=True),
                to_attr='current_inscriptions'
            )
        )

        # Organize data by class
        classes = {}
        for reservation in reservations:
            student = reservation.student
            current_inscription = getattr(student, 'current_inscriptions', [None])[0]

            if not current_inscription:
                continue

            classe = current_inscription.classe
            class_name = classe.nom

            if class_name not in classes:
                classes[class_name] = {
                    "students": {},
                    "total_uniforms": 0,
                    "total_amount": 0,
                }

            # Add or update student data
            if student.id not in classes[class_name]["students"]:
                classes[class_name]["students"][student.id] = {
                    "nom": student.nom,
                    "prenom": student.prenom,
                    "uniform_count": 0,
                    "total_amount": 0,
                }

            student_data = classes[class_name]["students"][student.id]
            student_data["uniform_count"] += reservation.quantity
            student_data["total_amount"] += reservation.quantity * reservation.cost_per_uniform

            # Update class totals
            classes[class_name]["total_uniforms"] += reservation.quantity
            classes[class_name]["total_amount"] += reservation.quantity * reservation.cost_per_uniform

        # Calculate grand totals
        total_uniforms = sum([info["total_uniforms"] for info in classes.values()])
        total_amount = sum([info["total_amount"] for info in classes.values()])

        context["classes"] = classes
        context["total_uniforms"] = total_uniforms
        context["total_amount"] = total_amount

        return context

class UniformReservationCreateView(CreateView):
    model = UniformReservation
    form_class = UniformReservationForm
    template_name = 'cash/reservations/uniform_reservation_form.html'
    success_url = reverse_lazy('uniform-reservation-list')

    def get_initial(self):
        initial = super().get_initial()
        student = get_object_or_404(Eleve, pk=self.kwargs['student_pk'])
        initial.update({'student': student})
        return initial

    def form_valid(self, form):
        # Automatically set the current school year if not set
        if not form.instance.school_year:
            current_school_year = AnneeScolaire.objects.filter(actuel=True).first()
            if not current_school_year:
                raise Exception("No current school year is defined.")
            form.instance.school_year = current_school_year
        return super().form_valid(form)

class UniformReservationUpdateView(UpdateView):
    model = UniformReservation
    form_class = UniformReservationForm
    template_name = 'cash/reservations/uniform_reservation_form.html'
    success_url = reverse_lazy('uniform-reservation-list')

class UniformReservationDeleteView(DeleteView):
    model = UniformReservation
    template_name = 'cash/reservations/uniform_reservation_confirm_delete.html'
    success_url = reverse_lazy('uniform-reservation-list')    
    

@login_required
def add_tarif(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    if request.method == 'POST':
        form = TarifForm(request.POST)
        if form.is_valid():
            tarif = form.save(commit=False)
            tarif.classe = classe
            tarif.annee_scolaire = current_annee_scolaire
            tarif.save()
            return redirect('manage_tarifs', pk=classe.pk)
    else:
        form = TarifForm()

    return render(request, 'cash/tarif/tarif_form.html', {'form': form, 'classe': classe})

@login_required
def update_tarif(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)
    classe = tarif.classe

    if request.method == 'POST':
        form = TarifForm(request.POST, instance=tarif)
        if form.is_valid():
            form.save()
            return redirect('manage_tarifs', pk=classe.pk)
    else:
        form = TarifForm(instance=tarif)

    return render(request, 'cash/tarif/tarif_form.html', {'form': form, 'classe': classe})

@login_required
def delete_tarif(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)
    classe = tarif.classe

    if request.method == 'POST':  # If the user confirms deletion
        if 'confirm' in request.POST:
            tarif.delete()
            return redirect('manage_tarifs', pk=classe.pk)  # Redirect after deletion
        else:
            return redirect('manage_tarifs', pk=classe.pk)  # Redirect if the user cancels

    return render(request, 'cash/tarif/tarif_confirm_delete.html', {'tarif': tarif})


@login_required
def export_accounting_report(request):
    # Exporting the accounting report to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="accounting_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Period', 'Total Income'])

    grouped_income = Mouvement.objects.filter(
        Q(type='R'),
        date_paye__gte=start_of_period
    ).annotate(period=Case(
        When(date_paye__lt=mid_of_period, then=Value('1st-15th')),
        default=Value('16th-end')
    )).values('period').annotate(total=Sum('montant')).order_by('period')

    for row in grouped_income:
        writer.writerow([row['period'], row['total']])

    return response

@login_required
def update_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        form = MouvementForm(request.POST, instance=mouvement)
        if form.is_valid():
            form.save()
            return redirect('mouvement_list')
    else:
        form = MouvementForm(instance=mouvement)
    return render(request, 'cash/mouvement/update_mouvement.html', {'form': form,  'mouvement': mouvement , 'page_identifier': 'S13'})

@login_required
def delete_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        return redirect('mouvement_list')
    return render(request, 'cash/mouvement/delete_mouvement.html', {'mouvement': mouvement ,   'page_identifier': 'S14' })



@login_required
def late_payment_report(request):
    data = {}
    grand_total_remaining = 0
    grand_total_diff_sco = 0
    grand_total_diff_can = 0

    try:
        current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)
    except AnneeScolaire.DoesNotExist:
        return render(request, 'cash/late_payment.html', {
            'data': data,
            'error': 'No current school year is set.',
            'page_identifier': 'S58'
        })

    schools = Ecole.objects.prefetch_related(
        Prefetch(
            'classe_set',
            queryset=Classe.objects.prefetch_related(
                Prefetch(
                    'inscription_set',
                    queryset=Inscription.objects.select_related('eleve')
                )
            )
        )
    )

    for school in schools:
        class_data = {}
        for classe in school.classe_set.all():
            students = Eleve.objects.filter(
                inscriptions__classe=classe,
                inscriptions__annee_scolaire=current_annee_scolaire,
                inscriptions__classe__ecole=school,
                cs_py='P',
                condition_eleve__in=["CONF", "PROP"]
            ).distinct()

            student_data = []
            total_class_remaining = 0
            total_diff_sco = 0
            total_diff_can = 0

            for student in students:
                # Fetch SCO payments only
                sco_payments = Mouvement.objects.filter(
                    inscription__eleve=student,
                    causal__in=['SCO'],
                    inscription__annee_scolaire=current_annee_scolaire
                )
                sco_payments = Mouvement.objects.filter(
                    inscription__eleve=student,
                    inscription__annee_scolaire=current_annee_scolaire
                ).exclude(causal__in=['CAN', 'TEN', 'INS'])

                sco_paid = sco_payments.aggregate(Sum('montant'))['montant__sum'] or 0

                can_payments = Mouvement.objects.filter(
                    inscription__eleve=student,
                    causal='CAN',
                    inscription__annee_scolaire=current_annee_scolaire
                )
                can_paid = can_payments.aggregate(Sum('montant'))['montant__sum'] or 0

                tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire)
                sco_exigible = tarifs.filter(causal__in=['SCO1' , 'SCO2'  ,'SCO3']).aggregate(Sum('montant'))[
                                    'montant__sum'] or 0
                can_exigible = tarifs.filter(causal='CAN').aggregate(Sum('montant'))['montant__sum'] or 0

                diff_sco = sco_exigible - sco_paid
                diff_can = can_exigible - can_paid
                retards = diff_sco + diff_can

                if retards > 0:
                    total_exigible = sco_exigible + can_exigible
                    percentage_paid = (
                        (sco_paid + can_paid) / total_exigible * 100
                    ) if total_exigible > 0 else 0

                    remaining_percentage = (
                        retards / total_exigible * 100
                    ) if total_exigible > 0 else 0

                    student_data.append({
                        'id': student.id,
                        'nom': student.nom,
                        'prenom': student.prenom,
                        'sex': student.sex,
                        'cs_py': student.cs_py,
                        'sco_paid': sco_paid,
                        'sco_exigible': sco_exigible,
                        'diff_sco': diff_sco,
                        'can_paid': can_paid,
                        'can_exigible': can_exigible,
                        'diff_can': diff_can,
                        'retards': retards,
                        'percentage_paid': percentage_paid,
                        'remaining_percentage': remaining_percentage,
                        'note': student.note_eleve,
                        'condition_eleve': student.condition_eleve,  # Include condition_eleve
                        'page_identifier': 'S30'
                    })

                    total_diff_sco += diff_sco
                    total_diff_can += diff_can

                total_class_remaining += retards

            if student_data:
                class_data[classe.nom] = {
                    'students': student_data,
                    'total_class_remaining': total_class_remaining,
                    'total_diff_sco': total_diff_sco,
                    'total_diff_can': total_diff_can,
                }

                grand_total_diff_sco += total_diff_sco
                grand_total_diff_can += total_diff_can
                # grand_total_remaining += total_class_remaining # Don't double count

        if class_data:
            data[school.nom] = class_data

    grand_total_remaining = grand_total_diff_sco + grand_total_diff_can # this is correct now

    return render(request, 'cash/late_payment.html', {
        'data': data,
        'grand_total_remaining': grand_total_remaining,
        'grand_total_diff_sco': grand_total_diff_sco,
        'page_identifier': 'S58',
        'grand_total_diff_can': grand_total_diff_can,
        'current_annee_scolaire': current_annee_scolaire,
    })





from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def expense_list(request):
    # Récupérer l'année scolaire courante via la méthode de classe
    current_year = AnneeScolaire.get_current_year()
    if not current_year:
        # On peut gérer le cas sans année courante définie
        return render(request, 'cash/expense/expense_list.html', {
            'expenses': [],
            'total_expense': 0,
            'page_identifier': 'S31',
            'error_message': "Aucune année scolaire courante définie.",
        })

    # Filtrer les dépenses dans la plage de l'année scolaire courante
    expenses = Expense.objects.filter(
        date__range=(current_year.date_initiale, current_year.date_finale)
    ).order_by('-date')

    progressive_total = 0
    total_expense = 0
    expense_data = []

    for expense in expenses:
        total_expense += expense.amount
        progressive_total += expense.amount
        expense_data.append({
            'expense': expense,
            'progressive_total': -abs(progressive_total),
        })

    return render(request, 'cash/expense/expense_list.html', {
        'expenses': expense_data,
        'total_expense': total_expense,
        'page_identifier': 'S31',
        'annee_scolaire': current_year,
    })


    
def get_sorted_expenses(request):
    sort_by = request.GET.get("sort_by", "date")  # Default sorting by date
    order = request.GET.get("order", "asc")  # Default to ascending order
    
    # Apply sorting dynamically
    if order == "desc":
        sort_by = f"-{sort_by}"  # Prefix '-' for descending order
    
    expenses = Expense.objects.all().order_by(sort_by)

    expense_list = []
    progressive_total = 0  # Track running total
    
    if order == "asc":  # Calculate normally for ascending
        for exp in expenses:
            progressive_total += exp.amount
            expense_list.append({
                "date": exp.date.strftime("%Y-%m-%d"),
                "description": f"COMPT-{exp.description}",
                "amount": exp.amount,
                "progressive_total": progressive_total
            })
    else:  # Calculate progressive total from bottom to top
        reversed_expenses = list(expenses)[::-1]
        progressive_total = sum(exp.amount for exp in reversed_expenses)  # Start from full total
        
        for exp in reversed_expenses:
            expense_list.append({
                "date": exp.date.strftime("%Y-%m-%d"),
                "description": f"COMPT-{exp.description}",
                "amount": exp.amount,
                "progressive_total": progressive_total
            })
            progressive_total -= exp.amount  # Subtract backwards

    return JsonResponse({"expenses": expense_list})

def expense_create(request):
    # Fetch the cashier "C_SCO"
    cashier = get_object_or_404(Cashier, name="C_SCO")

    # Calculate total income (sum of montant in Mouvement table)
    total_income = Mouvement.objects.aggregate(total=Sum('montant'))['total'] or 0

    # Calculate total expenses (sum of amount in Expense table)
    total_expenses = Expense.objects.filter(cashier=cashier).aggregate(total=Sum('amount'))['total'] or 0

    # Calculate balance
    balance = total_income - total_expenses

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.cashier = cashier  # Associate expense with the C_SCO cashier

            # Generate a unique legacy_id if it's not already set
            if not expense.legacy_id:
                expense.legacy_id = get_random_string(32)  # Generate a random string

            try:
                expense.save()
                messages.success(request, "Expense created successfully!")
                return redirect('expense_list')
            except IntegrityError:
                messages.error(request, "An error occurred: Duplicate legacy_id. Please try again.")
                # Optionally, regenerate the legacy_id and try saving again
                expense.legacy_id = get_random_string(32)
                try:
                    expense.save()
                    messages.success(request, "Expense created successfully after regenerating legacy_id!")
                    return redirect('expense_list')
                except IntegrityError:
                    messages.error(request, "Failed to generate a unique legacy_id. Please contact support.")
                    # Log the error here if necessary
                    pass  # Handle the case where a unique ID cannot be generated
    else:
        form = ExpenseForm()

    # Pass balance and total income to template
    context = {
        'form': form,
        'cashier_balance': balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'page_identifier': 'S60',  # Example page identifier
    }
    
    return render(request, 'cash/expense/expense_form.html', context)

def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'cash/expense/expense_form.html', {'form': form ,'page_identifier': 'S33'})

def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        return redirect('expense_list')
    return render(request, 'cash/expense/expense_confirm_delete.html', {'expense': expense , 'page_identifier': 'S34'})

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

@login_required
def income_list_view(request):
    # Récupère l'année scolaire courante
    current_year = AnneeScolaire.get_current_year()

    if not current_year:
        return render(request, 'cash/inoutflows/income_list.html', {
            'income_list': [],
            'total_montant': 0,
            'page_identifier': 'S35',
            'error_message': "Aucune année scolaire courante définie.",
        })

    # Récupère les paiements liés à cette année scolaire uniquement
    incomes = Mouvement.objects.filter(
        inscription__annee_scolaire=current_year
    ).order_by('-date_paye')

    total_montant = incomes.aggregate(total=Sum('montant'))['total'] or 0

    income_list = []
    progressive_total = 0
    for income in incomes:
        progressive_total += income.montant
        inscription_info = "N/A"
        student_info = "N/A"
        class_info = "N/A"

        if income.inscription:
            if income.inscription.eleve:
                student_info = f"{income.inscription.eleve.nom} {income.inscription.eleve.prenom}"
            if income.inscription.classe:
                class_info = f"{income.inscription.classe.nom}"
            inscription_info = f"{student_info} - {class_info}"

        income_list.append({
            'date': income.date_paye,
            'causal': income.causal,
            'montant': income.montant,
            'progressive': progressive_total,
            'inscription_info': inscription_info,
        })

    context = {
        'income_list': income_list,
        'total_montant': total_montant,
        'page_identifier': 'S35',
        'annee_scolaire': current_year,
    }

    return render(request, 'cash/inoutflows/income_list.html', context)



@login_required
def entree_sortie(request):
    cashier = get_object_or_404(Cashier, name="C_SCO")

    all_annee_scolaires = AnneeScolaire.objects.all().order_by('date_initiale')

    selected_year_id = request.GET.get('annee_scolaire')
    if selected_year_id:
        annee_scolaire = get_object_or_404(AnneeScolaire, pk=selected_year_id)
    else:
        annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()

    initial_balance = 0  # No carryover

    reset_requested = request.GET.get('reset') == 'true'
    if reset_requested:
        with transaction.atomic():
            Mouvement.objects.filter(inscription__annee_scolaire=annee_scolaire).delete()
            Expense.objects.filter(date__range=(annee_scolaire.date_initiale, annee_scolaire.date_finale)).delete()

    incomes = Mouvement.objects.filter(
        inscription__annee_scolaire=annee_scolaire
    ).order_by('date_paye')

    expenses = Expense.objects.filter(
        date__range=(annee_scolaire.date_initiale, annee_scolaire.date_finale)
    ).order_by('date')

    entries = []
    total_entree = 0
    total_sortie = 0
    for income in incomes:
        student_name = f"{income.inscription.eleve.nom} {income.inscription.eleve.prenom}" if income.inscription else "Inconnu"
        description = f"{income.causal} - {student_name}"
        entries.append({
            'date': income.date_paye,
            'description': description,
            'entree': income.montant,
            'sortie': 0,
        })
        total_entree += income.montant

    for expense in expenses:
        description = f"COMPT {expense.description or ''}"
        entries.append({
            'date': expense.date,
            'description': description,
            'entree': 0,
            'sortie': expense.amount,
        })
        total_sortie += expense.amount

    entries.sort(key=lambda x: x['date'])

    progressive_balance = initial_balance
    for entry in entries:
        progressive_balance += entry['entree'] - entry['sortie']
        entry['progressive'] = progressive_balance

    total_balance = progressive_balance

    return render(request, 'cash/inoutflows/entree_sortie.html', {
        'entries': entries,
        'cashier': cashier,
        'initial_balance': initial_balance,
        'balance': cashier.balance(),
        'total_balance': total_balance,
        'total_entree': total_entree,
        'total_sortie': total_sortie,
        'annee_scolaire': annee_scolaire,
        'all_annee_scolaires': all_annee_scolaires,
        'page_identifier': 'S35',
        'reset_requested': reset_requested,
    })


def rapport_comptable(request):
    # Fetch the C_SCO cashier
    cashier = get_object_or_404(Cashier, name="C_SCO")

    # Get current date
    today = date.today()

    # Fetch all incomes (Mouvement) for this cashier
    incomes = Mouvement.objects.filter(cashier=cashier, montant__gt=0)

    # Prepare data for accounting report
    accounting_data = generate_accounting_report(incomes)

    return render(request, 'cash/inoutflows/rapport_comptable.html', {
        'cashier': cashier,
        'accounting_data': accounting_data,
        'balance': cashier.balance(), 
        'page_identifier': 'S36'# Use the balance method from Cashier model
    })

def generate_accounting_report(incomes):
    """
    Generate accounting report data grouped by type and period.
    
    :param incomes: QuerySet of income movements.
    :return: A list of dictionaries with grouped income data.
    """
    
    grouped_incomes = {}

    for income in incomes:
        # Determine grouping based on your requirement
        week_start = income.date_paye - timedelta(days=income.date_paye.weekday())  # Start of week (Monday)
        if income.date_paye.day <= 15:
            period_key = f"{income.date_paye.year}-{income.date_paye.month}-01"  # First half of the month
        else:
            period_key = f"{income.date_paye.year}-{income.date_paye.month}-16"  # Second half of the month
        
        if period_key not in grouped_incomes:
            grouped_incomes[period_key] = {
                'total_amount': 0,
                'type': income.causal,
                'entries': []
            }
        
        grouped_incomes[period_key]['total_amount'] += income.montant
        grouped_incomes[period_key]['entries'].append(income)

    return grouped_incomes


def export_entree_sortie(request):
    # Fetch the C_SCO cashier
    cashier = get_object_or_404(Cashier, name="C_SCO")

    # Fetch all transactions (Mouvement) for this cashier
    mouvements = Mouvement.objects.filter().order_by('date_paye')

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="entree_sortie_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Entrée (Income)', 'Sortie (Outcome)', 'Solde Progressif'])

    progressive_balance = 0

    # Write data rows
    for mouvement in mouvements:
        if mouvement.montant > 0:  # Income
            description = f"Income - {mouvement.causal}"
            entry = [mouvement.date_paye, description, mouvement.montant, 0, progressive_balance + mouvement.montant]
            progressive_balance += mouvement.montant
        else:  # Outcome
            description = f"Outcome - {mouvement.causal}"
            entry = [mouvement.date_paye, description, 0, abs(mouvement.montant), progressive_balance]
            progressive_balance -= abs(mouvement.montant)

        writer.writerow(entry)

    return response
def export_rapport_comptable(request):
    # Fetch the C_SCO cashier
    cashier = get_object_or_404(Cashier, name="C_SCO")

    # Fetch all incomes (Mouvement) for this cashier
    incomes = Mouvement.objects.filter(cashier=cashier, montant__gt=0)

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rapport_comptable_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Période', 'Type', 'Total Entrées'])

    grouped_incomes = generate_accounting_report(incomes)

    # Write data rows
    for period, data in grouped_incomes.items():
        writer.writerow([period, data['type'], data['total_amount']])

    return response


# List all transfers
def transfer_list(request):
    transfers = Transfer.objects.all().order_by('-date')  # Order by date descending
    return render(request, 'cash/transfert/transfer_list.html', {'transfers': transfers , 'page_identifier': 'S37'})

# Create a new transfer
def create_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save()
            # Update balances after saving the transfer
            from_cashier = transfer.from_cashier
            to_cashier = transfer.to_cashier
            
            # Adjust balances
            from_cashier.balance(from_cashier)  # Deduct amount from sender's balance
            to_cashier.balance(to_cashier)      # Add amount to receiver's balance

            messages.success(request, "Transfer created successfully!")
            return redirect('transfer_list')
    else:
        form = TransferForm()

    return render(request, 'cash/transfert/create_transfert.html', {'form': form , 'page_identifier': 'S38'})

# Update an existing transfer
def update_transfer(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    
    if request.method == 'POST':
        form = TransferForm(request.POST, instance=transfer)
        if form.is_valid():
            # Update balances before saving the updated transfer
            original_from_cashier = transfer.from_cashier
            original_to_cashier = transfer.to_cashier
            
            # Adjust balances back before updating
            original_from_cashier.balance(original_from_cashier)  # Add back original amount
            original_to_cashier.balance(original_to_cashier)      # Subtract original amount
            
            # Save the updated transfer
            transfer = form.save()
            
            # Update balances after saving the new amount
            original_from_cashier.balance(original_from_cashier)  # Deduct new amount from sender
            original_to_cashier.balance(original_to_cashier)      # Add new amount to receiver
            
            messages.success(request, "Transfer updated successfully!")
            return redirect('transfer_list')
    else:
        form = TransferForm(instance=transfer)

    return render(request, 'cash/transfert/update_transfer.html',
                  {'form': form , 'page_identifier': 'S39'})

# Delete a transfer
def delete_transfer(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    
    if request.method == 'POST':
        # Adjust balances before deletion
        from_cashier = transfer.from_cashier
        to_cashier = transfer.to_cashier
        
        from_cashier.balance(from_cashier)  # Restore balance for sender
        to_cashier.balance(to_cashier)      # Deduct balance for receiver
        
        transfer.delete()
        messages.success(request, "Transfer deleted successfully!")
        return redirect('transfer_list')

    return render(request, 'cash/transfert/delete_transfer.html', 
                  {'transfer': transfer , 'page_identifier': 'S40'})

# List all cashiers
def cashier_list(request):
    cashiers = Cashier.objects.all().order_by('name')  # Order by name
    return render(request, 'cash/cashier/cashier_list.html', {'cashiers': cashiers
                                             ,'page_identifier': 'S41'                 })

# Create a new cashier
def create_cashier(request):
    if request.method == 'POST':
        form = CashierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cashier created successfully!")
            return redirect('cashier_list')
    else:
        form = CashierForm()

    return render(request, 'cash/cashier/create_cashier.html', {'form': form      ,'page_identifier': 'S42'       })

# Update an existing cashier
def update_cashier(request, pk):
    cashier = get_object_or_404(Cashier, pk=pk)
    
    if request.method == 'POST':
        form = CashierForm(request.POST, instance=cashier)
        if form.is_valid():
            form.save()
            messages.success(request, "Cashier updated successfully!")
            return redirect('cashier_list')
    else:
        form = CashierForm(instance=cashier)

    return render(request, 'cash/cashier/update_cashier.html', {'form': form      ,'page_identifier': 'S43'       })

# Delete a cashier
def delete_cashier(request, pk):
    cashier = get_object_or_404(Cashier, pk=pk)
    
    if request.method == 'POST':
        cashier.delete()
        messages.success(request, "Cashier deleted successfully!")
        return redirect('cashier_list')

    return render(request, 'cash/cashier/delete_cashier.html', {'cashier': cashier      ,'page_identifier': 'S44'       })





def transfer_list(request):
    transfers = Transfer.objects.all().order_by('-date').select_related('from_cashier', 'to_cashier' )  # Order by date descending, select related cashiers for efficient query
    for transfer in transfers:
        transfer.from_cashier_balance = transfer.from_cashier.balance()  # Calculate balance
        transfer.to_cashier_balance = transfer.to_cashier.balance() # Calculate balance
    return render(request, 'cash/transfert/transfer_list.html', {'transfers': transfers  ,'page_identifier': 'S45' })

def create_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)  # Do not save to DB yet
            
            # Automatically assign the current AnneeScolaire
            current_year = AnneeScolaire.get_current_year()
            if current_year:
                transfer.annee_scolaire = current_year
            else:
                messages.error(request, "No active school year found.")
                return redirect('transfer_list')

            # Save the transfer and update balances
            transfer.save()

            # Update balances for cashiers involved in the transfer
            from_cashier = transfer.from_cashier
            to_cashier = transfer.to_cashier
            
            from_cashier.balance()  # Recalculate balance for sender
            to_cashier.balance()    # Recalculate balance for receiver

            messages.success(request, "Transfer created successfully!")
            return redirect('transfer_list')
    else:
        form = TransferForm()

    return render(request, 'cash/transfert/create_transfert.html', {'form': form  ,'page_identifier': 'S46' })

# Update an existing transfer
def update_transfer(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    
    if request.method == 'POST':
        form = TransferForm(request.POST, instance=transfer)
        if form.is_valid():
            # Update balances before saving the updated transfer
            original_from_cashier = transfer.from_cashier
            original_to_cashier = transfer.to_cashier
            
            # Adjust balances back before updating
            original_from_cashier.balance(original_from_cashier)  # Add back original amount
            original_to_cashier.balance(original_to_cashier)      # Subtract original amount
            
            # Save the updated transfer
            transfer = form.save()
            
            # Update balances after saving the new amount
            original_from_cashier.balance(original_from_cashier)  # Deduct new amount from sender
            original_to_cashier.balance(original_to_cashier)      # Add new amount to receiver
            
            messages.success(request, "Transfer updated successfully!")
            return redirect('transfer_list')
    else:
        form = TransferForm(instance=transfer)

    return render(request, 'cash/transfert/update_transfer.html', {'form': form  ,'page_identifier': 'S47' })

# Delete a transfer
def delete_transfer(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    
    if request.method == 'POST':
        # Adjust balances before deletion
        from_cashier = transfer.from_cashier
        to_cashier = transfer.to_cashier
        
        from_cashier.balance(from_cashier)  # Restore balance for sender
        to_cashier.balance(to_cashier)      # Deduct balance for receiver
        
        transfer.delete()
        messages.success(request, "Transfer deleted successfully!")
        return redirect('transfer_list')

    return render(request, 'cash/transfert/delete_transfer.html', {'transfer': transfer  ,'page_identifier': 'S48' })

# List all cashiers
def cashier_list(request):
    cashiers = Cashier.objects.all().order_by('name')  # Order by name
    return render(request, 'cash/cashier/cashier_list.html', {'cashiers': cashiers ,'page_identifier': 'S49' })

# Create a new cashier
def create_cashier(request):
    if request.method == 'POST':
        form = CashierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cashier created successfully!")
            return redirect('cashier_list')
    else:
        form = CashierForm()

    return render(request, 'cash/cashier/create_cashier.html', {'form': form  ,'page_identifier': 'S50' })

# Update an existing cashier
def update_cashier(request, pk):
    cashier = get_object_or_404(Cashier, pk=pk)
    
    if request.method == 'POST':
        form = CashierForm(request.POST, instance=cashier)
        if form.is_valid():
            form.save()
            messages.success(request, "Cashier updated successfully!")
            return redirect('cashier_list')
    else:
        form = CashierForm(instance=cashier)

    return render(request, 'cash/cashier/update_cashier.html', {'form': form  ,'page_identifier': 'S51' })


# Delete a cashier
def delete_cashier(request, pk):
    cashier = get_object_or_404(Cashier, pk=pk)
    
    if request.method == 'POST':
        cashier.delete()
        messages.success(request, "Cashier deleted successfully!")
        return redirect('cashier_list')

    return render(request, 'cash/cashier/delete_cashier.html', {'cashier': cashier ,  'page_identifier': 'S52' })


# Cashier detail view
def cashier_detail(request, pk):
    cashier = get_object_or_404(Cashier, pk=pk)
    
    # Get the balance of the cashier
    balance = cashier.balance()  # Assuming this method is defined in your Cashier model

    # Get transfers involving this cashier
    transfers_out = Transfer.objects.filter(from_cashier=cashier).order_by('-date')
    transfers_in = Transfer.objects.filter(to_cashier=cashier).order_by('-date')

    return render(request, 'cash/cashier/cashier_detail.html', {
        'cashier': cashier,
        'balance': balance,
        'transfers_out': transfers_out,
        'transfers_in': transfers_in
         ,'page_identifier': 'S53' 
    })
def get_cashier_balance(request):
    cashier_id = request.GET.get('cashier_id')
    try:
        cashier = Cashier.objects.get(pk=cashier_id)
        balance = cashier.balance()  # Assuming you have a balance() method
        return JsonResponse({'balance': balance})
    except Cashier.DoesNotExist:
        return JsonResponse({'error': 'Cashier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_delay_per_class(request, pk):
    # Get the current school year
    try:
        current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)
    except AnneeScolaire.DoesNotExist:
        return render(request, 'cash/payment_delay_per_class.html', {
            'error': 'No current school year is set.',
             'page_identifier': 'S54' 
        })

    # Fetch the specific class
    try:
        classe = Classe.objects.get(id=pk)
    except Classe.DoesNotExist:
        return render(request, 'cash/payment_delay_per_class.html', {
            'error': 'Class not found.',
             'page_identifier': 'S54' 
        })

    # Fetch students linked to this class through inscriptions
    students = Eleve.objects.filter(
        inscriptions__classe=classe,
        inscriptions__annee_scolaire=current_annee_scolaire,
        cs_py='P',
       condition_eleve__in=["CONF", "PROP"]
    ).distinct()

    student_data = []
    total_diff_sco = 0
    total_diff_can = 0

    for student in students:
        # Calculate SCO and CAN payments and expectations
        payments = Mouvement.objects.filter(inscription__eleve=student)
        # Calculate SCO Paid (excluding CAN and TEN)
        sco_paid = Mouvement.objects.filter(
            inscription__eleve=student,
            inscription__annee_scolaire=current_annee_scolaire
        ).exclude(causal__in=['CAN', 'TEN','INS']).aggregate(Sum('montant'))['montant__sum'] or 0

        can_paid = Mouvement.objects.filter(
            inscription__eleve=student,
            causal='CAN',
            inscription__annee_scolaire=current_annee_scolaire
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire)
        sco_exigible = tarifs.filter(causal__in=['SCO1', 'SCO2', 'SCO3']).aggregate(Sum('montant'))['montant__sum'] or 0
        can_exigible = tarifs.filter(causal='CAN').aggregate(Sum('montant'))['montant__sum'] or 0

        diff_sco = sco_exigible - sco_paid
        diff_can = can_exigible - can_paid

        # Only include students with payment delays
        if diff_sco > 0 or diff_can > 0:
            student_data.append({
                'id': student.id,
                'nom': student.nom,
                'prenom': student.prenom,
                'condition_eleve': student.condition_eleve,
                'sex': student.sex,
                'sco_paid': sco_paid,
                'sco_exigible': sco_exigible,
                'diff_sco': diff_sco,
                'can_paid': can_paid,
                'can_exigible': can_exigible,
                'diff_can': diff_can,
            })

            total_diff_sco += diff_sco
            total_diff_can += diff_can

    return render(request, 'cash/payment_delay_per_class.html', {
        'classe': classe,
        'students': student_data,
        'total_diff_sco': total_diff_sco,
        'total_diff_can': total_diff_can,
         'page_identifier': 'S54' 
    })


@login_required
def classe_information(request, pk):
    classe = get_object_or_404(Classe, id=pk)  # Fetch the specific class
    school_name = classe.ecole.nom  # Assuming 'ecole' is a ForeignKey in Classe
    school_year = AnneeScolaire.objects.filter(actuel=True).first()  # Get current school year
    tarifs = Tarif.objects.filter(classe=classe)  # Get all tarifs related to this class

    # Count total students in the class
    total_students = Eleve.objects.filter(inscriptions__classe=classe).count()

    # Count confirmed students (PY & CONF)
    #total_students_confirmed = Eleve.objects.filter(inscriptions__classe=classe, condition_eleve='CONF').count()
    total_students_confirmed = Eleve.objects.filter(
    inscriptions__classe=classe,
    condition_eleve='CONF',
    cs_py='P'
    ).count()

    # Count students by categories
    total_CS = Eleve.objects.filter(inscriptions__classe=classe, cs_py='C').count()
    total_PY = Eleve.objects.filter(inscriptions__classe=classe, cs_py='P').count()
    other =  total_students - (total_PY + total_CS )

    # Calculate expected payments based on tranches
    sco1 = tarifs.filter(causal="SCO1").aggregate(total=models.Sum('montant'))['total'] or 0
    sco2 = tarifs.filter(causal="SCO2").aggregate(total=models.Sum('montant'))['total'] or 0
    sco3 = tarifs.filter(causal="SCO3").aggregate(total=models.Sum('montant'))['total'] or 0

    first_tranche = sco1
    second_tranche = sco1 + sco2
    third_tranche = sco1 + sco2 + sco3

    # Calculate progressif per tranche (PY & CONF)
    progressif_per_tranche = {
        '1er': first_tranche * total_students_confirmed,
        '2eme': second_tranche * total_students_confirmed,
        '3eme': third_tranche * total_students_confirmed,
    }
    expected_total_school_fees = third_tranche * total_students_confirmed  
    total_py_uniforms_received = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=school_year,
        inscription__eleve__cs_py='P',  # Filter for PY students
        causal='TEN'  # Assuming TEN is the causal for uniforms
    ).aggregate(total=Sum('montant'))['total'] or 0
    actual_total_school_fees_received = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=school_year,
        causal__in=['SCO']
    ).aggregate(total=Sum('montant'))['total'] or 0
    cost_per_uniform = UniformReservation.objects.filter(student_type='P').first().cost_per_uniform if UniformReservation.objects.filter(student_type='P').first() else 0 # 
    total_py_uniforms_expected = total_students_confirmed * cost_per_uniform
    return render(request, 'cash/tarif/classe_information.html', {
        'classe': classe,
        'school_name': school_name,
        'school_year': school_year,
        'tarifs': tarifs,
        'total_students': total_students,
        'total_students_confirmed': total_students_confirmed,
        'total_CS': total_CS,
        'total_PY': total_PY,
        'other':other,
        'progressif_per_tranche': progressif_per_tranche,
        'first_tranche': first_tranche,
        'second_tranche': second_tranche,
        'third_tranche': third_tranche,
        'total_py_uniforms_received':total_py_uniforms_received,
        'actual_total_school_fees_received':actual_total_school_fees_received,
        'expected_total_school_fees':expected_total_school_fees,
        'total_py_uniforms_expected':total_py_uniforms_expected,
         'page_identifier': 'S55' 
    })



@login_required
def tarif_update(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)  # Fetch the specific tarif
    if request.method == 'POST':
        form = TarifForm(request.POST, instance=tarif)  # Bind the form with the existing instance
        if form.is_valid():
            form.save()  # Save the updated tarif
            return redirect('classe_information', pk=tarif.classe.pk)  # Redirect back to class information page
    else:
        form = TarifForm(instance=tarif)  # Pre-fill the form with existing data

    return render(request, 'cash/tarif_form.html', {'form': form  ,'page_identifier': 'S56' })    

@login_required
def tarif_delete(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)  # Fetch the specific tarif
    if request.method == 'POST':
        tarif.delete()  # Delete the tarif
        return redirect('classe_information', pk=tarif.classe.pk)  # Redirect back to class information page

    return render(request, 'cash/tarif_confirm_delete.html', {'tarif': tarif  ,'page_identifier': 'S57' })

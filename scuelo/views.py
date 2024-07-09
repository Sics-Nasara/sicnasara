from django_filters.views import FilterView
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import UpdateView
from django.db import transaction
from django.views.generic import CreateView
from django.views.generic import (DetailView, ListView,
                                  View, ListView, CreateView, UpdateView
                                  )
from django.db.models import Q, Max, Sum, Count, Case, When, IntegerField
from .forms import  PaiementPerStudentForm ,  EleveUpdateForm
#InscriptionForm, EleveCreateForm, EleveUpdateForm, AnneeScolaireForm
from .filters import EleveFilter
from scuelo.models import Eleve, Classe, Inscription, AnneeScolaire ,  Mouvement
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


'''@login_required
def home(request):
    breadcrumbs = [('/', 'Home')]
    classes = Classe.objects.all()
    return render(request, 'scuelo/home.html', {'breadcrumbs': breadcrumbs, 'classes': classes})'''


@login_required
def home(request):
    classes = Classe.objects.all()
    return render(request, 'scuelo/home.html', {'classes': classes})

@login_required
def class_detail(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    students = Eleve.objects.filter(inscription__classe=classe)
    breadcrumbs = [('/', 'Home'), (reverse('home'), 'Classes'), ('#', classe.nom)]
    return render(request, 'scuelo/students/listperclasse.html', {'classe': classe, 'students': students, 'breadcrumbs': breadcrumbs})



@login_required
def student_detail(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    inscriptions = Inscription.objects.filter(eleve=student)
    payments = Mouvement.objects.filter(inscription__eleve=student)
    total_payment = payments.aggregate(Sum('montant'))['montant__sum'] or 0

    current_class = student.current_class
    if current_class:
        breadcrumbs = [
            ('/', 'Home'),
            (reverse('home'), 'Classes'),
            (reverse('class_detail', kwargs={'pk': current_class.pk}), current_class.nom),
            ('#', f"{student.nom} {student.prenom}")
        ]
    else:
        breadcrumbs = [
            ('/', 'Home'),
            (reverse('home'), 'Classes'),
            ('#', f"{student.nom} {student.prenom}")
        ]
    form = PaiementPerStudentForm()
    return render(request, 'scuelo/students/studentdetail.html', {
        'student': student,
        'inscriptions': inscriptions,
        'payments': payments,
        'total_payment': total_payment,
        'breadcrumbs': breadcrumbs,
        'form': form
    })


@method_decorator(csrf_exempt, name='dispatch')
def add_paiement(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    form = PaiementPerStudentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.inscription = Inscription.objects.filter(eleve=student).last()
            paiement.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def update_paiement(request, pk):
    paiement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            return redirect('student_detail', pk=paiement.inscription.eleve.pk)
    else:
        form = PaiementPerStudentForm(instance=paiement)

    return render(request, 'scuelo/paiements/updatepaiment.html', {'form': form, 'paiement': paiement})


@login_required
def student_update(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = EleveUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_detail', pk=student.pk)
    else:
        form = EleveUpdateForm(instance=student)
    
    return render(request, 'scuelo/students/studentupdate.html', {'form': form, 'student': student})



#scuelo/templates/scuelo/students/listperclasse.html
@login_required
def important_info(request):
    return render(request, 'scuelo/important_info.html')

@login_required
def user_management(request):
    return render(request, 'scuelo/user_management.html')

@login_required
def student_management(request):
    return render(request, 'scuelo/student_management.html')

@login_required
def teacher_management(request):
    return render(request, 'scuelo/teacher_management.html')

@login_required
def financial_management(request):
    return render(request, 'scuelo/financial_management.html')

@login_required
def reporting(request):
    return render(request, 'scuelo/reporting.html')

@login_required
def document_management(request):
    return render(request, 'scuelo/document_management.html')



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'scuelo/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def recording_on_records(request):
    # Your logic for recording_on_records
    return render(request, 'scuelo/recording_on_records.html')


def working_sessions(request):
    # Your logic for working_sessions
    return render(request, 'scuelo/working_sessions.html')

def types_of_fees(request):
    # Your logic for types_of_fees
    return render(request, 'scuelo/types_of_fees.html')

def school_uniforms(request):
    # Your logic for school_uniforms
    return render(request, 'scuelo/school_uniforms.html')

def late_payment(request):
    # Your logic for late_payment
    return render(request, 'scuelo/late_payment.html')

def print_receipts(request):
    # Your logic for print_receipts
    return render(request, 'scuelo/print_receipts.html')

def generic_reports(request):
    # Your logic for generic_reports
    return render(request, 'scuelo/generic_reports.html')


def cash_inflows_outflows(request):
    # Your logic for cash_inflows_outflows
    return render(request, 'scuelo/cash_inflows_outflows.html')

def cash_flow_report(request):
    # Your logic for cash_flow_report
    return render(request, 'scuelo/cash_flow_report.html')

def export_for_accounting(request):
    # Your logic for export_for_accounting
    return render(request, 'scuelo/export_for_accounting.html')

def offsite_students(request):
    # Your logic for offsite_students
    return render(request, 'scuelo/offsite_students.html')

def directly_managed_students(request):
    # Your logic for directly_managed_students
    return render(request, 'scuelo/directly_managed_students.html')

def new_student(request):
    # Your logic for new_student
    return render(request, 'scuelo/new_student.html')

def change_school(request):
    # Your logic for change_school
    return render(request, 'scuelo/change_school.html')

def class_upgrade(request):
    # Your logic for class_upgrade
    return render(request, 'scuelo/class_upgrade.html')

def start_school_year(request):
    # Your logic for start_school_year
    return render(request, 'scuelo/start_school_year.html')


def teacher_registry(request):
    # Your logic for teacher_registry
    return render(request, 'scuelo/teacher_registry.html')

def class_teachers_association(request):
    # Your logic for class_teachers_association
    return render(request, 'scuelo/class_teachers_association.html')
def student_documents(request):
    # Your logic for student_documents
    return render(request, 'scuelo/student_documents.html')

def teacher_documents(request):
    # Your logic for teacher_documents
    return render(request, 'scuelo/teacher_documents.html')

def accounting_documents(request):
    # Your logic for accounting_documents
    return render(request, 'scuelo/accounting_documents.html')
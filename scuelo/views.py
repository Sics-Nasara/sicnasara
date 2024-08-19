# Authentication
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic import DetailView, ListView, CreateView, TemplateView
from django.db.models import Q, Sum, Prefetch, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect
# Models and Forms
from .forms import (
    PaiementPerStudentForm, EleveUpdateForm, MouvementForm,
    EleveCreateForm, EcoleCreateForm, ClasseCreateForm,
    TarifForm, ClassUpgradeForm, SchoolChangeForm
)
from scuelo.models import (
    Eleve, Classe, Inscription, StudentLog,
    AnneeScolaire, Mouvement, Ecole, Tarif
)

from django.db.models import Sum, Q
from datetime import timedelta, datetime
import csv
from django.http import HttpResponse

# =======================
# 1. Authentication
# =======================
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


# =======================
# 2. Student Management
# =======================
@login_required
def home(request):
    schools = Ecole.objects.all()
    data = {}
    for school in schools:
        classes = Classe.objects.filter(ecole=school)
        class_data = []
        for classe in classes:
            if Inscription.objects.filter(classe=classe).exists():
                class_data.append(classe)
        if class_data:
            data[school] = class_data
    breadcrumbs = [('/', 'Home')]  # Update breadcrumbs as needed
    return render(request, 'scuelo/home.html', {'data': data, 'breadcrumbs': breadcrumbs})

@login_required
def class_detail(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    students = Eleve.objects.filter(inscription__classe=classe)
    breadcrumbs = [('/', 'Home'), (reverse('home'), 'Classes'), ('#', classe.nom)]
    return render(request, 'scuelo/students/listperclasse.html', {
        'classe': classe,
        'students': students,
        'breadcrumbs': breadcrumbs
    })

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    inscriptions = Inscription.objects.filter(eleve=student).order_by('date_inscription')
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
    logs = StudentLog.objects.filter(student=student).order_by('-timestamp')
    return render(request, 'scuelo/students/studentdetail.html', {
        'student': student,
        'inscriptions': inscriptions,
        'payments': payments,
        'total_payment': total_payment,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'logs': logs,
    })

@login_required
def student_update(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    old_values = student.__dict__.copy()
    if request.method == 'POST':
        form = EleveUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            # Log changes
            new_values = student.__dict__.copy()
            for field, old_value in old_values.items():
                new_value = new_values.get(field)
                if old_value != new_value:
                    StudentLog.objects.create(
                        student=student,
                        user=request.user,
                        action=f"Updated {field}",
                        old_value=str(old_value),
                        new_value=str(new_value)
                    )
            return redirect('student_detail', pk=student.pk)
    else:
        form = EleveUpdateForm(instance=student)
    
    return render(request, 'scuelo/students/studentupdate.html', {'form': form, 'student': student})

@method_decorator(login_required, name='dispatch')
class StudentListView(ListView):
    model = Eleve
    template_name = 'scuelo/student_management.html'
    context_object_name = 'students'

    def get_queryset(self):
        return Eleve.objects.all().order_by(
            'inscription__classe__ecole__nom',
            'inscription__classe__nom',
            'nom',
            'prenom'
        ).select_related('inscription__classe__ecole')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schools = Ecole.objects.prefetch_related(
            Prefetch('classe_set', queryset=Classe.objects.prefetch_related(
                Prefetch('inscription_set', queryset=Inscription.objects.select_related('eleve'))
            ))
        ).all()

        for school in schools:
            for classe in school.classe_set.all():
                for inscription in classe.inscription_set.all():
                    eleve = inscription.eleve
                    eleve.total_paiements = Mouvement.objects.filter(inscription=inscription).aggregate(total=Sum('montant'))['total'] or 0

        context['schools'] = schools
        return context

@login_required
def class_upgrade(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = ClassUpgradeForm(request.POST)
        if form.is_valid():
            new_class = form.cleaned_data['new_class']
            old_class = student.inscription_set.latest('date_inscription').classe.nom

            # Update the latest inscription to the new class
            latest_inscription = student.inscription_set.latest('date_inscription')
            latest_inscription.classe = new_class
            latest_inscription.save()

            # Log the class upgrade
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Upgraded Class",
                old_value=old_class,
                new_value=new_class.nom
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = ClassUpgradeForm()

    return render(request, 'scuelo/classe/class_upgrade.html', {'form': form, 'student': student})

@login_required
def change_school(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = SchoolChangeForm(request.POST)
        if form.is_valid():
            old_school = student.inscription_set.latest('date_inscription').classe.ecole.nom
            new_school = form.cleaned_data['new_school']
            # Assuming Inscription model has 'eleve', 'classe', and 'annee_scolaire' fields
            latest_inscription = student.inscription_set.latest('date_inscription')
            latest_inscription.classe.ecole = new_school
            latest_inscription.save()
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Changed School",
                old_value=old_school,
                new_value=new_school.nom
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = SchoolChangeForm()

    return render(request, 'scuelo/school/change_school.html', {'form': form, 'student': student})

@login_required
def offsite_students(request):
    offsite_students = Eleve.objects.filter(
        ~Q(inscription__classe__ecole__nom__iexact="SIG")
    ).distinct().order_by('nom', 'prenom')

    for student in offsite_students:
        student.total_paiements = Mouvement.objects.filter(inscription__eleve=student).aggregate(total=Sum('montant'))['total'] or 0

    context = {
        'offsite_students': offsite_students
    }
    return render(request, 'scuelo/offsite_students.html', context)

@method_decorator(login_required, name='dispatch')
class StudentCreateView(CreateView):
    model = Eleve
    form_class = EleveCreateForm
    template_name = 'scuelo/students/new_student.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['breadcrumbs'] = [('/', 'Home'), ('/students/create/', 'Ajouter élève')]
        return data

    def form_valid(self, form):
        eleve = form.save(commit=False)
        eleve.save()
        classe = form.cleaned_data['classe']
        annee_scolaire = form.cleaned_data['annee_scolaire']
        Inscription.objects.create(eleve=eleve, classe=classe, annee_scolaire=annee_scolaire)
        return super().form_valid(form)


# =======================
# 3. Class Management
# =======================
@method_decorator(login_required, name='dispatch')
class ClasseCreateView(CreateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_create.html'

    def form_valid(self, form):
        form.instance.ecole_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.kwargs['pk']})

@method_decorator(login_required, name='dispatch')
class ClasseDetailView(DetailView):
    model = Classe
    template_name = 'scuelo/classe/classe_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classe = self.get_object()
        context['students'] = Eleve.objects.filter(inscription__classe=classe)
        context['breadcrumbs'] = [('/', 'Home'), 
                                  (f'/homepage/schools/detail/{classe.ecole.pk}/', 'School Details'), 
                                  ('', 'Class Details')]
        return context

@method_decorator(login_required, name='dispatch')
class ClasseUpdateView(UpdateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_update.html'

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/classe/classe_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.object.ecole.pk})


# =======================
# 4. Payment Management
# =======================
@csrf_exempt
@login_required
def add_payment(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.inscription = Inscription.objects.filter(eleve=student).last()
            paiement.save()

            # Log the payment
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Added Payment",
                old_value="",
                new_value=f"{paiement.causal} - {paiement.montant} - {paiement.note} - {paiement.date_paye}"
            )
            
            # Redirect to the student's detail page after successful payment
            return redirect('student_detail', pk=student.pk)
    else:
        form = PaiementPerStudentForm()

    # Render the form again if it's a GET request or if the form is invalid
    return render(request, 'scuelo/paiements/add_payment.html', {'form': form, 'student': student})

@login_required
def update_paiement(request, pk):
    paiement = get_object_or_404(Mouvement, pk=pk)
    student = paiement.inscription.eleve
    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            # Log the update
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Updated Payment",
                old_value=f"{paiement.causal} - {paiement.montant} - {paiement.note} - {paiement.date_paye}",
                new_value=f"{paiement.causal} - {form.cleaned_data['montant']} - {form.cleaned_data['note']} - {form.cleaned_data['date_paye']}"
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = PaiementPerStudentForm(instance=paiement)

    return render(request, 'scuelo/paiements/updatepaiment.html', {'form': form, 'student': student})

@method_decorator(login_required, name='dispatch')
class UniformPaymentListView(ListView):
    model = Mouvement
    template_name = 'scuelo/uniforms/uniform_payments.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Mouvement.objects.filter(causal='TEN')

@method_decorator(login_required, name='dispatch')
class UniformPaymentCreateView(CreateView):
    model = Mouvement
    form_class = MouvementForm
    template_name = 'payment_form.html'
    success_url = reverse_lazy('uniform_payments')

    def form_valid(self, form):
        form.instance.causal = 'TEN'
        return super().form_valid(form)

from django.shortcuts import render
from django.db.models import Sum, Q
from datetime import timedelta, datetime
import csv
from django.http import HttpResponse

@login_required
def cash_flow_report(request):
    movements = Mouvement.objects.all().order_by('date_paye')
    progressive_total = 0
    data = []

    for movement in movements:
        if movement.type == 'R':
            progressive_total += movement.montant
        else:
            progressive_total -= movement.montant

        data.append({
            'date': movement.date_paye,
            'causal': movement.causal,
            'inflow': movement.montant if movement.type == 'R' else '',
            'outflow': movement.montant if movement.type == 'D' else '',
            'progressive_total': progressive_total
        })

    return render(request, 'scuelo/cash/cash_flow_report.html', {'data': data})

@login_required
def accounting_report(request):
    # Grouping by period (e.g., 1st-15th and 16th-end)
    start_of_period = datetime.now().replace(day=1)  # Start of the month
    mid_of_period = datetime.now().replace(day=16)  # Mid of the month
    
    grouped_income = Mouvement.objects.filter(
        Q(type='R'),
        date_paye__gte=start_of_period
    ).annotate(period=Case(
        When(date_paye__lt=mid_of_period, then=Value('1st-15th')),
        default=Value('16th-end')
    )).values('period').annotate(total=Sum('montant')).order_by('period')

    return render(request, 'scuelo/cash/accounting_report.html', {'grouped_income': grouped_income})

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
def mouvement_list(request):
    search_query = request.GET.get('search', '')
    
    # Fetch all movements
    movements = Mouvement.objects.all().order_by('-date_paye')
    
    # Apply search filters if search_query is provided
    if search_query:
        movements = movements.filter(
            Q(causal__icontains=search_query) | 
            Q(note__icontains=search_query) |
            Q(inscription__eleve__nom__icontains=search_query)
        )
    
    # Update type to 'R' for specific causals
    for mouvement in movements:
        if mouvement.causal in ['INS', 'SCO', 'TEN', 'CAN']:
            mouvement.type = 'R'
        else:
            mouvement.type = 'D'
    
    return render(request, 'scuelo/mouvement/mouvement_list.html', {
        'movements': movements,
        'search_query': search_query
    })

@login_required
def add_mouvement(request):
    if request.method == 'POST':
        form = MouvementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mouvement_list')
    else:
        form = MouvementForm()
    return render(request, 'scuelo/mouvement/add_mouvement.html', {'form': form})
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
    return render(request, 'scuelo/mouvement/update_mouvement.html', {'form': form, 'mouvement': mouvement})

@login_required
def delete_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        return redirect('mouvement_list')
    return render(request, 'scuelo/mouvement/delete_mouvement.html', {'mouvement': mouvement})


@login_required
def delay_list(request):
    data = {}
    schools = Ecole.objects.all()
    for school in schools:
        classes = Classe.objects.filter(ecole=school)
        class_data = {}
        for classe in classes:
            students = Eleve.objects.filter(inscription__classe=classe, cs_py='PY')
            student_data = []
            for student in students:
                sco_paid = Mouvement.objects.filter(inscription__eleve=student, causal__in=['INS', 'SCO1', 'SCO2', 'SCO3']).aggregate(total=Sum('montant'))['total'] or 0
                sco_exigible = Tarif.objects.filter(classe=classe, causal__in=['INS', 'SCO1', 'SCO2', 'SCO3']).aggregate(total=Sum('montant'))['total'] or 0
                can_paid = Mouvement.objects.filter(inscription__eleve=student, causal='CAN').aggregate(total=Sum('montant'))['total'] or 0
                can_exigible = Tarif.objects.filter(classe=classe, causal='CAN').aggregate(total=Sum('montant'))['total'] or 0

                diff_sco = sco_paid - sco_exigible
                diff_can = can_paid - can_exigible
                retards = diff_sco + diff_can

                if retards != 0:  # Only include students with a balance
                    percentage_paid = int(100 * (sco_paid + can_paid) / (sco_exigible + can_exigible)) if (sco_exigible + can_exigible) > 0 else 0

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
                        'note': student.note_eleve,
                    })
            if student_data:  # Only add classes with students who have late payments
                class_data[classe.nom] = student_data
        if class_data:  # Only add schools with classes that have students with late payments
            data[school.nom] = class_data
    return render(request, 'scuelo/paiements/late_payments_report.html', {'data': data})


# =======================
# 5. School Management
# =======================
@method_decorator(login_required, name='dispatch')
class SchoolManagementView(TemplateView):
    template_name = 'scuelo/school/school_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schools'] = Ecole.objects.annotate(num_students=Count('classe__inscription__eleve', distinct=True))
        context['form'] = EcoleCreateForm()
        return context

@method_decorator(login_required, name='dispatch')
class SchoolCreateView(CreateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school_create.html'
    success_url = reverse_lazy('student_management')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"message": "Success"})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(form.errors, status=400)
        return response

@method_decorator(login_required, name='dispatch')
class SchoolUpdateView(UpdateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school/school_update.html'
    success_url = reverse_lazy('student_management')

@method_decorator(login_required, name='dispatch')
class SchoolDeleteView(DeleteView):
    model = Ecole
    template_name = 'scuelo/school/school_confirm_delete.html'
    success_url = reverse_lazy('student_management')

@method_decorator(login_required, name='dispatch')
class SchoolDetailView(DetailView):
    model = Ecole
    template_name = 'scuelo/school/school_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Eleve.objects.filter(inscription__classe__ecole=self.object).distinct()
        context['classe_form'] = ClasseCreateForm()
        return context

@login_required
def load_classes(request):
    school_id = request.GET.get('school_id')
    classes = Classe.objects.filter(ecole_id=school_id).order_by('nom')
    return JsonResponse(list(classes.values('id', 'nom')), safe=False)


# =======================
# 6. Financial Management
# =======================
@method_decorator(login_required, name='dispatch')
class TarifListView(ListView):
    model = Tarif
    template_name = 'scuelo/tarif/tarif_list.html'
    context_object_name = 'tarifs'

    def get_queryset(self):
        return Tarif.objects.all().order_by('classe__ecole__nom', 'classe__nom', 'annee_scolaire__nom', 'causal')

@method_decorator(login_required, name='dispatch')
class TarifCreateView(CreateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'scuelo/tarif/tarif_form.html'
    success_url = reverse_lazy('tarif_list')

@method_decorator(login_required, name='dispatch')
class TarifUpdateView(UpdateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'scuelo/tarif/tarif_form.html'
    success_url = reverse_lazy('tarif_list')

@method_decorator(login_required, name='dispatch')
class TarifDeleteView(DeleteView):
    model = Tarif
    template_name = 'scuelo/tarif/tarif_confirm_delete.html'
    success_url = reverse_lazy('tarif_list')


# =======================
# 7. Others (Not Completed)
# =======================
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

def recording_on_records(request):
    # Your logic for recording_on_records
    return render(request, 'scuelo/recording_on_records.html')

def working_sessions(request):
    # Your logic for working_sessions
    return render(request, 'scuelo/working_sessions.html')

def school_uniforms(request):
    # Your logic for school_uniforms
    return render(request, 'scuelo/school/school_uniforms.html')

def print_receipts(request):
    # Your logic for print_receipts
    return render(request, 'scuelo/print_receipts.html')

def generic_reports(request):
    # Your logic for generic_reports
    return render(request, 'scuelo/generic_reports.html')

def export_for_accounting(request):
    # Your logic for export_for_accounting
    return render(request, 'scuelo/export_for_accounting.html')

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

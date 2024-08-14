from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse , HttpResponseRedirect 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import UpdateView
from django.views.generic import (DetailView, ListView,
                                  ListView, CreateView, UpdateView ,TemplateView , DeleteView
                                  )
from django.db.models import Q, Max, Sum, Prefetch , Count, Case, When, IntegerField


from .forms import  ( PaiementPerStudentForm ,  EleveUpdateForm , MouvementForm ,
                     EleveCreateForm , EcoleCreateForm , ClasseCreateForm ,
                    TarifForm  ,   ClassUpgradeForm, SchoolChangeForm )
from .filters import EleveFilter
from scuelo.models import ( Eleve, Classe, Inscription,StudentLog, 
                           AnneeScolaire ,  Mouvement , Ecole , Tarif
)

'''
this is the home view ,it main functionality
is to list the classes in a single page and enable each to get in a inspect
'''
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

'''
this one concern the detail of each classe it list the students of that 
classe and some important stats about that particular classe
'''
@login_required
def class_detail(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    students = Eleve.objects.filter(inscription__classe=classe)
    breadcrumbs = [('/', 'Home'), 
                   (reverse('home'), 'Classes'),
                   ('#', classe.nom)
    ]
    return render(
        request, 'scuelo/students/listperclasse.html',
                  {
                    'classe': classe,
                    'students': students,
                    'breadcrumbs': breadcrumbs
    })
'''
once in the classe this one enable you to get more detailed informations
about each students, this details are important because there are :
  - the list of the paiment made for this student and update btn even
  -the basic informations of that student (the name firstname and so)
  -the list of inscriptions and even btn for updates
  - in this view we are able to add some payments for that student
  - we can be able to see also the total payments of that student
  and also update the basic informations of that student
'''
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



'''
this view is for adding payments (it concerns the students)
in the payment addition process we can add some paiment concerning some
registered inscriptions
'''
@method_decorator(csrf_exempt, name='dispatch')
def add_paiement(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    form = PaiementPerStudentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.inscription = Inscription.objects.filter(eleve=student).last()
            old_value = f"{paiement.causal} - {paiement.montant} - {paiement.note}"
            paiement.save()
            new_value = f"{paiement.causal} - {paiement.montant} - {paiement.note}"
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Added Payment",
                old_value=old_value,
                new_value=new_value
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

'''
for updating payments
'''
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

    return render(
        request, 'scuelo/paiements/updatepaiment.html', 
        {'form': form, 'paiement': paiement}
    )

'''students update'''
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
    
    return render(request, 'scuelo/students/studentupdate.html',
                  {'form': form, 'student': student}
    )

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

class ClasseUpdateView(UpdateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_update.html'

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/classe/classe_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.object.ecole.pk})
    
class TarifListView(ListView):
    model = Tarif
    template_name = 'scuelo/tarif/tarif_list.html'
    context_object_name = 'tarifs'

class TarifCreateView(CreateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'scuelo/tarif/tarif_form.html'
    success_url = reverse_lazy('tarif_list')

class TarifUpdateView(UpdateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'scuelo/tarif/tarif_form.html'
    success_url = reverse_lazy('tarif_list')


@login_required
def delay_list(request):
    data = {}
    schools = Ecole.objects.all()
    for school in schools:
        classes = Classe.objects.filter(ecole=school)
        class_data = {}
        for classe in classes:
            students = Eleve.objects.filter(inscription__classe=classe)
            student_data = []
            for student in students:
                sco_total = 0
                sco_exigible_total = 0
                can_total = 0
                can_exigible_total = 0

                inscriptions = Inscription.objects.filter(eleve=student, classe=classe)
                for inscription in inscriptions:
                    tariffs = Tarif.objects.filter(classe=classe, annee_scolaire=inscription.annee_scolaire)
                    for tarif in tariffs:
                        if tarif.causal == 'SCO1' or tarif.causal == 'SCO2' or tarif.causal == 'SCO3':
                            sco_total += tarif.montant
                            sco_exigible_total += tarif.montant  # This should be calculated based on due date and payments made
                        elif tarif.causal == 'CAN':
                            can_total += tarif.montant
                            can_exigible_total += tarif.montant  # This should be calculated based on due date and payments made

                diff_sco = sco_total - sco_exigible_total
                diff_can = can_total - can_exigible_total
                retards = diff_sco + diff_can

                if retards > 0:  # Only include students with late payments
                    student_data.append({
                        'id': student.pk,
                        'nom': student.nom,
                        'prenom': student.prenom,
                        'sex': student.sex,
                        'cs_py': student.cs_py,
                        'sco': sco_total,
                        'sco_exigible': sco_exigible_total,
                        'diff_sco': diff_sco,
                        'can': can_total,
                        'can_exigible': can_exigible_total,
                        'diff_can': diff_can,
                        'retards': retards,
                        'note': student.note_eleve
                    })
            if student_data:  # Only add classes with students who have late payments
                class_data[classe.nom] = student_data
        if class_data:  # Only add schools with classes that have students with late payments
            data[school.nom] = class_data
    return render(request, 'scuelo/tarif/delay_list.html', {'data': data})

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
    

# List all inflows and outflows
@method_decorator(login_required, name='dispatch')
class InflowOutflowListView(ListView):
    model = Mouvement
    template_name = 'scuelo/inoutflows/inflow_outflow_list.html'
    context_object_name = 'mouvements'

    def get_queryset(self):
        return Mouvement.objects.all()

# Create a new inflow or outflow
@method_decorator(login_required, name='dispatch')
class InflowOutflowCreateView(CreateView):
    model = Mouvement
    form_class = MouvementForm
    template_name = 'scuelo/inoutflows/inflow_outflow_form.html'
    success_url = reverse_lazy('inflow_outflow_list')

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

# Update an existing inflow or outflow
@method_decorator(login_required, name='dispatch')
class InflowOutflowUpdateView(UpdateView):
    model = Mouvement
    form_class = MouvementForm
    template_name = 'scuelo/inoutflows/inflow_outflow_form.html'
    success_url = reverse_lazy('inflow_outflow_list')

# Delete an existing inflow or outflow
@method_decorator(login_required, name='dispatch')
class InflowOutflowDeleteView(DeleteView):
    model = Mouvement
    template_name = 'scuelo/inoutflows/inflow_outflow_confirm_delete.html'
    success_url = reverse_lazy('inflow_outflow_list')

# Generate report for inflows and outflows
@login_required
def inflow_outflow_report(request):
    inflows = Mouvement.objects.filter(type='inflow').aggregate(total=Sum('montant'))['total'] or 0
    outflows = Mouvement.objects.filter(type='outflow').aggregate(total=Sum('montant'))['total'] or 0
    context = {
        'inflows': inflows,
        'outflows': outflows,
    }
    return render(request, 'scuelo/inflow_outflow_report.html', context)

@login_required
def cash_flow_report(request):
    mouvements = Mouvement.objects.all().order_by('date_paye')
    
    # Calculate the progressive balance
    balance = 0
    for mouvement in mouvements:
        if mouvement.type == "R":
            balance += mouvement.montant
        else:
            balance -= mouvement.montant
        mouvement.progressif = balance
    
    return render(request, 'scuelo/cash/flow_report.html', {'mouvements': mouvements})

@login_required
def cash_accounting_export(request):
    # Your logic for exporting cash accounting data
    return render(request, 'scuelo/cash/accounting_export.html')
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


@login_required
def cash_movements(request):
    movements = Mouvement.objects.filter(destination='A').order_by('date_paye')
    progressive_total = 0
    data = []

    for movement in movements:
        if movement.type == 'R':
            progressive_total += movement.montant
            inflow = movement.montant
            outflow = ''
        else:
            progressive_total -= movement.montant
            inflow = ''
            outflow = movement.montant

        inscription = movement.inscription
        if inscription:
            student = inscription.eleve
            classe = inscription.classe
            school = classe.ecole
        else:
            student = None
            classe = None
            school = None

        data.append({
            'id': movement.id,
            'date': movement.date_paye,
            'description': movement.causal,
            'inflow': inflow,
            'outflow': outflow,
            'progressive_total': progressive_total,
            'student': student,
            'classe': classe,
            'school': school,
        })

    return render(request, 'scuelo/cash/cash_movements.html', {'data': data})



@login_required
def add_mouvement(request):
    if request.method == 'POST':
        form = MouvementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cash_movements')
    else:
        form = MouvementForm()
    return render(request, 'scuelo/cash/add_mouvement.html', {'form': form})

@login_required
def update_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        form = MouvementForm(request.POST, instance=mouvement)
        if form.is_valid():
            form.save()
            return redirect('cash_movements')
    else:
        form = MouvementForm(instance=mouvement)
    return render(request, 'scuelo/cash/update_mouvement.html', {'form': form, 'mouvement': mouvement})

@login_required
def delete_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        return redirect('cash_movements')
    return render(request, 'scuelo/cash/delete_mouvement.html', {'mouvement': mouvement})



@method_decorator(csrf_exempt, name='dispatch')
def add_paiement(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    form = PaiementPerStudentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.inscription = Inscription.objects.filter(eleve=student).last()
            tarif = Tarif.objects.get(classe=paiement.inscription.classe, causal=paiement.causal)
            paiement.montant = tarif.montant
            old_value = f"{paiement.causal} - {paiement.montant} - {paiement.note}"
            paiement.save()
            new_value = f"{paiement.causal} - {paiement.montant} - {paiement.note}"
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Added Payment",
                old_value=old_value,
                new_value=new_value
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def cash_flow_report(request):
    mouvements = Mouvement.objects.all().order_by('date_paye')

    # Calculate the progressive balance
    balance = 0
    for mouvement in mouvements:
        if mouvement.type == "R":
            balance += mouvement.montant
        else:
            balance -= mouvement.montant
        mouvement.progressif = balance

    return render(request, 'scuelo/cash/flow_report.html', {'mouvements': mouvements})

@login_required
def cash_accounting_export(request):
    # Your logic for exporting cash accounting data
    return render(request, 'scuelo/cash/accounting_export.html')


from django.http import JsonResponse

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
def load_classes(request):
    school_id = request.GET.get('school_id')
    classes = Classe.objects.filter(ecole_id=school_id).order_by('nom')
    return JsonResponse(list(classes.values('id', 'nom')), safe=False)


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
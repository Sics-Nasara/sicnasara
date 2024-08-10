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
from django.views.generic import (DetailView, ListView,
                                  ListView, CreateView, UpdateView ,TemplateView , DeleteView
                                  )
from django.db.models import Q, Max, Sum, Prefetch , Count, Case, When, IntegerField

from .forms import  ( PaiementPerStudentForm ,  EleveUpdateForm , 
                     EleveCreateForm , EcoleCreateForm , ClasseCreateForm 
                      )
from .filters import EleveFilter
from scuelo.models import Eleve, Classe, Inscription, AnneeScolaire ,  Mouvement , Ecole

'''
this is the home view ,it main functionality
is to list the classes in a single page and enable each to get in a inspect
'''
@login_required
def home(request):
    classes = Classe.objects.all()
    return render(request, 'scuelo/home.html', {'classes': classes})


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
            paiement.save()
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
    if request.method == 'POST':
        form = EleveUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
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
    form_class = EleveUpdateForm
    template_name = 'scuelo/students/new_student.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['breadcrumbs'] = [('/', 'Home'), ('/students/create/', 'Ajouter élève')]
        return data





@method_decorator(login_required, name='dispatch')
class SchoolManagementView(TemplateView):
    template_name = 'scuelo/school_management.html'

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
    template_name = 'scuelo/school_update.html'
    success_url = reverse_lazy('student_management')

@method_decorator(login_required, name='dispatch')
class SchoolDeleteView(DeleteView):
    model = Ecole
    template_name = 'scuelo/school_confirm_delete.html'
    success_url = reverse_lazy('student_management')

@method_decorator(login_required, name='dispatch')
class SchoolDetailView(DetailView):
    model = Ecole
    template_name = 'scuelo/school_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Eleve.objects.filter(inscription__classe__ecole=self.object).distinct()
        context['classe_form'] = ClasseCreateForm()
        return context

@method_decorator(login_required, name='dispatch')
class ClasseCreateView(CreateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/students/classe_create.html'

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
    template_name = 'scuelo/students/classe_update.html'

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/students/classe_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.object.ecole.pk})
    
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
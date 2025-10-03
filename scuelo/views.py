# Authentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

# Shortcuts & utilities
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Generic views
from django.views.generic import (
    DetailView, ListView, CreateView, TemplateView
)
from django.views.generic.edit import UpdateView, DeleteView

# Django ORM tools
from django.db import models
from django.db.models import (
    Q, Sum, Prefetch, Count, F, Case, When, Value, IntegerField
)
from django.db.models.functions import TruncDay

# Forms
from .forms import (
    EleveUpdateForm, EleveCreateForm, EcoleCreateForm, ClasseCreateForm,
    StudentRangForm, ClassUpgradeForm, SchoolChangeForm, UniformReservationForm
)
from cash.forms import PaiementPerStudentForm

# Models
from scuelo.models import (
    Eleve, Classe, Inscription, StudentLog,
    AnneeScolaire, Ecole, UniformReservation, Rang ,TypeClasse
)
from cash.models import Mouvement, Tarif

# Python & third-party libs
from datetime import timedelta, datetime
import csv
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns


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
class SchoolYearManagementView(ListView):
    model = AnneeScolaire
    template_name = 'scuelo/annee_scolaire_manage.html'
    context_object_name = 'school_years'

    # Additional context if needed, e.g., for adding, updating, or deleting years
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add extra context if necessary
        return context
    
class AddSchoolYearView(CreateView):
    model = AnneeScolaire
    fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
    template_name = 'scuelo/add_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')

class EditSchoolYearView(UpdateView):
    model = AnneeScolaire
    fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
    template_name = 'scuelo/edit_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')


class DeleteSchoolYearView(DeleteView):
    model = AnneeScolaire
    template_name = 'scuelo/delete_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')    

@login_required
def select_school_year(request):
    if request.method == 'POST':
        # Get the selected school year from the form
        school_year_id = request.POST.get('school_year')
        if school_year_id:
            # Save the selected school year ID in the session
            request.session['selected_school_year'] = school_year_id
        return redirect('home')  # Redirect to home page after setting the year

    # Fetch all available school years for the dropdown
    all_years = AnneeScolaire.objects.all()
    # Retrieve the currently selected school year from the session if it exists
    current_year_id = request.session.get('selected_school_year')

    return render(request, 'scuelo/select_school_year.html', {
        'all_years': all_years,
        'current_year_id': current_year_id,
    })
from django.db import transaction

@login_required
def home(request):
    # Ordre désiré des écoles
    school_order = [
        "École Maternelle Centre social de Nasara",
        "École primaire Centre social de Nasara",
        "École Secondaire Centre social de Nasara"
    ]
    order_school_map = {name: i for i, name in enumerate(school_order)}

    # Ordre désiré des classes
    class_order = ['PS', 'MS', 'GS', 'CP1', 'CP2', 'CE1', 'CE2', 'CM1', 'CM2', '6me']
    order_class_map = {name: i for i, name in enumerate(class_order)}

    schools = Ecole.objects.filter(externe=False)

    # Tri des écoles selon la liste order_school_map, non listées à la fin
    schools = sorted(schools, key=lambda e: order_school_map.get(e.nom, len(school_order)))

    data = {}

    icon_mapping = {
        "MATERNELLE": "child",
        "PRIMAIRE": "school",
        "SECONDAIRE": "user-graduate",
        "LYCEE": "chalkboard-teacher"
    }

    for school in schools:
        classes = list(Classe.objects.filter(ecole=school))

        # Trier les classes selon order_class_map, non listées à la fin
        classes.sort(key=lambda c: order_class_map.get(c.nom, len(class_order)))

        classes_with_icon = [{
            'classe': c,
            'icon': icon_mapping.get(c.type.type_ecole, "school")
        } for c in classes]

        data[school] = classes_with_icon

    all_years = AnneeScolaire.objects.all()
    current_year = AnneeScolaire.objects.filter(actuel=True).first()
    breadcrumbs = [('/', 'Home')]

    return render(request, 'scuelo/home.html', {
        'data': data,
        'breadcrumbs': breadcrumbs,
        'all_years': all_years,
        'current_year': current_year,
        'page_identifier': 'S01',
    })


from django.db import transaction

@login_required
def class_detail(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    all_annee_scolaires = AnneeScolaire.objects.all()
    selected_annee_scolaire_id = request.GET.get('annee_scolaire')

    if selected_annee_scolaire_id:
        try:
            selected_annee_scolaire = AnneeScolaire.objects.get(pk=selected_annee_scolaire_id)
        except AnneeScolaire.DoesNotExist:
            selected_annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()
    else:
        selected_annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()

    # Update 'actuel' flag atomically
    with transaction.atomic():
        if selected_annee_scolaire and not selected_annee_scolaire.actuel:
            AnneeScolaire.objects.filter(actuel=True).update(actuel=False)
            selected_annee_scolaire.actuel = True
            selected_annee_scolaire.save()

    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)
    students = [inscription.eleve for inscription in inscriptions if inscription.eleve.condition_eleve != 'ABAN']

    for student in students:
        payments = Mouvement.objects.filter(inscription__eleve=student, inscription__classe=classe, inscription__annee_scolaire=selected_annee_scolaire)
        student.total_payment = payments.aggregate(total=Sum('montant'))['total'] or 0
        student.payment_details = payments.values('causal', 'montant', 'date_paye')
        student.tenues = payments.filter(causal='TEN').values('montant')
        student.notes = student.note_eleve

    total_class_payment = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=selected_annee_scolaire
    ).aggregate(total=Sum('montant'))['total'] or 0

    tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)

    cs_count = sum(1 for student in students if student.get_cs_py_display() == 'CS')
    py_count = sum(1 for student in students if student.get_cs_py_display() == 'PY')
    aut_count = len(students) - cs_count - py_count

    breadcrumbs = [('/', 'Home'), (reverse('home'), 'Classes'), ('#', classe.nom)]
    total_students = len(students)
    student_count_display = f"{total_students}({cs_count}-{py_count}-{aut_count})"

    return render(request, 'scuelo/students/listperclasse.html', {
        'classe': classe,
        'students': students,
        'tarifs': tarifs,
        'breadcrumbs': breadcrumbs,
        'total_class_payment': total_class_payment,
        'student_count_display': student_count_display,
        'all_annee_scolaires': all_annee_scolaires,
        'selected_annee_scolaire': selected_annee_scolaire,
        'page_identifier': 'S02'
    })


class ClasseInformation(LoginRequiredMixin, DetailView):
    model = Classe
    template_name = "scuelo/classe/classe_information.html"
    context_object_name = "classe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        selected_annee_scolaire_id = self.request.GET.get('annee_scolaire')
        if selected_annee_scolaire_id:
            selected_annee_scolaire = get_object_or_404(AnneeScolaire, pk=selected_annee_scolaire_id)
        else:
            selected_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        classe = self.get_object()

        inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)

        # Sélection des élèves PY non abandonnés
        students = Eleve.objects.filter(
            inscriptions__in=inscriptions,
            cs_py='P'
        ).exclude(condition_eleve='ABAN').distinct()

        total_paid_py = 0
        py_students = []

        for student in students:
            payments = Mouvement.objects.filter(
                inscription__eleve=student,
                inscription__classe=classe,
                inscription__annee_scolaire=selected_annee_scolaire
            )
            student.total_payment = payments.aggregate(total=Sum('montant'))['total'] or 0
            py_students.append(student)
            total_paid_py += student.total_payment

        py_count = len(py_students)

        # Calcul 1ère tranche = nb élèves PY * tarif SCO1
        tarif_sco1 = Tarif.objects.filter(
            classe=classe,
            causal='SCO1',
            annee_scolaire=selected_annee_scolaire
        ).aggregate(total=Sum('montant'))['total'] or 0

        expected_first_tranche = tarif_sco1 * py_count

        total_payment_percentage = round((total_paid_py / expected_first_tranche * 100), 2) if expected_first_tranche else 0

        context.update({
            'students': students,
            'tarifs': Tarif.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire),
            'selected_annee_scolaire': selected_annee_scolaire,
            'py_count': py_count,
            'total_paid_py': total_paid_py,
            'expected_first_tranche': expected_first_tranche,
            'total_payment_percentage': total_payment_percentage,
            'breadcrumbs': [('/', 'Home'), ('#', classe.nom)],
        })

        return context

from django.shortcuts import render, get_object_or_404, redirect, reverse

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Eleve, pk=pk)

    current_year = AnneeScolaire.objects.filter(actuel=True).first()
    selected_annee_id = request.GET.get('annee_scolaire') or (current_year.id if current_year else None)

    if selected_annee_id:
        payments = Mouvement.objects.filter(
            inscription__eleve=student,
            inscription__annee_scolaire_id=selected_annee_id
        )
    else:
        payments = Mouvement.objects.filter(inscription__eleve=student)

    total_payment = payments.aggregate(Sum('montant'))['montant__sum'] or 0

    inscriptions = Inscription.objects.filter(eleve=student).order_by('date_inscription')

    current_class = student.current_class
    current_school_name = current_class.ecole.nom if current_class else "No School Assigned"
    current_class_name = current_class.type if current_class else "No Class Assigned"

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
    rang_form = StudentRangForm()
    logs = StudentLog.objects.filter(student=student).order_by('-timestamp')

    existing_rang = None
    if current_class and current_year:
        existing_rang = Rang.objects.filter(
            eleve=student,
            classe=current_class,
            annee_scolaire=current_year
        ).first()
        if existing_rang:
            rang_form = StudentRangForm(instance=existing_rang)

    annee_scolaires = AnneeScolaire.objects.all().order_by('-date_initiale')

    return render(request, 'scuelo/students/studentdetail.html', {
        'student': student,
        'inscriptions': inscriptions,
        'payments': payments,
        'total_payment': total_payment,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'rang_form': rang_form,
        'existing_rang': existing_rang,
        'logs': logs,
        'current_school_name': current_school_name,
        'current_class_name': current_class_name,
        'page_identifier': 'S03',
        'annee_scolaires': annee_scolaires,
        'selected_annee_id': int(selected_annee_id) if selected_annee_id else None,
        'active_school_year': current_year,  # Pass for top bar display
    })


@login_required
def add_student_rang(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    current_year = AnneeScolaire.objects.filter(actuel=True).first()
    current_inscription = Inscription.objects.filter(eleve=student, annee_scolaire=current_year).first()
    current_class = current_inscription.classe if current_inscription else None
    existing_rang = None
    if current_class and current_year:
        existing_rang = Rang.objects.filter(
            eleve=student,
            classe=current_class,
            annee_scolaire=current_year
        ).first()

    if request.method == 'POST':
        rang_form = StudentRangForm(request.POST, instance=existing_rang)
        if rang_form.is_valid():
            rang = rang_form.save(commit=False)
            rang.eleve = student
            rang.classe = current_class
            rang.annee_scolaire = current_year
            rang.save()
            return JsonResponse({'success': True})  # Return success for AJAX
        else:
            return JsonResponse({'success': False, 'errors': rang_form.errors})  # Return errors for AJAX
    else:
        if existing_rang:
            rang_form = StudentRangForm(instance=existing_rang)
        else:
            rang_form = StudentRangForm()

    return render(request, 'scuelo/students/add_student_rang_modal.html', {
        'rang_form': rang_form,
        'student': student,
        'existing_rang': existing_rang,
    })


from django.views.generic import ListView
from django.db.models import Prefetch, Sum
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse

@method_decorator(login_required, name='dispatch')
class StudentListView(ListView):
    model = Ecole  # On liste par écoles et classes
    template_name = 'scuelo/student_management.html'
    context_object_name = 'schools'

    def get_queryset(self):
        current_year = AnneeScolaire.objects.filter(actuel=True).first()
        if not current_year:
            return Ecole.objects.none()

        # Charge écoles avec classes qui ont inscriptions dans l'année scolaire courante
        return Ecole.objects.prefetch_related(
            Prefetch(
                'classe_set',
                queryset=Classe.objects.prefetch_related(
                    Prefetch(
                        'inscription_set',
                        queryset=Inscription.objects.filter(annee_scolaire=current_year).select_related('eleve')
                    )
                ).filter(inscription__annee_scolaire=current_year).distinct()
            )
        ).order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_year = AnneeScolaire.objects.filter(actuel=True).first()
        if not current_year:
            return HttpResponse("Aucune année scolaire actuelle trouvée.", status=400)
        
        context['annee_scolaire'] = current_year
        context['page_identifier'] = 'S14'
        return context


@login_required
def class_upgrade(request, pk):
    student = get_object_or_404(Eleve, pk=pk)

    # Récupération des écoles et classes (avec écoles rattachées)
    schools = Ecole.objects.all()
    classes = Classe.objects.select_related('ecole').all()

    # Récupération classe et école actuelles
    current_inscription = Inscription.objects.filter(eleve=student, annee_scolaire__actuel=True).first()
    current_class = current_inscription.classe if current_inscription else None
    current_school = current_class.ecole if current_class else None

    if request.method == 'POST':
        new_class_id = request.POST.get('new_class')
        if not new_class_id:
            messages.error(request, "Veuillez sélectionner une nouvelle classe.")
        else:
            new_class = Classe.objects.get(pk=new_class_id)

            current_year = current_inscription.annee_scolaire if current_inscription else None
            if current_year:
                # Supprimer mm l'inscription existante
                Inscription.objects.filter(eleve=student, annee_scolaire=current_year).delete()

                # Créer nouvelle inscription
                Inscription.objects.create(
                    eleve=student,
                    classe=new_class,
                    annee_scolaire=current_year
                )

                messages.success(request, f"Classe et école mises à jour avec succès pour {student.nom} {student.prenom}.")
                return redirect('student_detail', pk=student.pk)
            else:
                messages.error(request, "Année scolaire actuelle non définie. Veuillez contacter l'administrateur.")
    
    context = {
        'student': student,
        'schools': schools,
        'classes': classes,
        'current_class': current_class,
        'current_school': current_school,
        'page_identifier': 'S04',
    }
    return render(request, 'scuelo/classe/class_upgrade.html', context)
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

    return render(request, 'scuelo/school/change_school.html',
                  {'form': form, 'student': student ,
                    'page_identifier': 'S05' })




@login_required
def offsite_students(request):
    """
    View to display students associated with schools where `externe` is True,
    avoiding duplicate student entries.
    """

    # 1. Fetch all relevant student IDs using a single, combined query
    offsite_student_ids = Inscription.objects.filter(
        classe__ecole__externe=True,
        classe__isnull=False,
        classe__ecole__isnull=False
    ).values_list('eleve_id', flat=True)

    # Also include students where `annee_inscr` is Null
    offsite_student_ids_null_annee = Eleve.objects.filter(
        inscriptions__classe__ecole__externe=True,
        inscriptions__classe__isnull=False,
        inscriptions__classe__ecole__isnull=False,
        annee_inscr__isnull=True
    ).distinct().values_list('id', flat=True)

    all_offsite_student_ids = set(list(offsite_student_ids) + list(offsite_student_ids_null_annee))

    # 2. Fetch all unique offsite students in a single query
    offsite_students = Eleve.objects.filter(id__in=all_offsite_student_ids).prefetch_related(
        'inscriptions__classe__ecole'
    )

    # 3. Prepare the data for the template
    student_data_list = []
    for student in offsite_students:
        # Get the latest inscription to fetch school name
        latest_inscription = student.inscriptions.filter(
            classe__ecole__externe=True,
            classe__isnull=False,
            classe__ecole__isnull=False
        ).order_by('-date_inscription').first()

        school_name = latest_inscription.classe.ecole.nom if latest_inscription else "No School Assigned"
        classe_name = latest_inscription.classe.nom if latest_inscription else "No School Assigned"

        student_data = {
            'id': student.id,
            'nom': student.nom,
            'prenom': student.prenom,
            'condition_eleve': student.get_condition_eleve_display(),
            'sex': student.get_sex_display(),  # Correctly use get_sex_display()
            'date_naissance': student.date_naissance,
            'cs_py': student.get_cs_py_display(),  # Correctly use get_cs_py_display()
            'school_name': school_name,
            'classe_name': classe_name,
            'hand': student.get_hand_display(),
            'note_eleve': student.note_eleve,
        }
        student_data_list.append(student_data)

    # 4. Prepare the context
    context = {
        'all_offsite_students': student_data_list,
        'page_identifier': 'S06',
        'total': len(student_data_list),
    }

    return render(request, 'scuelo/offsite_students.html', context)


        
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class StudentCreateView(CreateView):
    model = Eleve
    form_class = EleveCreateForm
    template_name = 'scuelo/students/new_student.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['breadcrumbs'] = [('/', 'Home'), ('/students/create/', 'Ajouter élève')]
        data['page_identifier'] = 'S15'
        data['ecoles'] = Ecole.objects.all()
        return data

    def form_valid(self, form):
        # Save Eleve instance first
        eleve = form.save(commit=False)
        eleve.save()

        # Create Inscription tying eleve to classe and annee_scolaire
        classe = form.cleaned_data['classe']
        annee_scolaire = form.cleaned_data['annee_scolaire']
        Inscription.objects.create(eleve=eleve, classe=classe, annee_scolaire=annee_scolaire)

        # Call super to proceed with redirect etc
        return super().form_valid(form)

def get_classes_by_school(request):
    ecole_id = request.GET.get('ecole')
    classes = Classe.objects.filter(ecole_id=ecole_id).order_by('nom')
    return render(request, 'scuelo/classe_dropdown_list_options.html', {'classes': classes})

class StudentUpdateView(UpdateView):
    model = Eleve
    form_class = EleveUpdateForm
    template_name = 'scuelo/students/studentupdate.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Manually set initial values for dates
        if self.object.date_naissance:
            form.initial['date_naissance'] = self.object.date_naissance.strftime('%Y-%m-%d')
        if self.object.date_enquete:
            form.initial['date_enquete'] = self.object.date_enquete.strftime('%Y-%m-%d')
        return form
    
    def get_success_url(self):
        return reverse_lazy('student_detail', kwargs={'pk': self.object.pk})
# =======================
# 3. Class Management
# =======================


@method_decorator(login_required, name='dispatch')
class ClasseDetailView(DetailView):
    model = Classe
    template_name = 'scuelo/classe/classe_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classe = self.get_object()

        # Get the current academic year
        current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        # Class Information
        context['classe'] = classe
        context['school_name'] = classe.ecole.nom
        context['teacher'] = None  # Placeholder for when teachers are assigned
        context['notes'] = "Add any specific notes about the class here."  # Placeholder for notes

        # Tariffs for the class and current academic year
        latest_tariffs = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire).order_by('date_expiration')
        
        # Calculate expected total for each tariff based on PY and CONF students
        py_conf_students_count = Inscription.objects.filter(
            classe=classe,
            annee_scolaire=current_annee_scolaire,
            eleve__cs_py="P",  # Only PY students
            eleve__condition_eleve="CONF"  # Only CONF students
        ).count()

        for tarif in latest_tariffs:
            tarif.expected_total = (tarif.montant * py_conf_students_count) if py_conf_students_count else 0

        context['latest_tariffs'] = latest_tariffs

        # Uniforms (Tenues)
        tenues = Mouvement.objects.filter(inscription__classe=classe, causal='TEN', inscription__annee_scolaire=current_annee_scolaire).aggregate(total=Sum('montant'))['total'] or 0
        context['tenues'] = tenues

        # Total payments for the class
        total_class_payment = Mouvement.objects.filter(inscription__classe=classe, inscription__annee_scolaire=current_annee_scolaire).aggregate(total=Sum('montant'))['total'] or 0
        context['total_class_payment'] = total_class_payment

        # Add Breadcrumbs
        context['breadcrumbs'] = [
            ('/', 'Home'),
            (f'/homepage/schools/detail/{classe.ecole.pk}/', 'School Details'),
            ('', 'Class Details')
        ]

        return context


@method_decorator(login_required, name='dispatch')
class ClasseUpdateView(UpdateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the page identifier for this view
        context['page_identifier'] = 'S18'  # Example page identifier
        return context

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/classe/classe_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the page identifier for this view
        context['page_identifier'] = 'S19'  # Example page identifier
        return context

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.object.ecole.pk})

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
        context['page_identifier'] = 'S25'  # Add page identifier
        return context

class SchoolCreateView(CreateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school/school_create.html'  # Use the new template
    success_url = reverse_lazy('school_management')  # Redirect to school management page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S26'  # Add page identifier
        return context
@method_decorator(login_required, name='dispatch')
class SchoolUpdateView(UpdateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school/school_update.html'
    success_url = reverse_lazy('school_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S27'  # Add page identifier
        return context


@method_decorator(login_required, name='dispatch')
class SchoolDeleteView(DeleteView):
    model = Ecole
    template_name = 'scuelo/school/school_confirm_delete.html'
    success_url = reverse_lazy('school_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S28'  # Add page identifier
        return context

    def delete(self, request, *args, **kwargs):
        # Optional: Add any pre-deletion logic here
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class SchoolDetailView(DetailView):
    model = Ecole
    template_name = 'scuelo/school/school_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.get_object()

        # Get the current academic year
        current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        # Fetch students associated with this school for the current academic year
        students = Eleve.objects.filter(
            inscriptions__classe__ecole=school,
            inscriptions__annee_scolaire=current_annee_scolaire
        ).distinct()

        # Calculate CS, PY, and AUT counts for the entire school
        cs_count = sum(1 for student in students if student.cs_py == 'CS')
        py_count = sum(1 for student in students if student.cs_py == 'PY')
        aut_count = len(students) - cs_count - py_count

        # Add counts and student display string to context
        context['cs_count'] = cs_count
        context['py_count'] = py_count
        context['aut_count'] = aut_count
        context['total_students'] = len(students)
        context['student_count_display'] = f"{len(students)}({cs_count}-{py_count}-{aut_count})"

        # Calculate counts for each class
        classes_with_counts = []
        for classe in school.classe_set.all():
            students_in_classe = Eleve.objects.filter(
                inscriptions__classe=classe,
                inscriptions__annee_scolaire=current_annee_scolaire
            ).distinct()
            cs_count_classe = sum(1 for student in students_in_classe if student.cs_py == 'CS')
            py_count_classe = sum(1 for student in students_in_classe if student.cs_py == 'PY')
            aut_count_classe = len(students_in_classe) - cs_count_classe - py_count_classe
            classes_with_counts.append({
                'classe': classe,
                'cs_count': cs_count_classe,
                'py_count': py_count_classe,
                'aut_count': aut_count_classe,
                'total_students': len(students_in_classe),
            })

        # Add classes with counts to context
        context['classes_with_counts'] = classes_with_counts

        # Add form for creating new classes within the school
        context['classe_form'] = ClasseCreateForm()

        # Add page identifier
        context['page_identifier'] = 'S29'

        # Breadcrumb navigation
        context['breadcrumbs'] = [
            ('/', 'Home'),
            (reverse('home'), 'Classes'),
            ('#', school.nom)  # Current page (school name)
        ]

        return context
@method_decorator(login_required, name='dispatch')
class ClassCreateView(CreateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_create.html'

    def get_success_url(self):
        # Redirect to the school detail page after creation
        return reverse('school_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the school object to the context for use in the template
        context['school'] = get_object_or_404(Ecole, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        # Set the school for the class being created
        form.instance.ecole = get_object_or_404(Ecole, pk=self.kwargs['pk'])
        return super().form_valid(form)
        
@login_required
def load_classes(request):
    school_id = request.GET.get('school_id')
    classes = Classe.objects.filter(ecole_id=school_id).order_by('nom')
    return JsonResponse(list(classes.values('id', 'nom')), safe=False)


from django.shortcuts import render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from scuelo.models import AnneeScolaire, Classe, Ecole, Inscription


@require_http_methods(["GET", "POST"])
def manage_promotions(request):
    ecoles = Ecole.objects.all().order_by('nom')
    annee_scolaires = AnneeScolaire.objects.all().order_by('-date_initiale')

    selected_from_ecole_id = request.POST.get("from_ecole") or request.GET.get("from_ecole")
    selected_to_ecole_id = request.POST.get("to_ecole") or request.GET.get("to_ecole")

    # Classes filtrées par école sélectionnée ou vide
    from_classes = Classe.objects.filter(ecole_id=selected_from_ecole_id).order_by('nom') if selected_from_ecole_id else Classe.objects.none()
    to_classes = Classe.objects.filter(ecole_id=selected_to_ecole_id).order_by('nom') if selected_to_ecole_id else Classe.objects.none()

    promoted_students = []
    target_class = None

    selected_from_class_id = request.POST.get("from_class")
    selected_from_year_id = request.POST.get("from_year")
    selected_to_class_id = request.POST.get("to_class")
    selected_to_year_id = request.POST.get("to_year")

    if request.method == "POST":
        if not (selected_from_ecole_id and selected_from_class_id and selected_from_year_id and selected_to_ecole_id and selected_to_class_id and selected_to_year_id):
            messages.error(request, "Merci de sélectionner toutes les écoles, classes et années scolaires.")
        else:
            try:
                with transaction.atomic():
                    from_class = Classe.objects.get(id=selected_from_class_id)
                    to_class = Classe.objects.get(id=selected_to_class_id)
                    from_year = AnneeScolaire.objects.get(id=selected_from_year_id)
                    to_year = AnneeScolaire.objects.get(id=selected_to_year_id)

                    inscriptions = Inscription.objects.filter(
                        classe=from_class,
                        annee_scolaire=from_year
                    ).select_related('eleve')

                    if not inscriptions.exists():
                        messages.warning(request, f"Aucun élève trouvé dans la classe {from_class.nom} pour l'année {from_year.nom}.")
                    else:
                        promoted_count = 0
                        for inscription in inscriptions:
                            eleve = inscription.eleve
                            if eleve.cs_py == 'C':
                                eleve.condition_eleve = 'CONF'
                            elif eleve.cs_py == 'P':
                                eleve.condition_eleve = 'PROP'
                            eleve.save()

                            Inscription.objects.filter(
                                eleve=eleve,
                                annee_scolaire=to_year
                            ).delete()

                            Inscription.objects.create(
                                eleve=eleve,
                                classe=to_class,
                                annee_scolaire=to_year,
                                date_inscription=timezone.now(),
                            )
                            promoted_count += 1

                        messages.success(request, f"{promoted_count} élève(s) promu(s) avec succès.")

                    target_class = to_class
                    promoted_students = Inscription.objects.filter(
                        annee_scolaire=to_year,
                        classe=to_class
                    ).select_related('eleve').order_by('eleve__nom', 'eleve__prenom')

            except Classe.DoesNotExist:
                messages.error(request, "Une des classes sélectionnées est invalide.")
            except AnneeScolaire.DoesNotExist:
                messages.error(request, "Une des années scolaires sélectionnées est invalide.")
            except Exception as e:
                messages.error(request, f"Erreur lors de la promotion : {str(e)}")

    context = {
        "ecoles": ecoles,

        "annee_scolaires": annee_scolaires,
        "from_classes": from_classes,
        "to_classes": to_classes,
        "promoted_students": promoted_students,
        "target_class": target_class,
        "selected_from_ecole_id": int(selected_from_ecole_id) if selected_from_ecole_id else None,
        "selected_from_class_id": int(selected_from_class_id) if selected_from_class_id else None,
        "selected_from_year_id": int(selected_from_year_id) if selected_from_year_id else None,
        "selected_to_ecole_id": int(selected_to_ecole_id) if selected_to_ecole_id else None,
        "selected_to_class_id": int(selected_to_class_id) if selected_to_class_id else None,
        "selected_to_year_id": int(selected_to_year_id) if selected_to_year_id else None,
    }

    return render(request, "scuelo/promotion/manage_promotions.html", context)



def manage_single_failure(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    
    ecoles = Ecole.objects.all().order_by('nom')
    annees = AnneeScolaire.objects.all().order_by('-date_initiale')

    selected_ecole_id = None
    selected_class_id = None
    selected_year_id = None
    
    classes = Classe.objects.none()

    if request.method == 'POST':
        selected_ecole_id = request.POST.get('ecole')
        selected_class_id = request.POST.get('classe')
        selected_year_id = request.POST.get('annee_scolaire')

        # Charger les classes selon école sélectionnée pour affichage si validé
        if selected_ecole_id:
            classes = Classe.objects.filter(ecole_id=selected_ecole_id).order_by('nom')
        else:
            classes = Classe.objects.none()

        # Validation simple
        if not (selected_ecole_id and selected_class_id and selected_year_id):
            messages.error(request, "Merci de sélectionner l'école, la classe et l'année scolaire.")
        else:
            try:
                with transaction.atomic():
                    # Supprime l'inscription existante de l'élève pour l'année ciblée (promotion)
                    Inscription.objects.filter(eleve=eleve, annee_scolaire_id=selected_year_id).delete()

                    # Crée une nouvelle inscription pour le redoublement
                    classe = Classe.objects.get(id=selected_class_id)
                    annee = AnneeScolaire.objects.get(id=selected_year_id)

                    Inscription.objects.create(
                        eleve=eleve,
                        classe=classe,
                        annee_scolaire=annee,
                        date_inscription=timezone.now()
                    )

                    messages.success(request, f"L'élève {eleve.nom} {eleve.prenom} est désormais redoublant en classe {classe.nom} pour l'année {annee.nom}.")

                    # Met à jour les sélections pour affichage
                    selected_ecole_id = classe.ecole.id
                    selected_class_id = classe.id
                    selected_year_id = annee.id

            except Classe.DoesNotExist:
                messages.error(request, "La classe sélectionnée est invalide.")
            except AnneeScolaire.DoesNotExist:
                messages.error(request, "L'année scolaire sélectionnée est invalide.")
            except Exception as e:
                messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")
    else:
        # GET : Pré-remplir avec l'inscription actuelle (année en cours) et année suivante possible
        current_year = AnneeScolaire.objects.filter(actuel=True).first()
        next_year = AnneeScolaire.objects.filter(actuel=False).first()

        current_inscription = Inscription.objects.filter(eleve=eleve, annee_scolaire=current_year).first() if current_year else None

        if current_inscription:
            selected_ecole_id = current_inscription.classe.ecole.id
            selected_class_id = current_inscription.classe.id
            selected_year_id = next_year.id if next_year else None

            if selected_ecole_id:
                classes = Classe.objects.filter(ecole_id=selected_ecole_id).order_by('nom')

    context = {
        'eleve': eleve,
        'ecoles': ecoles,
        'classes': classes,
        'annees': annees,
        'selected_ecole_id': int(selected_ecole_id) if selected_ecole_id else None,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'selected_year_id': int(selected_year_id) if selected_year_id else None,
    }
    return render(request, 'scuelo/promotion/manage_single_failure.html', context)

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

@login_required
def home(request):
    # Fetch only internal (non-external) schools
    schools = Ecole.objects.filter(externe=False)
    data = {}

    # Icon mapping for each class category
    icon_mapping = {
        "Maternelle": "child",
        "Primaire": "school",
        "Secondaire": "user-graduate",
        "Lycée": "chalkboard-teacher"
    }
 
    # Get the current school year based on request or use the active year by default
    school_year_id = request.GET.get("school_year")
    if school_year_id:
        current_year = AnneeScolaire.objects.get(id=school_year_id)
    else:
        current_year = AnneeScolaire.objects.filter(actuel=True).first()
    
    all_years = AnneeScolaire.objects.all()

    # Group classes by categories within each school
    for school in schools:
        categories = {
            "Maternelle": [],
            "Primaire": [],
            "Secondaire": [],
            "Lycée": []
        }

        # Filter classes based on the selected school year and categorize
        classes = Classe.objects.filter(ecole=school)
        for classe in classes:
            category_key = None
            if classe.type.type_ecole == 'M':
                category_key = "Maternelle"
            elif classe.type.type_ecole == 'P':
                category_key = "Primaire"
            elif classe.type.type_ecole == 'S':
                category_key = "Secondaire"
            elif classe.type.type_ecole == 'L':
                category_key = "Lycée"
            
            if category_key:
                # Add class along with the corresponding icon
                categories[category_key].append({
                    'classe': classe,
                    'icon': icon_mapping.get(category_key, 'school')
                })

        # Only add school to data if it has classes in at least one category
        if any(categories.values()):
            data[school] = categories

    breadcrumbs = [('/', 'Home')]

    return render(request, 'scuelo/home.html', {
        'data': data,
        'breadcrumbs': breadcrumbs,
        'all_years': all_years,
        'current_year': current_year,
        'page_identifier': 'S01'  # Unique page identifier
    })





@login_required
def class_detail(request, pk):
    # Get the class based on the provided primary key (pk)
    classe = get_object_or_404(Classe, pk=pk)

    # Get all academic years to display in the selection dropdown
    all_annee_scolaires = AnneeScolaire.objects.all()

    # Get the selected academic year, default to the current year if none is selected
    selected_annee_scolaire_id = request.GET.get('annee_scolaire')
    selected_annee_scolaire = get_object_or_404(AnneeScolaire, pk=selected_annee_scolaire_id) if selected_annee_scolaire_id else AnneeScolaire.objects.get(actuel=True)

    # Get students registered in this class during the selected academic year, EXCLUDING those with 'ABAN' condition
    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)
    students = [inscription.eleve for inscription in inscriptions if inscription.eleve.condition_eleve != 'ABAN']

    # Calculate total payments for each student and get details of each payment
    for student in students:
        payments = Mouvement.objects.filter(inscription__eleve=student, inscription__classe=classe, inscription__annee_scolaire=selected_annee_scolaire)
        student.total_payment = payments.aggregate(total=Sum('montant'))['total'] or 0
        student.payment_details = payments.values('causal', 'montant', 'date_paye')  # Detailed payment info
        student.tenues = payments.filter(causal='TEN').values('montant')  # Only "tenues" payments
        student.notes = student.note_eleve  # Fetch student's notes if available

    # Calculate the total payment amount for the class in the selected academic year
    total_class_payment = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=selected_annee_scolaire
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Get tarifs related to this class for the selected academic year
    tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)
        # Calculate counts for each category
    cs_count = sum(1 for student in students if student.get_cs_py_display() == 'CS' )
    py_count = sum(1 for student in students if student.get_cs_py_display() == 'PY')
    aut_count = len(students) - cs_count - py_count

    # Breadcrumb navigation (for template rendering)
    breadcrumbs = [('/', 'Home'), (reverse('home'), 'Classes'), ('#', classe.nom)]
    total_students = len(students)
    student_count_display = f"{total_students}({cs_count}-{py_count}-{aut_count})"

    return render(request, 'scuelo/students/listperclasse.html', {
        'classe': classe,
        'students': students,  # List of students registered this year (excluding 'ABAN')
        'tarifs': tarifs,  # Tarifs related to this class for this year
        'breadcrumbs': breadcrumbs,
        'total_class_payment': total_class_payment,
        'student_count_display':student_count_display,
        'all_annee_scolaires': all_annee_scolaires,  # Pass all academic years for selection
        'selected_annee_scolaire': selected_annee_scolaire,  # Pass the selected academic year
        'total_class_payment': total_class_payment,  # Total amount of payments for the class in the selected year
        'page_identifier': 'S02' 
    })



class ClasseInformation(LoginRequiredMixin, DetailView):
    model = Classe
    template_name = "scuelo/classe/classe_information.html"
    context_object_name = "classe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the selected academic year (annee_scolaire)
        selected_annee_scolaire_id = self.request.GET.get('annee_scolaire')
        selected_annee_scolaire = get_object_or_404(AnneeScolaire, pk=selected_annee_scolaire_id) if selected_annee_scolaire_id else AnneeScolaire.objects.get(actuel=True)

        classe = self.get_object()

        # Get students registered in this class during the selected academic year, EXCLUDING those with 'ABAN' condition
        # First, get the inscriptions for the class and year
        inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)

        # Then, get the students who are in those inscriptions and are NOT 'ABAN'
        students = Eleve.objects.filter(
            inscriptions__in=inscriptions,  # Students in these inscriptions
            condition_eleve__ne='ABAN'  # Who are not 'ABAN'
        ).distinct()  # Avoid duplicates

        # Calculate total payments for each student and get details of each payment
        # We can now calculate payments and categorize them all in one go
        total_class_payment = 0
        total_paid_cs = 0
        total_paid_py = 0
        total_paid_conf = 0
        total_paid_aut = 0
        
        cs_students = []
        py_students = []
        conf_students = []
        aut_students = []

        for student in students:
            # Get payments for the student
            # Assuming Mouvement has a ForeignKey to Inscription named 'inscription'
            payments = Mouvement.objects.filter(
                inscription__eleve=student,
                inscription__classe=classe,
                inscription__annee_scolaire=selected_annee_scolaire
            )

            student.total_payment = payments.aggregate(total=Sum('montant'))['total'] or 0
            student.payment_details = payments.values('causal', 'montant', 'date_paye')
            student.tenues = payments.filter(causal='TEN').values('montant')  # Only "tenues" payments
            student.notes = student.note_eleve  # Assuming `note_eleve` is a field, or adjust accordingly

            # Categorize students based on cs_py and condition_eleve
            if student.cs_py == 'C':
                cs_students.append(student)
                total_paid_cs += student.total_payment
            elif student.cs_py == 'P':
                py_students.append(student)
                total_paid_py += student.total_payment
            elif student.condition_eleve == 'CONF':
                conf_students.append(student)
                total_paid_conf += student.total_payment
            else:
                aut_students.append(student)
                total_paid_aut += student.total_payment

            total_class_payment += student.total_payment

        # Get tarifs related to this class for the selected academic year
        tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)

        # Total number of students in each category
        cs_count = len(cs_students)
        py_count = len(py_students)
        conf_count = len(conf_students)
        aut_count = len(aut_students)
        total_students = len(students)

        student_count_display = f"{total_students} ({cs_count}-{py_count}-{conf_count}-{aut_count})"

        # Calculate the expected total for the class (for now, assuming it's a placeholder calculation)
        expected_total_class = self.calculate_expected_total(classe)

        # 1. PY + CONF students count
        py_conf_count = py_count + conf_count

        # 2. Progressive fees from tariffs
        progressive_fee_1 = Tarif.objects.filter(
            classe=classe,
            causal='SCO1',
            annee_scolaire=selected_annee_scolaire
        ).aggregate(total=Sum('montant'))['total'] or 0

        progressive_fee_2 = Tarif.objects.filter(
            classe=classe,
            causal='SCO2',
            annee_scolaire=selected_annee_scolaire
        ).aggregate(total=Sum('montant'))['total'] or 0

        progressive_fee_3 = Tarif.objects.filter(
            classe=classe,
            causal='SCO3',
            annee_scolaire=selected_annee_scolaire
        ).aggregate(total=Sum('montant'))['total'] or 0

        # 3. Payment percentage calculation
        expected_total_class = classe.get_expected_payment()  # Use existing method
        total_payment_percentage = round((total_class_payment / expected_total_class * 100), 2) if expected_total_class else 0

        # 4. Tenues payments for PY students
        total_tenues_py = sum(
            sum(p['montant'] for p in student.tenues)
            for student in py_students
        )

        # 5. Expected tenues for PY students
        tenues_tarif = Tarif.objects.filter(
            classe=classe,
            causal='TEN',
            annee_scolaire=selected_annee_scolaire
        ).aggregate(total=Sum('montant'))['total'] or 0
        expected_total_tenues_py = tenues_tarif * py_count

        context.update({
            'students': students,
            'tarifs': tarifs,
            'breadcrumbs': [('/', 'Home'), ('#', classe.nom)],
            'total_class_payment': total_class_payment,
            'student_count_display': student_count_display,
            'cs_count': cs_count,
            'py_count': py_count,
            'conf_count': conf_count,
            'aut_count': aut_count,
            'total_paid_cs': total_paid_cs,
            'total_paid_py': total_paid_py,
            'total_paid_conf': total_paid_conf,
            'total_paid_aut': total_paid_aut,
            'all_annee_scolaires': AnneeScolaire.objects.all(),
            'selected_annee_scolaire': selected_annee_scolaire,
            'expected_total_class': expected_total_class,  # Placeholder, replace with actual calculation if needed
            'py_conf_count': py_conf_count,
            'progressive_fee_1': progressive_fee_1,
            'progressive_fee_2': progressive_fee_2,
            'progressive_fee_3': progressive_fee_3,
            'total_payment_percentage': total_payment_percentage,
            'actual_total_received': total_class_payment,  # Same as total_class_payment
            'actual_total_received_tenues_py': total_tenues_py,
            'expected_total_tenues_py': expected_total_tenues_py,
        })

        return context

    def calculate_expected_total(self, classe):
        # Replace this with your actual calculation for the expected total for the class
        # This is just a placeholder to prevent errors
        return 0


from .forms import  StudentRangForm  
@login_required
def student_detail(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    inscriptions = Inscription.objects.filter(eleve=student).order_by('date_inscription')
    
    # Filter payments using the correct field relationship
    payments = Mouvement.objects.filter(inscription__eleve=student)
    
    total_payment = payments.aggregate(Sum('montant'))['montant__sum'] or 0
    current_class = student.current_class
    
    # Get the current school name if the student has a current class
    current_school_name = current_class.ecole.nom if current_class else "No School Assigned"
    current_class_name = current_class.type if current_class else "No Class Assigned"
    
    # Check if current_class is None
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
    
    # Handle receipt printing
    if request.method == 'POST' and 'print_receipt' in request.POST:
        payment_id = request.POST.get('payment_id')
        payment = get_object_or_404(Mouvement, pk=payment_id)

        # Render receipt template to HTML
        html_string = render_to_string('cash/paiements/receipt.html', {'student': student, 'payment': payment})

        # Generate PDF
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Create a HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=receipt_{student.nom}_{student.prenom}_{payment.id}.pdf'
        
        return response
    
    # Get the current school year and class
    current_year = AnneeScolaire.objects.filter(actuel=True).first()
    current_inscription = Inscription.objects.filter(eleve=student, annee_scolaire=current_year).first()
    current_class = current_inscription.classe if current_inscription else None

    # Handle Rang form submission
    if request.method == 'POST' and 'rang_form' in request.POST:
        rang_form = StudentRangForm(request.POST)
        if rang_form.is_valid():
            rang = rang_form.save(commit=False)
            rang.eleve = student
            rang.classe = current_class
            rang.annee_scolaire = current_year
            rang.save()
            return redirect('student_detail', pk=student.pk)  # Redirect to refresh the page
    else:
        rang_form = StudentRangForm()

    # Get existing rang data
    existing_rang = None
    if current_class and current_year:
        existing_rang = Rang.objects.filter(
            eleve=student,
            classe=current_class,
            annee_scolaire=current_year
        ).first()
        if existing_rang:
            rang_form = StudentRangForm(instance=existing_rang)  # Populate form with existing data

    return render(request, 'scuelo/students/studentdetail.html', {
        'student': student,
        'inscriptions': inscriptions,
        'payments': payments,
        'total_payment': total_payment,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'logs': logs,
        'current_school_name': current_school_name,
        'current_class_name': current_class_name,
        'page_identifier': 'S03',
        'rang_form': rang_form,  # Pass the Rang form
        'existing_rang': existing_rang,  # Pass the existing rang data
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
@method_decorator(login_required, name='dispatch')
class StudentListView(ListView):
    model = Eleve
    template_name = 'scuelo/student_management.html'
    context_object_name = 'students'

    def get_queryset(self):
        return Eleve.objects.prefetch_related(
            Prefetch(
                'inscriptions',
                queryset=Inscription.objects.select_related('classe__ecole')
            )
        ).order_by('nom', 'prenom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the current academic year
        selected_annee_scolaire = AnneeScolaire.objects.filter(actuel=True).first()
        if not selected_annee_scolaire:
            return HttpResponse("No current academic year found.", status=400)

        # Define the desired school order
        preferred_schools = ['École Maternelle Centre social de Nasara', 'École primaire Centre social de Nasara']

        # Annotate schools and classes and order them as requested
        schools = Ecole.objects.annotate(
            school_order=Case(
                *[When(nom=school, then=Value(i)) for i, school in enumerate(preferred_schools)],
                default=Value(len(preferred_schools)),
                output_field=IntegerField()
            )
        ).prefetch_related(
            Prefetch(
                'classe_set',
                queryset=Classe.objects.annotate(
                    student_count=Count('inscription')
                ).filter(student_count__gt=0).order_by('-student_count')
            )
        ).order_by('school_order', 'nom')

        # Attach payment data to each inscription
        for school in schools:
            for classe in school.classe_set.all():
                for inscription in classe.inscription_set.all():
                    eleve = inscription.eleve

                    # Calculate total payments for the student within this class and academic year
                    total_payments = Mouvement.objects.filter(
                        inscription=inscription,
                        annee_scolaire=selected_annee_scolaire
                    ).aggregate(Sum('montant'))['montant__sum'] or 0

                    # Assign the total_payments directly to the inscription
                    inscription.total_payments = total_payments

        context['schools'] = schools
        context['page_identifier'] = 'S14'
        return context



@login_required
def class_upgrade(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    
    # Get the latest inscription or None
    latest_inscription = student.inscriptions.order_by('-date_inscription').first()
    if not latest_inscription:
        # No inscription exists, show error and empty form
        form = ClassUpgradeForm()
        return render(request, 'scuelo/classe/class_upgrade.html', {
            'form': form,
            'student': student,
            'page_identifier': 'S04',
            'error': 'Student has no inscriptions.'
        })
    
    current_class = latest_inscription.classe
    current_school = current_class.ecole

    if request.method == 'POST':
        form = ClassUpgradeForm(request.POST)
        if form.is_valid():
            new_class = form.cleaned_data['new_class']

            # Create a new inscription for the upgraded class
            # Use the same school year as latest inscription or current year if you want
            new_inscription = Inscription.objects.create(
                eleve=student,
                classe=new_class,
                annee_scolaire=latest_inscription.annee_scolaire,
                date_inscription=timezone.now()
            )

            # Redirect to student detail page after upgrade
            return redirect('student_detail', pk=student.pk)
    else:
        form = ClassUpgradeForm()

    # Fetch all schools and classes for display (optional)
    schools = Ecole.objects.all()
    classes = Classe.objects.select_related('ecole').all()

    return render(request, 'scuelo/classe/class_upgrade.html', {
        'form': form,
        'student': student,
        'current_class': current_class,
        'current_school': current_school,
        'schools': schools,
        'classes': classes,
        'page_identifier': 'S04'
    })
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST  # Pass request.POST as data
        return kwargs
    
    def form_valid(self, form):
        classe = form.cleaned_data['classe']
        ecole = form.cleaned_data['ecole']
        annee_scolaire = form.cleaned_data['annee_scolaire']
        eleve = form.save()
        Inscription.objects.create(eleve=eleve, classe=classe, annee_scolaire=annee_scolaire)
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


from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from scuelo.models import AnneeScolaire, Classe, Inscription, Eleve

@require_http_methods(["GET", "POST"])
def manage_promotions(request):
    # Get all classes ordered for selection lists
    classes = Classe.objects.all().order_by('type__type_ecole', 'type__ordre', 'nom')
    # Get all school years (could be limited if you prefer)
    annee_scolaires = AnneeScolaire.objects.all().order_by('-date_initiale')
    
    promoted_students = []
    target_class = None
    
    # To remember selections and repopulate form after POST
    selected_from_class_id = None
    selected_to_class_id = None
    selected_year_id = None

    if request.method == "POST":
        selected_from_class_id = request.POST.get("from_class")
        selected_to_class_id = request.POST.get("to_class")
        selected_year_id = request.POST.get("annee_scolaire")

        if not selected_from_class_id or not selected_to_class_id or not selected_year_id:
            messages.error(request, "Veuillez sélectionner la classe source, la classe cible et l'année scolaire.")
        else:
            try:
                with transaction.atomic():
                    from_class = Classe.objects.get(id=selected_from_class_id)
                    to_class = Classe.objects.get(id=selected_to_class_id)
                    target_year = AnneeScolaire.objects.get(id=selected_year_id)
                    current_year = AnneeScolaire.objects.filter(actuel=True).first()

                    if not current_year:
                        messages.error(request, "L'année scolaire actuelle n'est pas définie.")
                        raise Exception("Current school year is not defined")

                    # Fetch inscriptions of students in 'from_class' during the current active year
                    inscriptions = Inscription.objects.filter(
                        classe=from_class, annee_scolaire=current_year
                    ).select_related('eleve')

                    if not inscriptions.exists():
                        messages.warning(request, f"Aucun élève trouvé dans la classe {from_class.nom} pour l'année courante.")
                    else:
                        promoted_count = 0
                        for inscription in inscriptions:
                            eleve = inscription.eleve

                            # Update student condition_eleve depending on cs_py
                            if eleve.cs_py == 'C':
                                eleve.condition_eleve = 'CONF'
                            elif eleve.cs_py == 'P':
                                eleve.condition_eleve = 'PROP'
                            # else keep existing value
                            eleve.save()

                            # Remove existing inscription if any to avoid duplicates
                            Inscription.objects.filter(eleve=eleve, annee_scolaire=target_year).delete()

                            # Create the new inscription for the target year and class (promotion)
                            Inscription.objects.create(
                                eleve=eleve,
                                classe=to_class,
                                annee_scolaire=target_year,
                                date_inscription=timezone.now(),
                            )
                            promoted_count += 1

                        messages.success(request, f"{promoted_count} élève(s) promu(s) avec succès.")

                    # After promotion, fetch promoted students for display
                    target_class = to_class
                    promoted_students = Inscription.objects.filter(
                        annee_scolaire=target_year,
                        classe=to_class
                    ).select_related('eleve').order_by('eleve__nom', 'eleve__prenom')

            except Classe.DoesNotExist:
                messages.error(request, "Classe invalide sélectionnée.")
            except AnneeScolaire.DoesNotExist:
                messages.error(request, "Année scolaire invalide sélectionnée.")
            except Exception as e:
                messages.error(request, f"Erreur lors de la promotion : {str(e)}")

    context = {
        "classes": classes,
        "annee_scolaires": annee_scolaires,
        "promoted_students": promoted_students,
        "target_class": target_class,
        "selected_from_class_id": selected_from_class_id,
        "selected_to_class_id": selected_to_class_id,
        "selected_year_id": selected_year_id,
    }
    return render(request, "scuelo/promotion/manage_promotions.html", context)

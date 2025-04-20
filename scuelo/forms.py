from django import forms
from .models import Eleve, Inscription, AnneeScolaire   , Ecole , Classe  ,UniformReservation , TypeClasse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User, Group 
from django.contrib.auth.forms import UserCreationForm




        
class ClasseCreateForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'type', 'legacy_id']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'legacy_id': forms.TextInput(attrs={'class': 'form-control'}),
        }   
        
        
class UniformReservationForm(forms.ModelForm):
    class Meta:
        model = UniformReservation
        fields = ['student', 'quantity', 'cost_per_uniform', 'status', 'school_year']
                 
    
'''class ClassUpgradeForm(forms.Form):
    new_school = forms.ModelChoiceField(queryset=Ecole.objects.all(), required=True, label="Nouvelle École")
    new_class = forms.ModelChoiceField(queryset=Classe.objects.none(), required=True, label="Nouvelle Classe")

    def __init__(self, *args, **kwargs):
        super(ClassUpgradeForm, self).__init__(*args, **kwargs)
        if 'new_school' in self.data:
            try:
                school_id = int(self.data.get('new_school'))
                self.fields['new_class'].queryset = Classe.objects.filter(ecole_id=school_id).order_by('nom')
            except (ValueError, TypeError):
                self.fields['new_class'].queryset = Classe.objects.none()
        else:
            self.fields['new_class'].queryset = Classe.objects.none()
'''
       
'''class ClassUpgradeForm(forms.Form):
    new_school = forms.ModelChoiceField(
        queryset=Ecole.objects.all(),
        label="Select School",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_class = forms.ModelChoiceField(
        queryset=Classe.objects.none(),  # Initially empty, will be populated via AJAX
        label="Select Class",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the new_class field based on the selected school
        if 'new_school' in self.data:
            try:
                school_id = int(self.data.get('new_school'))
                self.fields['new_class'].queryset = Classe.objects.filter(ecole_id=school_id)
            except (ValueError, TypeError):
                pass     '''     
                
class ClassUpgradeForm(forms.Form):
    ecole = forms.ModelChoiceField(
        queryset=Ecole.objects.all(),
        label="École",
        required=True,
        widget=forms.Select(attrs={'id': 'id_ecole'})
    )
    new_class = forms.ModelChoiceField(
        queryset=Classe.objects.none(),  # Initially empty
        label="New Class",
        required=True,
        widget=forms.Select(attrs={'id': 'id_new_class'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'ecole' in self.data:
            try:
                ecole_id = int(self.data['ecole'])
                self.fields['new_class'].queryset = Classe.objects.filter(ecole_id=ecole_id)
            except (ValueError, TypeError):
                pass  # Invalid input; don't filter queryset
                 
class SchoolChangeForm(forms.Form):
    new_school = forms.ModelChoiceField(queryset=Ecole.objects.all(), required=True, label="Nouvelle École")

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['classe', 'annee_scolaire']

class EcoleCreateForm(forms.ModelForm):
    class Meta:
        model = Ecole
        fields = ['nom', 'ville', 'nom_du_referent', 'prenom_du_referent', 'email_du_referent', 'telephone_du_referent', 'note', 'externe']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'email_du_referent': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone_du_referent': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'externe': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class UserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'groups']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }
   
class InscriptionPerStudentForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['classe', 'annee_scolaire']

'''class EleveCreateForm(forms.ModelForm):
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True, label="Classe")
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True, label="Année Scolaire")

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_enquete', 'condition_eleve', 'sex',
            'date_naissance', 'cs_py', 'hand', 'annee_inscr', 'parent',
            'tel_parent', 'note_eleve', 'classe', 'annee_scolaire'
        ]
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'annee_inscr': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'note_eleve': forms.Textarea(attrs={'rows': 4}),
        }
'''
from datetime import datetime
'''class EleveCreateForm(forms.ModelForm):
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True, label="Classe")
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True, label="Année Scolaire")

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_enquete', 'condition_eleve', 'sex',
            'date_naissance', 'cs_py', 'hand', 'annee_inscr',
            'parent', 'tel_parent', 'note_eleve'
        ]
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'annee_inscr': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'note_eleve': forms.Textarea(attrs={'rows': 4}),
        }
           ''' 
           

from django import forms
from .models import Eleve, Ecole, Classe, AnneeScolaire

class EleveCreateForm(forms.ModelForm):
    ecole = forms.ModelChoiceField(
        queryset=Ecole.objects.all(),
        required=True,
        label="École",
        widget=forms.Select(attrs={'id': 'id_ecole'})  # Add id for js
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        label="Classe",
        widget=forms.Select(attrs={'id': 'id_classe'})  # Add id for js
    )
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all(),
        required=True,
        label="Année Scolaire"
    )

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_enquete', 'condition_eleve', 'sex',
            'date_naissance', 'cs_py', 'hand', 'annee_inscr',
            'parent', 'tel_parent', 'note_eleve', 'ecole', 'classe', 'annee_scolaire'
        ]
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'annee_inscr': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'note_eleve': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classe'].queryset = Classe.objects.none()
        if 'ecole' in self.data:
            try:
                ecole_id = int(self.data.get('ecole'))
                self.fields['classe'].queryset = Classe.objects.filter(ecole_id=ecole_id)
            except (ValueError, TypeError):
                pass  # Invalid input; leave queryset empty



class EleveUpdateForm(forms.ModelForm):
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True, label="Année Scolaire")

    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'condition_eleve', 'sex', 'date_naissance',
            'cs_py', 'date_enquete', 'hand', 'annee_inscr', 'parent', 'tel_parent',
            'note_eleve', 'annee_scolaire'
        ]  # Removed 'classe', 'ecole'
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'annee_inscr': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'note_eleve': forms.Textarea(attrs={'rows': 4}),
        }
                    
class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['eleve', 'classe', 'annee_scolaire']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),

        }


class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_bref': forms.TextInput(attrs={'class': 'form-control'}),
            'date_initiale': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_finale': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actuel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        
class ClasseCreateForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'type']  # Remove 'ecole' since it's set automatically

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].queryset = TypeClasse.objects.all()


from .models import Rang

class StudentRangForm(forms.ModelForm):
    class Meta:
        model = Rang
        fields = ['rang1', 'rang2', 'rang3', 'rang_annuelle']
        widgets = {
            'rang1': forms.NumberInput(attrs={'class': 'form-control'}),
            'rang2': forms.NumberInput(attrs={'class': 'form-control'}),
            'rang3': forms.NumberInput(attrs={'class': 'form-control'}),
            'rang_annuelle': forms.NumberInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import Eleve, Inscription, AnneeScolaire  , Mouvement , Ecole , Classe
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User, Group 
from django.contrib.auth.forms import UserCreationForm

class PaiementPerStudentForm(forms.ModelForm):
    class Meta:
        model = Mouvement
        fields = ['date_paye', 'montant', 'causal', 'note']

class EleveUpdateForm(forms.ModelForm):
    ecole = forms.ModelChoiceField(queryset=Ecole.objects.all(), required=True)
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True)

    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'date_naissance', 'condition_eleve', 'sex',
                  'cs_py', 'hand', 'date_enquete', 'parent', 'tel_parent', 'note_eleve', 'ecole', 'classe'
        ]
        
class ClasseCreateForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'type', 'legacy_id']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'legacy_id': forms.TextInput(attrs={'class': 'form-control'}),
        }    
    
    
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


class EleveCreateForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'date_enquete', 'condition_eleve', 'sex', 'date_naissance', 'cs_py', 'hand',
                  'parent', 'tel_parent', 'note_eleve', 'legacy_id']
        widgets = {
            'date_enquete': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'condition_eleve': forms.Select(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'cs_py': forms.Select(attrs={'class': 'form-control'}),
            'hand': forms.Select(attrs={'class': 'form-control'}),
            'parent': forms.TextInput(attrs={'class': 'form-control'}),
            'tel_parent': forms.TextInput(attrs={'class': 'form-control'}),
            'note_eleve': forms.Textarea(attrs={'class': 'form-control'}),
            'legacy_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


'''class EleveUpdateForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'date_naissance', 'condition_eleve', 'sex', 'cs_py', 'date_enquete', 'hand',
                  'parent', 'tel_parent', 'note_eleve']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.instance and hasattr(self.instance, field_name):
                field.initial = getattr(self.instance, field_name)

'''
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


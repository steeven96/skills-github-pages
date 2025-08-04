from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Student, Subject, WorkGroup, AttendanceSession, Project, ProjectSubmission, DirectorComment
import openpyxl


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Créer le compte', css_class='btn btn-primary btn-lg w-100')
        )


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'filiere', 'student_id', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('filiere', css_class='form-group col-md-4 mb-3'),
                Column('student_id', css_class='form-group col-md-4 mb-3'),
                Column('email', css_class='form-group col-md-4 mb-3'),
            ),
            Submit('submit', 'Enregistrer', css_class='btn btn-success')
        )


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Fichier Excel",
        help_text="Format attendu: Nom(s), Prénom(s), Filière, Numéro étudiant, Email (optionnel)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('excel_file', css_class='form-control mb-3'),
            Submit('submit', 'Importer', css_class='btn btn-primary')
        )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if not file.name.endswith(('.xlsx', '.xls')):
            raise forms.ValidationError("Le fichier doit être au format Excel (.xlsx ou .xls)")
        return file


class WorkGroupForm(forms.ModelForm):
    group_size = forms.IntegerField(
        min_value=2, 
        max_value=10, 
        initial=4,
        label="Taille des groupes"
    )
    
    class Meta:
        model = WorkGroup
        fields = ['subject', 'is_mixed']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('subject', css_class='form-group col-md-6 mb-3'),
                Column('group_size', css_class='form-group col-md-6 mb-3'),
            ),
            Field('is_mixed', css_class='form-check-input mb-3'),
            Submit('submit', 'Créer les groupes', css_class='btn btn-success')
        )


class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['subject', 'date', 'start_time', 'end_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'subject',
            Row(
                Column('date', css_class='form-group col-md-4 mb-3'),
                Column('start_time', css_class='form-group col-md-4 mb-3'),
                Column('end_time', css_class='form-group col-md-4 mb-3'),
            ),
            'notes',
            Submit('submit', 'Créer la session', css_class='btn btn-primary')
        )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'subject', 'project_type', 'due_date', 'work_group']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            Row(
                Column('subject', css_class='form-group col-md-6 mb-3'),
                Column('project_type', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('due_date', css_class='form-group col-md-6 mb-3'),
                Column('work_group', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Créer le projet', css_class='btn btn-success')
        )


class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = ['file', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Notes optionnelles...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'file',
            'notes',
            Submit('submit', 'Soumettre le projet', css_class='btn btn-primary')
        )


class DirectorCommentForm(forms.ModelForm):
    class Meta:
        model = DirectorComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Votre commentaire...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'comment',
            Submit('submit', 'Ajouter le commentaire', css_class='btn btn-primary')
        )
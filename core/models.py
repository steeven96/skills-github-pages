from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    USER_TYPES = [
        ('student', 'Étudiant'),
        ('delegate', 'Délégué'),
        ('director', 'Directeur des Études'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()})"


class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la matière")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    teacher = models.CharField(max_length=100, verbose_name="Enseignant")
    teacher_email = models.EmailField(verbose_name="Email enseignant")
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"


class Student(models.Model):
    FILIERE_CHOICES = [
        ('informatique', 'Informatique'),
        ('mathematiques', 'Mathématiques'),
        ('physique', 'Physique'),
        ('chimie', 'Chimie'),
        ('biologie', 'Biologie'),
        ('economie', 'Économie'),
        ('gestion', 'Gestion'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="Prénom(s)")
    last_name = models.CharField(max_length=100, verbose_name="Nom(s)")
    filiere = models.CharField(max_length=50, choices=FILIERE_CHOICES, verbose_name="Filière")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="Numéro étudiant")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_filiere_display()})"
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['last_name', 'first_name']


class WorkGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du groupe")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Matière")
    students = models.ManyToManyField(Student, verbose_name="Étudiants")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    is_mixed = models.BooleanField(default=False, verbose_name="Groupes mixtes")
    
    def __str__(self):
        return f"{self.name} - {self.subject.name}"
    
    class Meta:
        verbose_name = "Groupe de travail"
        verbose_name_plural = "Groupes de travail"


class AttendanceSession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Matière")
    date = models.DateField(verbose_name="Date")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    def __str__(self):
        return f"{self.subject.name} - {self.date}"
    
    class Meta:
        verbose_name = "Session de présence"
        verbose_name_plural = "Sessions de présence"
        ordering = ['-date', '-start_time']


class Attendance(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False, verbose_name="Présent")
    notes = models.TextField(blank=True, verbose_name="Remarques")
    
    def __str__(self):
        status = "Présent" if self.is_present else "Absent"
        return f"{self.student} - {status}"
    
    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ['session', 'student']


class Project(models.Model):
    PROJECT_TYPES = [
        ('individual', 'Individuel'),
        ('group', 'Groupe'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre du projet")
    description = models.TextField(verbose_name="Description")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Matière")
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, verbose_name="Type")
    due_date = models.DateTimeField(verbose_name="Date limite")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True)
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Groupe de travail")
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['due_date']


class ProjectSubmission(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projet")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Étudiant")
    file = models.FileField(upload_to='submissions/', verbose_name="Fichier")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Soumis le")
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_validated = models.BooleanField(default=False, verbose_name="Validé")
    
    def __str__(self):
        return f"{self.project.title} - {self.student}"
    
    class Meta:
        verbose_name = "Soumission de projet"
        verbose_name_plural = "Soumissions de projet"
        unique_together = ['project', 'student']


class DirectorComment(models.Model):
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="Commentaire")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Commentaire sur {self.attendance_session}"
    
    class Meta:
        verbose_name = "Commentaire directeur"
        verbose_name_plural = "Commentaires directeur"
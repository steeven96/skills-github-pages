from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import openpyxl
import random
from collections import defaultdict
from .models import *
from .forms import *


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Créer le profil utilisateur par défaut comme étudiant
            UserProfile.objects.create(user=user, user_type='student')
            login(request, user)
            messages.success(request, 'Compte créé avec succès!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    user_profile = getattr(request.user, 'userprofile', None)
    if not user_profile:
        # Créer un profil par défaut si il n'existe pas
        user_profile = UserProfile.objects.create(user=request.user, user_type='student')
    
    context = {
        'user_profile': user_profile,
    }
    
    if user_profile.user_type == 'delegate':
        context.update({
            'students_count': Student.objects.count(),
            'subjects_count': Subject.objects.count(),
            'groups_count': WorkGroup.objects.filter(created_by=request.user).count(),
            'recent_sessions': AttendanceSession.objects.filter(created_by=request.user)[:5],
        })
    elif user_profile.user_type == 'director':
        context.update({
            'total_sessions': AttendanceSession.objects.count(),
            'pending_comments': AttendanceSession.objects.filter(directorcomment__isnull=True).count(),
            'recent_sessions': AttendanceSession.objects.all()[:5],
        })
    elif user_profile.user_type == 'student':
        try:
            student = Student.objects.get(user=request.user)
            context.update({
                'student': student,
                'my_groups': WorkGroup.objects.filter(students=student),
                'my_projects': Project.objects.filter(
                    Q(project_type='individual') | 
                    Q(work_group__students=student)
                ).distinct(),
            })
        except Student.DoesNotExist:
            messages.warning(request, 'Votre profil étudiant n\'est pas encore configuré.')
    
    return render(request, 'core/dashboard.html', context)


@login_required
def students_list(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    students = Student.objects.all()
    return render(request, 'core/students_list.html', {'students': students})


@login_required
def add_student(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Étudiant ajouté avec succès!')
            return redirect('students_list')
    else:
        form = StudentForm()
    
    return render(request, 'core/add_student.html', {'form': form})


@login_required
def import_students(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
                
                imported_count = 0
                errors = []
                
                for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(row[:4]):  # Skip empty rows
                        continue
                    
                    try:
                        last_name = str(row[0]).strip() if row[0] else ''
                        first_name = str(row[1]).strip() if row[1] else ''
                        filiere = str(row[2]).strip().lower() if row[2] else ''
                        student_id = str(row[3]).strip() if row[3] else ''
                        email = str(row[4]).strip() if row[4] and len(row) > 4 else ''
                        
                        if not all([last_name, first_name, filiere, student_id]):
                            errors.append(f"Ligne {row_num}: Données manquantes")
                            continue
                        
                        # Vérifier si la filière existe dans les choix
                        filiere_choices = dict(Student.FILIERE_CHOICES)
                        filiere_key = None
                        for key, value in filiere_choices.items():
                            if filiere.lower() in [key.lower(), value.lower()]:
                                filiere_key = key
                                break
                        
                        if not filiere_key:
                            errors.append(f"Ligne {row_num}: Filière '{filiere}' non reconnue")
                            continue
                        
                        # Créer ou mettre à jour l'étudiant
                        student, created = Student.objects.get_or_create(
                            student_id=student_id,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'filiere': filiere_key,
                                'email': email,
                            }
                        )
                        
                        if created:
                            imported_count += 1
                        else:
                            # Mettre à jour les informations existantes
                            student.first_name = first_name
                            student.last_name = last_name
                            student.filiere = filiere_key
                            student.email = email
                            student.save()
                    
                    except Exception as e:
                        errors.append(f"Ligne {row_num}: Erreur - {str(e)}")
                
                if imported_count > 0:
                    messages.success(request, f'{imported_count} étudiants importés avec succès!')
                
                if errors:
                    for error in errors[:5]:  # Afficher seulement les 5 premières erreurs
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f"... et {len(errors) - 5} autres erreurs")
                
                return redirect('students_list')
            
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'importation: {str(e)}')
    else:
        form = ExcelUploadForm()
    
    return render(request, 'core/import_students.html', {'form': form})


@login_required
def create_groups(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = WorkGroupForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            group_size = form.cleaned_data['group_size']
            is_mixed = form.cleaned_data['is_mixed']
            
            # Supprimer les anciens groupes pour cette matière
            WorkGroup.objects.filter(subject=subject, created_by=request.user).delete()
            
            students = list(Student.objects.all())
            if not students:
                messages.error(request, 'Aucun étudiant trouvé. Veuillez d\'abord ajouter des étudiants.')
                return redirect('students_list')
            
            groups = []
            
            if is_mixed:
                # Groupes mixtes - équilibrer les filières
                filieres = defaultdict(list)
                for student in students:
                    filieres[student.filiere].append(student)
                
                # Mélanger chaque filière
                for filiere_students in filieres.values():
                    random.shuffle(filiere_students)
                
                # Créer les groupes en distribuant équitablement les filières
                num_groups = len(students) // group_size + (1 if len(students) % group_size > 0 else 0)
                groups = [[] for _ in range(num_groups)]
                
                # Distribuer les étudiants par filière
                for filiere, filiere_students in filieres.items():
                    for i, student in enumerate(filiere_students):
                        group_index = i % num_groups
                        groups[group_index].append(student)
            else:
                # Groupes aléatoires simples
                random.shuffle(students)
                for i in range(0, len(students), group_size):
                    group = students[i:i + group_size]
                    if group:  # Ne pas créer de groupes vides
                        groups.append(group)
            
            # Créer les groupes dans la base de données
            for i, group_students in enumerate(groups, 1):
                if group_students:  # Vérifier que le groupe n'est pas vide
                    work_group = WorkGroup.objects.create(
                        name=f"Groupe {i} - {subject.name}",
                        subject=subject,
                        created_by=request.user,
                        is_mixed=is_mixed
                    )
                    work_group.students.set(group_students)
            
            messages.success(request, f'{len(groups)} groupes créés avec succès pour {subject.name}!')
            return redirect('groups_list')
    else:
        form = WorkGroupForm()
    
    return render(request, 'core/create_groups.html', {'form': form})


@login_required
def groups_list(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    groups = WorkGroup.objects.filter(created_by=request.user).prefetch_related('students', 'subject')
    return render(request, 'core/groups_list.html', {'groups': groups})


@login_required
def attendance_sessions(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    sessions = AttendanceSession.objects.filter(created_by=request.user).order_by('-date', '-start_time')
    return render(request, 'core/attendance_sessions.html', {'sessions': sessions})


@login_required
def create_attendance_session(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            
            # Créer les entrées de présence pour tous les étudiants
            students = Student.objects.all()
            for student in students:
                Attendance.objects.create(
                    session=session,
                    student=student,
                    is_present=False
                )
            
            messages.success(request, 'Session de présence créée avec succès!')
            return redirect('take_attendance', session_id=session.id)
    else:
        form = AttendanceSessionForm()
    
    return render(request, 'core/create_attendance_session.html', {'form': form})


@login_required
def take_attendance(request, session_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'delegate':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    session = get_object_or_404(AttendanceSession, id=session_id, created_by=request.user)
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    if request.method == 'POST':
        for attendance in attendances:
            is_present = request.POST.get(f'present_{attendance.id}') == 'on'
            attendance.is_present = is_present
            attendance.save()
        
        messages.success(request, 'Présences enregistrées avec succès!')
        return redirect('attendance_sessions')
    
    return render(request, 'core/take_attendance.html', {
        'session': session,
        'attendances': attendances
    })


@login_required
def generate_attendance_pdf(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Vérifier les permissions
    user_profile = getattr(request.user, 'userprofile', None)
    if not user_profile or user_profile.user_type not in ['delegate', 'director']:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="presence_{session.subject.code}_{session.date}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.darkblue
    )
    
    title = f"Liste de Présence - {session.subject.name}"
    story.append(Paragraph(title, title_style))
    
    # Informations de la session
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )
    
    info_text = f"""
    <b>Matière:</b> {session.subject.name} ({session.subject.code})<br/>
    <b>Enseignant:</b> {session.subject.teacher}<br/>
    <b>Date:</b> {session.date.strftime('%d/%m/%Y')}<br/>
    <b>Horaire:</b> {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}<br/>
    <b>Délégué:</b> {session.created_by.get_full_name()}<br/>
    """
    
    story.append(Paragraph(info_text, info_style))
    story.append(Spacer(1, 20))
    
    # Tableau des présences
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    data = [['#', 'Nom', 'Prénom', 'Filière', 'Présence', 'Signature']]
    
    for i, attendance in enumerate(attendances, 1):
        status = '✓' if attendance.is_present else '✗'
        data.append([
            str(i),
            attendance.student.last_name,
            attendance.student.first_name,
            attendance.student.get_filiere_display(),
            status,
            ''  # Colonne pour signature
        ])
    
    table = Table(data, colWidths=[0.5*inch, 1.5*inch, 1.5*inch, 1.2*inch, 0.8*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(table)
    
    # Statistiques
    total_students = attendances.count()
    present_count = attendances.filter(is_present=True).count()
    absent_count = total_students - present_count
    
    story.append(Spacer(1, 30))
    stats_text = f"""
    <b>Statistiques:</b><br/>
    Total étudiants: {total_students}<br/>
    Présents: {present_count}<br/>
    Absents: {absent_count}<br/>
    Taux de présence: {(present_count/total_students*100):.1f}% si total_students > 0 else 0
    """
    
    story.append(Paragraph(stats_text, info_style))
    
    # Notes si présentes
    if session.notes:
        story.append(Spacer(1, 20))
        notes_text = f"<b>Notes:</b><br/>{session.notes}"
        story.append(Paragraph(notes_text, info_style))
    
    doc.build(story)
    return response


# Vues pour le directeur des études
@login_required
def director_attendance_list(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'director':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    sessions = AttendanceSession.objects.all().order_by('-date', '-start_time')
    
    # Filtres
    subject_filter = request.GET.get('subject')
    date_filter = request.GET.get('date')
    
    if subject_filter:
        sessions = sessions.filter(subject_id=subject_filter)
    if date_filter:
        sessions = sessions.filter(date=date_filter)
    
    subjects = Subject.objects.all()
    
    return render(request, 'core/director_attendance_list.html', {
        'sessions': sessions,
        'subjects': subjects,
        'subject_filter': subject_filter,
        'date_filter': date_filter,
    })


@login_required
def director_add_comment(request, session_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'director':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    if request.method == 'POST':
        form = DirectorCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.attendance_session = session
            comment.created_by = request.user
            comment.save()
            messages.success(request, 'Commentaire ajouté avec succès!')
            return redirect('director_attendance_list')
    else:
        form = DirectorCommentForm()
    
    return render(request, 'core/director_add_comment.html', {
        'form': form,
        'session': session
    })


# Vues pour les étudiants
@login_required
def student_groups(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'student':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
        groups = WorkGroup.objects.filter(students=student)
        return render(request, 'core/student_groups.html', {
            'student': student,
            'groups': groups
        })
    except Student.DoesNotExist:
        messages.error(request, 'Profil étudiant non trouvé.')
        return redirect('dashboard')


@login_required
def student_projects(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'student':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
        projects = Project.objects.filter(
            Q(project_type='individual') | 
            Q(work_group__students=student)
        ).distinct()
        
        return render(request, 'core/student_projects.html', {
            'student': student,
            'projects': projects
        })
    except Student.DoesNotExist:
        messages.error(request, 'Profil étudiant non trouvé.')
        return redirect('dashboard')


@login_required
def submit_project(request, project_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'student':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    project = get_object_or_404(Project, id=project_id)
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Vérifier si l'étudiant peut soumettre ce projet
        can_submit = False
        if project.project_type == 'individual':
            can_submit = True
        elif project.work_group and student in project.work_group.students.all():
            can_submit = True
        
        if not can_submit:
            messages.error(request, 'Vous n\'êtes pas autorisé à soumettre ce projet.')
            return redirect('student_projects')
        
        # Vérifier si déjà soumis
        existing_submission = ProjectSubmission.objects.filter(
            project=project, 
            student=student
        ).first()
        
        if request.method == 'POST':
            form = ProjectSubmissionForm(request.POST, request.FILES, instance=existing_submission)
            if form.is_valid():
                submission = form.save(commit=False)
                submission.project = project
                submission.student = student
                submission.save()
                
                action = 'mis à jour' if existing_submission else 'soumis'
                messages.success(request, f'Projet {action} avec succès!')
                return redirect('student_projects')
        else:
            form = ProjectSubmissionForm(instance=existing_submission)
        
        return render(request, 'core/submit_project.html', {
            'form': form,
            'project': project,
            'existing_submission': existing_submission
        })
        
    except Student.DoesNotExist:
        messages.error(request, 'Profil étudiant non trouvé.')
        return redirect('dashboard')
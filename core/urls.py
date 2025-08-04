from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('', auth_views.LoginView.as_view(), name='login'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Delegate views - Students management
    path('students/', views.students_list, name='students_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/import/', views.import_students, name='import_students'),
    
    # Delegate views - Groups management
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.create_groups, name='create_groups'),
    
    # Delegate views - Attendance management
    path('attendance/', views.attendance_sessions, name='attendance_sessions'),
    path('attendance/create/', views.create_attendance_session, name='create_attendance_session'),
    path('attendance/<int:session_id>/', views.take_attendance, name='take_attendance'),
    path('attendance/<int:session_id>/pdf/', views.generate_attendance_pdf, name='generate_attendance_pdf'),
    
    # Director views
    path('director/attendance/', views.director_attendance_list, name='director_attendance_list'),
    path('director/attendance/<int:session_id>/comment/', views.director_add_comment, name='director_add_comment'),
    
    # Student views
    path('student/groups/', views.student_groups, name='student_groups'),
    path('student/projects/', views.student_projects, name='student_projects'),
    path('student/projects/<int:project_id>/submit/', views.submit_project, name='submit_project'),
]
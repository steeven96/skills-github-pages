from django.contrib import admin
from .models import (
    UserProfile, Subject, Student, WorkGroup, AttendanceSession, 
    Attendance, Project, ProjectSubmission, DirectorComment
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone']
    list_filter = ['user_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'teacher', 'teacher_email']
    search_fields = ['name', 'code', 'teacher']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'filiere', 'email']
    list_filter = ['filiere']
    search_fields = ['first_name', 'last_name', 'student_id', 'email']


@admin.register(WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'created_by', 'created_at', 'is_mixed']
    list_filter = ['subject', 'is_mixed', 'created_at']
    filter_horizontal = ['students']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'date', 'start_time', 'end_time', 'created_by']
    list_filter = ['subject', 'date', 'created_by']
    date_hierarchy = 'date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'is_present']
    list_filter = ['is_present', 'session__subject', 'session__date']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'project_type', 'due_date', 'created_by']
    list_filter = ['subject', 'project_type', 'due_date']
    search_fields = ['title', 'description']


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ['project', 'student', 'submitted_at', 'is_validated']
    list_filter = ['is_validated', 'submitted_at', 'project__subject']
    search_fields = ['project__title', 'student__first_name', 'student__last_name']


@admin.register(DirectorComment)
class DirectorCommentAdmin(admin.ModelAdmin):
    list_display = ['attendance_session', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
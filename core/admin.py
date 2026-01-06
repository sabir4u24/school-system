from django.contrib import admin
from .models import Student, Subject, MarksEntry, CoScholasticResult, TeacherProfile, StaffProfile, Session

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_current', 'start_date', 'end_date')
    list_editable = ('is_current',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('st_id', 'student_name', 'class_name', 'section', 'roll_no')
    search_fields = ('st_id', 'student_name', 'class_name')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_optional')

@admin.register(MarksEntry)
class MarksEntryAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'term', 'total_marks')
    list_filter = ('subject', 'term', 'student__class_name')

admin.site.register(CoScholasticResult)
admin.site.register(TeacherProfile)
admin.site.register(StaffProfile)

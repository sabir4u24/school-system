from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.http import HttpResponse
from .models import Student, Subject, MarksEntry, TeacherProfile, StaffProfile, StudentSubject, SchoolBranch, Session, STREAM_CHOICES, CLASS_CHOICES, SECTION_CHOICES, CoScholasticResult
import csv
from .forms import StudentAdmissionForm, SubjectAssignmentForm, AttendanceSettingsForm
from .forms_marks import MarksSelectionForm, MarksEntryFormSet, CoScholasticEntryForm
from .pdf_utils import render_to_pdf
import csv
import io
import os
import subprocess
from django.conf import settings
from datetime import datetime

# Class-wise subject mapping
CLASS_SUBJECT_MAPPING = {
    'Babyland': ['English', 'Hindi', 'Drawing'],
    'KG': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '1': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '2': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '3': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer'],
    '4': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '5': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '6': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '7': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '8': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '9': ['English', 'Hindi', 'Assamese', 'Mathematics', 'Science', 'Social Science', 'Artificial Intelligence', 'Painting'],
    '10': ['English', 'Hindi', 'Assamese', 'Mathematics', 'Science', 'Social Science', 'Artificial Intelligence', 'Painting'],
    '11': ['English', 'Hindi', 'Physics', 'Accountancy', 'Political Science', 'Biology', 'Economics', 'Geography', 'Mathematics', 'Psychology', 'Informatics Practices', 'Computer Science', 'Chemistry', 'Business Studies', 'Sociology', 'Physical Education'],
    '12': ['English', 'Hindi', 'Physics', 'Accountancy', 'Political Science', 'Biology', 'Economics', 'Geography', 'Mathematics', 'Psychology', 'Informatics Practices', 'Computer Science', 'Chemistry', 'Business Studies', 'Sociology', 'Physical Education']
}

@login_required
def assign_subjects_view(request, student_id):
    # Only Admin or Staff can assign subjects
    # Only Admin, Staff, or Teachers can assign subjects
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    is_teacher = hasattr(request.user, 'teacher_profile')
    
    if not (request.user.is_superuser or is_staff or is_teacher):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    student = get_object_or_404(Student, st_id=student_id)
    
    # Extra check for teachers: can only assign to their own students
    if is_teacher and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        if not (student.class_name == teacher.assigned_class and 
                student.section == teacher.assigned_section and
                student.school_branch == teacher.school_branch):
             messages.error(request, "Permission Denied. You can only assign subjects to your own students.")
             return redirect('student_list')
    
    if request.method == 'POST':
        # Clear existing subjects
        StudentSubject.objects.filter(student=student).delete()
        
        # Get selected subjects from form
        subject_ids = request.POST.getlist('subjects')
        
        for subj_id in subject_ids:
            subject = Subject.objects.get(id=subj_id)
            StudentSubject.objects.create(student=student, subject=subject)
        
        messages.success(request, f"Subjects updated for {student.student_name}")
        return redirect('student_list')
    else:
        # Get current subjects
        current_subjects = StudentSubject.objects.filter(student=student).values_list('subject', flat=True)
        
        # Get available subjects based on class
        class_name = student.class_name
        
        if class_name in ['11', '12']:
            # For classes 11 and 12, show all elective subjects
            available_subject_names = [
                'English', 'Hindi', 'Physics', 'Accountancy', 'Political Science', 
                'Biology', 'Economics', 'Geography', 'Mathematics', 'Psychology', 
                'Informatics Practices', 'Computer Science', 'Chemistry', 
                'Business Studies', 'Sociology', 'Physical Education'
            ]
            max_subjects = 6
        else:
            # For other classes, use predefined mapping
            available_subject_names = CLASS_SUBJECT_MAPPING.get(class_name, [])
            max_subjects = len(available_subject_names)
        
        # Get or create subject objects
        available_subjects = []
        for subject_name in available_subject_names:
            subject, created = Subject.objects.get_or_create(name=subject_name)
            available_subjects.append(subject)
        
        context = {
            'student': student,
            'available_subjects': available_subjects,
            'current_subjects': current_subjects,
            'max_subjects': max_subjects,
            'is_elective_class': class_name in ['11', '12']
        }
        
        return render(request, 'core/assign_subjects.html', context)

@login_required
def bulk_assign_subjects_view(request):
    # Only Admin or Teachers
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    class_name = None
    section = None
    branch = None
    
    if hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        class_name = teacher.assigned_class
        section = teacher.assigned_section
        branch = teacher.school_branch
    else:
        # Admin: simplified for now, could take GET param
        messages.warning(request, "Bulk assignment is currently optimized for Teachers.")
        return redirect('student_list')

    if class_name in ['11', '12']:
        messages.warning(request, f"Bulk assignment is not available for Class {class_name} as subjects are elective.")
        return redirect('student_list')
        
    # Get subjects mapping
    subject_names = CLASS_SUBJECT_MAPPING.get(class_name, [])
    if not subject_names:
        messages.error(request, f"No default subjects found for Class {class_name}.")
        return redirect('student_list')
        
    # Get relevant students
    students = Student.objects.filter(class_name=class_name, section=section, school_branch=branch)
    
    count = 0
    for student in students:
        # Clear existing? Maybe safer not to, or yes to ensure consistency?
        # Let's clean slate for consistency as per "Assign Default Subjects"
        StudentSubject.objects.filter(student=student).delete()
        
        for name in subject_names:
            subject, _ = Subject.objects.get_or_create(name=name)
            StudentSubject.objects.create(student=student, subject=subject)
        count += 1
        
    messages.success(request, f"Successfully assigned default subjects to {count} students in Class {class_name}-{section}.")
    return redirect('student_list')

@login_required
def bulk_assign_subjects_selection_view(request):
    # Only Admin or Teachers
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    if request.method == 'POST':
        student_ids = request.POST.getlist('selected_students')
        
        if not student_ids:
            messages.warning(request, "Please select at least one student.")
            return redirect('student_list')
        
        # Validate students and get common class
        students = Student.objects.filter(st_id__in=student_ids)
        if not students.exists():
            messages.error(request, "Invalid students selected.")
            return redirect('student_list')

        first_student = students.first()
        class_name = first_student.class_name
        
        # Verify all students are in the same class (optional but good for UI consistency)
        if students.exclude(class_name=class_name).exists():
             messages.warning(request, "Mixed classes selected. Please select students from the same class.")
             return redirect('student_list')

        # Handle class 11/12 specific logic or standard map
        if class_name in ['11', '12']:
            available_subject_names = [
                'English', 'Hindi', 'Physics', 'Accountancy', 'Political Science', 
                'Biology', 'Economics', 'Geography', 'Mathematics', 'Psychology', 
                'Informatics Practices', 'Computer Science', 'Chemistry', 
                'Business Studies', 'Sociology', 'Physical Education'
            ]
            max_subjects = 6
        else:
             available_subject_names = CLASS_SUBJECT_MAPPING.get(class_name, [])
             max_subjects = len(available_subject_names)

        available_subjects = []
        for subject_name in available_subject_names:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            available_subjects.append(subject)
            
        context = {
            'students': students,
            'student_ids': ",".join(student_ids), # Pass IDs as comma separated string
            'available_subjects': available_subjects,
            'max_subjects': max_subjects,
            'class_name': class_name,
            'is_elective_class': class_name in ['11', '12']
        }
        return render(request, 'core/bulk_assign_subjects.html', context)
        
    elif request.method == 'GET':
         # If GET, maybe processing the final assignment
         # Wait, the plan was 2 steps.
         # Step 2: Final assignment POST
         pass
         
    return redirect('student_list')

@login_required
def bulk_assign_subjects_save_view(request):
    if request.method == 'POST':
        student_ids_str = request.POST.get('student_ids')
        subject_ids = request.POST.getlist('subjects')
        
        if not student_ids_str or not subject_ids:
            messages.error(request, "Missing data.")
            return redirect('student_list')
            
        student_ids = student_ids_str.split(',')
        students = Student.objects.filter(st_id__in=student_ids)
        
        count = 0
        for student in students:
            StudentSubject.objects.filter(student=student).delete()
            for subj_id in subject_ids:
                subject = Subject.objects.get(id=subj_id)
                StudentSubject.objects.create(student=student, subject=subject)
            count += 1
            
        messages.success(request, f"Assigned subjects to {count} students.")
        return redirect('student_list')
        
    return redirect('student_list')

def marks_entry_view(request):
    # Only Teachers (or Admin) can enter marks
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Permission Denied. Only Teachers can enter marks.")
        return redirect('home')

    teacher_profile = getattr(request.user, 'teacher_profile', None)
    
    allowed_subjects = None
    if teacher_profile and teacher_profile.assigned_class:
         # Filter based on assigned class
         # Note: this requires CLASS_SUBJECT_MAPPING to be accessible or logic duplicated. 
         # Since CLASS_SUBJECT_MAPPING is defined in this file (views.py), we can use it.
         subject_names = CLASS_SUBJECT_MAPPING.get(teacher_profile.assigned_class, [])
         
         if subject_names:
             allowed_subjects = Subject.objects.filter(name__in=subject_names)


    form = MarksSelectionForm(request.GET or None, teacher_profile=teacher_profile, allowed_subjects=allowed_subjects)
    formset = None
    students_data = []

    if request.method == 'POST' and 'submit_marks' in request.POST:
        # Reconstruct formset from POST data
        formset = MarksEntryFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            
            # Handle attendance and promotion status data
            for key, value in request.POST.items():
                if key.startswith('attendance_'):
                    student_id = key.replace('attendance_', '')
                    try:
                        student = Student.objects.get(st_id=student_id)
                        days_present = int(value) if value else 0
                        student.days_present = days_present
                        
                        # Handle Promotion Status (same loop as it's per student)
                        # The key for status is promotion_status_{student_id}
                        status_key = f'promotion_status_{student_id}'
                        promotion_status = request.POST.get(status_key)
                        if promotion_status in ['Promoted', 'Detained']:
                            student.promotion_status = promotion_status
                        elif promotion_status == "":
                             student.promotion_status = None # Clear if selected default
                        
                        student.save()
                    except (Student.DoesNotExist, ValueError):
                        pass
            
            messages.success(request, "Marks and attendance updated successfully!")
            return redirect(request.get_full_path())
        else:
            messages.error(request, "Error saving marks. Please check inputs.")
    
    elif form.is_valid():
        if teacher_profile:
            # Force teacher's class settings
            class_name = teacher_profile.assigned_class
            section = teacher_profile.assigned_section
        else:
            class_name = form.cleaned_data['class_name']
            section = form.cleaned_data['section']
            
        subject = form.cleaned_data['subject']
        term = int(form.cleaned_data['term'])

        # Filter students based on selected criteria AND subject assignment
        students = Student.objects.filter(
            class_name=class_name,
            section=section,
            subjects__subject=subject  # Only students assigned this subject
        ).distinct()

        # For teachers, further filter by their assigned branch
        if teacher_profile:
            students = students.filter(school_branch=teacher_profile.school_branch)
        
        students = students.order_by('roll_no', 'student_name')
        
        # Ensure MarksEntry objects exist for all valid students
        for student in students:
            MarksEntry.objects.get_or_create(
                student=student,
                subject=subject,
                term=term
            )
        
        # Get queryset for selected criteria
        queryset = MarksEntry.objects.filter(
            student__class_name=class_name,
            student__section=section,
            subject=subject,
            term=term
        ).order_by('student__roll_no', 'student__student_name')
        
        formset = MarksEntryFormSet(queryset=queryset)
        students_data = list(students.values('st_id', 'student_name', 'roll_no', 'days_present', 'total_days'))

    return render(request, 'core/marks_entry.html', {
        'form': form, 
        'formset': formset,
        'students_data': students_data
    })

@login_required
def co_scholastic_entry_view(request):
    # Only Teachers (or Admin)
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    teacher_profile = getattr(request.user, 'teacher_profile', None)
    
    # Defaults
    class_name = None
    section = None
    
    if teacher_profile:
        class_name = teacher_profile.assigned_class
        section = teacher_profile.assigned_section
    else:
        # Admin needs to select class/section via GET params or show a selection form
        # For simplicity, let's look for GET params, or if not, redirect to marks entry to select
        class_name = request.GET.get('class_name')
        section = request.GET.get('section')
        
    students = Student.objects.none()
    
    if class_name and section:
        students = Student.objects.filter(class_name=class_name, section=section).order_by('roll_no')
        if teacher_profile:
             students = students.filter(school_branch=teacher_profile.school_branch)
        
        # Ensure objects exist
        for student in students:
            CoScholasticResult.objects.get_or_create(student=student)
            
    # Formset
    from django.forms import modelformset_factory
    CoScholasticFormSet = modelformset_factory(CoScholasticResult, form=CoScholasticEntryForm, extra=0)
    
    if request.method == 'POST':
        formset = CoScholasticFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Co-Scholastic grades updated successfully!")
            return redirect(request.get_full_path() + f"?class_name={class_name}&section={section}")
        else:
            messages.error(request, "Error saving grades.")
    else:
        if students.exists():
            queryset = CoScholasticResult.objects.filter(student__in=students).order_by('student__roll_no')
            formset = CoScholasticFormSet(queryset=queryset)
        else:
             formset = None

    context = {
        'formset': formset,
        'class_name': class_name,
        'section': section,
        'is_teacher': teacher_profile is not None
    }
    return render(request, 'core/co_scholastic_entry.html', context)

@login_required
def home(request):
    user = request.user
    total_students = Student.objects.count()
    context = {'total_students': total_students}
    
    if hasattr(user, 'teacher_profile'):
        teacher = user.teacher_profile
        my_students = Student.objects.filter(
            class_name=teacher.assigned_class,
            section=teacher.assigned_section,
            school_branch=teacher.school_branch
        )
        context['my_students_count'] = my_students.count()
        context['assigned_class'] = f"{teacher.assigned_class} - {teacher.assigned_section}"
        
        # Get current total_days setting (from first student in class)
        first_student = my_students.first()
        current_total_days = first_student.total_days if first_student and first_student.total_days else 0
        
        # Handle attendance settings form
        if request.method == 'POST' and 'set_attendance' in request.POST:
            attendance_form = AttendanceSettingsForm(request.POST)
            if attendance_form.is_valid():
                total_days = attendance_form.cleaned_data['total_days']
                # Update all students in this class
                my_students.update(total_days=total_days)
                messages.success(request, f"Total attendance days set to {total_days} for all students in {context['assigned_class']}")
                return redirect('home')
        else:
            attendance_form = AttendanceSettingsForm(initial={'total_days': current_total_days})
        
        context['attendance_form'] = attendance_form
        context['current_total_days'] = current_total_days
        
    return render(request, 'core/home.html', context)

@login_required
def teacher_reports_view(request):
    # Teachers see only their assigned class/section/branch students
    if hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        students = Student.objects.filter(
            class_name=teacher.assigned_class,
            section=teacher.assigned_section,
            school_branch=teacher.school_branch
        ).order_by('roll_no')
    else:
        # Admin sees all students
        students = Student.objects.all().order_by('st_id')
    
    # Search
    q = request.GET.get('q', '')
    if q:
        students = students.filter(
            models.Q(st_id__icontains=q) |
            models.Q(student_name__icontains=q) |
            models.Q(fathers_name__icontains=q)
        )
    
    return render(request, 'core/teacher_reports.html', {'students': students, 'query': q})

@login_required
def bulk_download_reports(request):
    # Teachers: bulk download for their assigned class/section/branch
    if hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        students = Student.objects.filter(
            class_name=teacher.assigned_class,
            section=teacher.assigned_section,
            school_branch=teacher.school_branch
        ).order_by('roll_no')
    else:
        # Admin: would need class selection (for now, all students - can be improved)
        students = Student.objects.all().order_by('st_id')

    # Search
    q = request.GET.get('q', '')
    if q:
        students = students.filter(
            models.Q(st_id__icontains=q) |
            models.Q(student_name__icontains=q) |
            models.Q(fathers_name__icontains=q)
        )
    
    # For now, just render a list of students that would be included
    # In a real scenario, this would trigger a PDF generation for each student
    # and potentially combine them or zip them.
    return render(request, 'core/bulk_download_reports.html', {'students': students, 'query': q})

@login_required
def student_list(request):
    students = _get_filtered_students(request)
    
    # Optimization: Calculate permissions once
    is_teacher = hasattr(request.user, 'teacher_profile') or request.user.groups.filter(name='Teachers').exists()
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    
    # Get choices for filters
    context = {
        'students': students,
        'query': request.GET.get('q', ''),
        'stream_choices': STREAM_CHOICES,
        'class_choices': CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
        'branch_choices': SchoolBranch.objects.all(),
        # Maintain filter state
        'selected_stream': request.GET.get('stream', ''),
        'selected_class': request.GET.get('class_name', ''),
        'selected_section': request.GET.get('section', ''),
        'selected_branch': request.GET.get('branch', ''),
        # Pass flags to template
        'is_teacher': is_teacher,
        'is_staff': is_staff,
    }

    return render(request, 'core/student_list.html', context)

def _get_filtered_students(request):
    """Helper to verify permissions and apply filters for student list and exports."""
    # Teacher permission check
    if hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        students = Student.objects.filter(
            class_name=teacher.assigned_class,
            section=teacher.assigned_section,
            school_branch=teacher.school_branch
        ).order_by('roll_no')
    else:
        students = Student.objects.all().order_by('st_id')

    # Apply Filters
    stream = request.GET.get('stream')
    branch = request.GET.get('branch')
    class_name = request.GET.get('class_name')
    section = request.GET.get('section')
    q = request.GET.get('q')

    if stream:
        students = students.filter(stream=stream)
    if branch:
        students = students.filter(school_branch=branch)
    if class_name:
        students = students.filter(class_name=class_name)
    if section:
        students = students.filter(section=section)
    
    # Search
    if q:
        students = students.filter(
            models.Q(st_id__icontains=q) |
            models.Q(student_name__icontains=q) |
            models.Q(fathers_name__icontains=q)
        )
    
    return students

@login_required
def export_students_csv(request):
    students = _get_filtered_students(request)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_list.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Name', 'Stream', 'Branch', 'Class', 'Section', 'Roll No', 'Father Name'])
    
    for student in students:
        writer.writerow([
            student.st_id,
            student.student_name,
            student.stream,
            student.school_branch,
            student.class_name,
            student.section,
            student.roll_no,
            student.fathers_name
        ])
        
    return response

@login_required
def export_students_pdf(request):
    students = _get_filtered_students(request)
    
    context = {
        'students': students,
        'class_name': request.GET.get('class_name'),
        'section': request.GET.get('section'),
        'stream': request.GET.get('stream'),
        'branch': request.GET.get('branch'),
    }
    
    return render_to_pdf('core/student_list_pdf.html', context, request)

@login_required
def admission_view(request):
    # Only Admin or Staff can admit
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    if not (request.user.is_superuser or is_staff):
        messages.error(request, "Permission Denied. Only Office Staff can admit students.")
        return redirect('home')

    if request.method == 'POST':
        form = StudentAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student admitted successfully! ID: {student.st_id}")
            return redirect('admission')
    else:
        form = StudentAdmissionForm()
    return render(request, 'core/admission.html', {'form': form})

@login_required
def promotion_view(request):
    # Only Teachers (or Admin) can promote
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Permission Denied.")
        return redirect('home')
    
    teacher = getattr(request.user, 'teacher_profile', None)
    
    # Default to teacher's class, or allow selection if Admin
    initial_class = teacher.assigned_class if teacher else 'KG'
    initial_section = teacher.assigned_section if teacher else 'A'

    # Fetch sessions for dropdown (Trigger Reload)
    sessions = Session.objects.all().order_by('-name')
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        target_session_name = request.POST.get('target_session')
        
        # Get target session object or create/fallback (though UI restricts to selection)
        # Requirement: "populate the sessions here in this combo box" - implied existing sessions.
        
        # Logic: Increment Class
        class_order = ['Babyland', 'KG', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        
        promoted_count = 0
        detained_count = 0
        
        # We need to iterate over ALL students currently visible/in this class to handle detention (session update only)
        # But wait, the request is: "students who are not promoted, their session will also modifed but class remains the same."
        # This implies we should process all valid students for this teacher.
        
        if teacher:
            all_students = Student.objects.filter(class_name=teacher.assigned_class, section=teacher.assigned_section, school_branch=teacher.school_branch)
        else:
            # Admin fallback - might need to be more specific in real usage but keeping simple as per current scope
            all_students = Student.objects.all() # Risky for bulk, but consistent with previous 'none' logic if we want to restrict
            if not teacher and not request.user.is_superuser:
                 all_students = Student.objects.none()

        for student in all_students:
            if student.st_id in student_ids:
                # Promote
                try:
                    current_idx = class_order.index(student.class_name)
                    if current_idx < len(class_order) - 1:
                        next_class = class_order[current_idx + 1]
                        student.class_name = next_class
                        student.session_year = target_session_name
                        # Reset attendance for new session? 
                        # Requirement doesn't explicitly say, but usually yes. 
                        # Only modifying explicitly requested fields: class, session_year.
                        student.save()
                        promoted_count += 1
                except ValueError:
                    pass 
            else:
                # Detain / Not Promoted
                # "class remains the same", "session will also modifed"
                student.session_year = target_session_name
                student.save()
                detained_count += 1
        
        if promoted_count > 0 or detained_count > 0:
            messages.success(request, f"Process Complete: {promoted_count} Promoted, {detained_count} Detained/Session Updated.")
            return redirect('home')
        else:
            messages.warning(request, "No changes made.")

    
    # Get students for promotion view
    if teacher:
        students = Student.objects.filter(class_name=teacher.assigned_class, section=teacher.assigned_section, school_branch=teacher.school_branch).order_by('roll_no')
    else:
        students = Student.objects.none() 

    # Calculate overall result for display
    student_list = []
    for student in students:
        # Reuse get_student_report_data logic or simplified version
        # We need the final grade.
        # Let's use a simplified logical block here to avoid circular imports or heavy overhead if creating full PDF data
        
        assigned_subjects = StudentSubject.objects.filter(student=student).values_list('subject', flat=True)
        marks_entries = MarksEntry.objects.filter(student=student, subject__in=assigned_subjects)
        subjects = set(m.subject for m in marks_entries)
        
        grand_total = 0
        count = 0
        
        for subject in subjects:
            m1 = marks_entries.filter(subject=subject, term=1).first()
            m2 = marks_entries.filter(subject=subject, term=2).first()
            
            t1_total = m1.total_marks if m1 else 0
            t2_total = m2.total_marks if m2 else 0
            
            if m1 and m2:
                final_avg = (t1_total + t2_total) / 2
            elif m1:
                final_avg = t1_total
            elif m2:
                final_avg = t2_total
            else:
                final_avg = 0
            
            grand_total += final_avg
            count += 1
            
        overall_avg = grand_total / count if count > 0 else 0
        final_grade = calculate_grade(overall_avg)
        
        student.calculated_grade = final_grade
        student_list.append(student)

    return render(request, 'core/promotion.html', {'students': student_list, 'sessions': sessions})

from .utils import calculate_grade, get_remark
from django.db.models import Avg

@login_required
def generate_report_card(request, student_id):
    student = get_object_or_404(Student, st_id=student_id)
    
    # 1. Fetch Marks only for assigned subjects
    # First get assigned subjects
    assigned_subjects = StudentSubject.objects.filter(student=student).values_list('subject', flat=True)
    
    if assigned_subjects:
        marks_entries = MarksEntry.objects.filter(student=student, subject__in=assigned_subjects)
    else:
        # Fallback: if no subjects assigned, maybe show none or all? 
        # Requirement says "Subject Assignment... now all... displaying", implies we should respect assignment.
        # If empty, shows empty.
        marks_entries = MarksEntry.objects.none()

    subjects = set(m.subject for m in marks_entries)
    
    marks_rows = []
    grand_total = 0
    count = 0
    
    for subject in subjects:
        m1 = marks_entries.filter(subject=subject, term=1).first()
        m2 = marks_entries.filter(subject=subject, term=2).first()
        
        row = {'subject': subject.name, 't1': {}, 't2': {}}
        
        # Term 1 Data
        t1_total = 0
        if m1:
            row['t1']['pt_eff'] = m1.periodic_test / 4.0
            row['t1']['nb'] = m1.notebook
            row['t1']['se'] = m1.subject_enrichment
            row['t1']['exam'] = m1.exam_marks
            t1_total = row['t1']['pt_eff'] + m1.notebook + m1.subject_enrichment + m1.exam_marks
            row['t1']['total'] = t1_total
        
        # Term 2 Data
        t2_total = 0
        if m2:
            row['t2']['pt_eff'] = m2.periodic_test / 4.0
            row['t2']['nb'] = m2.notebook
            row['t2']['se'] = m2.subject_enrichment
            row['t2']['exam'] = m2.exam_marks
            t2_total = row['t2']['pt_eff'] + m2.notebook + m2.subject_enrichment + m2.exam_marks
            row['t2']['total'] = t2_total
        
        # Average
        if m1 and m2:
            final_avg = (t1_total + t2_total) / 2
        elif m1:
            final_avg = t1_total
        elif m2:
            final_avg = t2_total
        else:
            final_avg = 0
            
        row['final_avg'] = final_avg
        row['grade'] = calculate_grade(final_avg)
        
        marks_rows.append(row)
        grand_total += final_avg
        count += 1
    
    # Co-Scholastic Data
    co_scholastic_rows = []
    try:
        co_res = student.co_scholastic_result
        co_scholastic_rows = [
            {'name': 'Work Education', 't1': co_res.work_education_t1, 't2': co_res.work_education_t2},
            {'name': 'Art Education', 't1': co_res.art_education_t1, 't2': co_res.art_education_t2},
            {'name': 'Health & Physical Education', 't1': co_res.health_education_t1, 't2': co_res.health_education_t2},
            {'name': 'Regularity & Punctuality', 't1': co_res.regularity_t1, 't2': co_res.regularity_t2},
            {'name': 'Sincerity', 't1': co_res.sincerity_t1, 't2': co_res.sincerity_t2},
            {'name': 'Behaviour & Values', 't1': co_res.behaviour_t1, 't2': co_res.behaviour_t2},
        ]
    except CoScholasticResult.DoesNotExist:
        # Defaults if not entered
        activities = [
            'Work Education', 'Art Education', 'Health & Physical Education',
            'Regularity & Punctuality', 'Sincerity', 'Behaviour & Values'
        ]
        co_scholastic_rows = [{'name': act, 't1': '', 't2': ''} for act in activities]

    # Calculate additional metrics
    overall_avg = grand_total / count if count > 0 else 0
    final_grade = calculate_grade(overall_avg)
    final_remark = get_remark(final_grade)
    max_marks = count * 100  # Each subject is out of 100
    percentage = (grand_total / max_marks * 100) if max_marks > 0 else 0
    
    # Determine next class based on promotion_status
    class_order = ['KG', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    next_class = "Next Class"

    try:
        current_idx = class_order.index(student.class_name)
    except ValueError:
        current_idx = -1

    if student.promotion_status == 'Promoted':
        if current_idx != -1 and current_idx < len(class_order) - 1:
            next_cls = class_order[current_idx + 1]
            next_class = f"PROMOTED TO CLASS {next_cls}"
        else:
            next_class = "PROMOTED TO NEXT CLASS"
    elif student.promotion_status == 'Detained':
        next_class = f"DETAINED IN CLASS {student.class_name}"
    else:
        # Fallback
        if current_idx != -1 and current_idx < len(class_order) - 1:
            next_class = class_order[current_idx + 1]
        else:
            next_class = "Invalid result"

    # Format attendance
    if student.days_present is not None and student.total_days is not None and student.total_days > 0:
        attendance = f"{student.days_present} / {student.total_days}"
    else:
        attendance = "-"

    context = {
        'student': student,
        'marks_rows': marks_rows,
        'co_scholastic_rows': co_scholastic_rows,
        'grand_total': grand_total,
        'max_marks': max_marks,
        'percentage': percentage,
        'final_grade': final_grade,
        'final_remark': final_remark,
        'next_class': next_class,
        'attendance': attendance,
    }
    
    pdf = render_to_pdf('core/marksheet_pdf.html', context, request=request)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"ReportCard_{student.st_id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF")

# Helper to gather report data
def get_student_report_data(student):
    assigned_subjects = StudentSubject.objects.filter(student=student).values_list('subject', flat=True)
    if assigned_subjects:
        marks_entries = MarksEntry.objects.filter(student=student, subject__in=assigned_subjects)
    else:
        marks_entries = MarksEntry.objects.none()

    subjects = set(m.subject for m in marks_entries)
    marks_rows = []
    grand_total = 0
    count = 0
    
    for subject in subjects:
        m1 = marks_entries.filter(subject=subject, term=1).first()
        m2 = marks_entries.filter(subject=subject, term=2).first()
        row = {'subject': subject.name, 't1': {}, 't2': {}}
        
        # Term 1
        t1_total = 0
        if m1:
            row['t1']['pt_eff'] = m1.periodic_test / 4.0
            row['t1']['nb'] = m1.notebook
            row['t1']['se'] = m1.subject_enrichment
            row['t1']['exam'] = m1.exam_marks
            t1_total = row['t1']['pt_eff'] + m1.notebook + m1.subject_enrichment + m1.exam_marks
            row['t1']['total'] = t1_total
        
        # Term 2
        t2_total = 0
        if m2:
            row['t2']['pt_eff'] = m2.periodic_test / 4.0
            row['t2']['nb'] = m2.notebook
            row['t2']['se'] = m2.subject_enrichment
            row['t2']['exam'] = m2.exam_marks
            t2_total = (row['t2']['pt_eff'] or 0) + m2.notebook + m2.subject_enrichment + m2.exam_marks
            row['t2']['total'] = t2_total
        
        if m1 and m2:
            final_avg = (t1_total + t2_total) / 2
        elif m1:
            final_avg = t1_total
        elif m2:
            final_avg = t2_total
        else:
            final_avg = 0
            
        row['final_avg'] = final_avg
        row['grade'] = calculate_grade(final_avg)
        marks_rows.append(row)
        grand_total += final_avg
        count += 1

    co_scholastic_rows = [
        {'name': 'Work Education', 't1': 'A', 't2': 'A'},
        {'name': 'Art Education', 't1': 'A', 't2': 'A'},
        {'name': 'Health & Physical Education', 't1': 'A', 't2': 'A'},
        {'name': 'Discipline', 't1': 'A', 't2': 'A'},
    ]
    overall_avg = grand_total / count if count > 0 else 0
    final_grade = calculate_grade(overall_avg)
    final_remark = get_remark(final_grade)
    max_marks = count * 100  # Each subject is out of 100
    percentage = (grand_total / max_marks * 100) if max_marks > 0 else 0
    
    # Determine next class based on promotion_status
    class_order = ['KG', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    next_class_display = "Next Class"

    try:
        current_idx = class_order.index(student.class_name)
    except ValueError:
        current_idx = -1

    if student.promotion_status == 'Promoted':
        if current_idx != -1 and current_idx < len(class_order) - 1:
            next_cls = class_order[current_idx + 1]
            next_class_display = f"PROMOTED TO CLASS {next_cls}"
        else:
            next_class_display = "PROMOTED TO NEXT CLASS"
    elif student.promotion_status == 'Detained':
        next_class_display = f"DETAINED IN CLASS {student.class_name}"
    else:
        # Fallback
        if current_idx != -1 and current_idx < len(class_order) - 1:
            next_class_display = class_order[current_idx + 1]
        else:
            next_class_display = "Next Class"

    next_class = next_class_display
    
    # Format attendance
    if student.days_present is not None and student.total_days is not None and student.total_days > 0:
        attendance = f"{student.days_present} / {student.total_days}"
    else:
        attendance = "-"
    
    return {
        'student': student,
        'marks_rows': marks_rows,
        'co_scholastic_rows': co_scholastic_rows,
        'grand_total': grand_total,
        'max_marks': max_marks,
        'percentage': percentage,
        'final_grade': final_grade,
        'final_remark': final_remark,
        'next_class': next_class,
        'attendance': attendance,
    }

@login_required
def teacher_reports_view(request):
    if not (hasattr(request.user, 'teacher_profile') or request.user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('home')
    
    students = Student.objects.none()
    if hasattr(request.user, 'teacher_profile'):
        teacher = request.user.teacher_profile
        students = Student.objects.filter(class_name=teacher.assigned_class, section=teacher.assigned_section)
    elif request.user.is_superuser:
        students = Student.objects.all() # Admin sees all
        
    return render(request, 'core/teacher_reports.html', {'students': students})

@login_required
def bulk_download_reports(request):
    if not (hasattr(request.user, 'teacher_profile') or request.user.is_superuser):
        return redirect('home')
        
    students = Student.objects.none()
    if hasattr(request.user, 'teacher_profile'):
        teacher = request.user.teacher_profile
        students = Student.objects.filter(class_name=teacher.assigned_class, section=teacher.assigned_section)
    elif request.user.is_superuser:
        class_name = request.GET.get('class') # Maybe add filter later for admin
        if class_name:
             students = Student.objects.filter(class_name=class_name)
        else:
             return HttpResponse("Please select a class (Admin functionality WIP)")

    reports_data = []
    for student in students:
        reports_data.append(get_student_report_data(student))
        
    context = {'reports': reports_data}
    pdf = render_to_pdf('core/bulk_marksheet_pdf.html', context, request=request)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Bulk_Report_Cards.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating Bulk PDF")
@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, st_id=student_id)
    # Allow Admin, Staff, and Teachers (to view their students)
    # Teacher restriction check:
    if hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        if not (student.class_name == teacher.assigned_class and 
                student.section == teacher.assigned_section and
                student.school_branch == teacher.school_branch):
             messages.error(request, "Permission Denied.")
             return redirect('home')

    return render(request, 'core/student_detail.html', {'student': student})

@login_required
def student_edit(request, student_id):
    student = get_object_or_404(Student, st_id=student_id)
    
    # Permission Check: Admin, Staff, or Teacher (own class)
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    is_teacher = hasattr(request.user, 'teacher_profile')
    
    allowed = False
    if request.user.is_superuser or is_staff:
        allowed = True
    elif is_teacher:
        teacher = request.user.teacher_profile
        if (student.class_name == teacher.assigned_class and 
            student.section == teacher.assigned_section and
            student.school_branch == teacher.school_branch):
            allowed = True
            
    if not allowed:
        messages.error(request, "Permission Denied.")
        return redirect('home')
    
    if request.method == 'POST':
        form = StudentAdmissionForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.st_id} updated successfully!")
            return redirect('student_detail', student_id=student.st_id)
    else:
        form = StudentAdmissionForm(instance=student)
        
    return render(request, 'core/edit_student.html', {'form': form, 'student': student})

# --- Teacher Management Views ---
from django.contrib.auth.models import User, Group

@login_required
def manage_teachers_view(request):
    # Only Admin or Staff
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    if not (request.user.is_superuser or is_staff):
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    teachers = TeacherProfile.objects.all().select_related('user')
    return render(request, 'core/manage_teachers.html', {'teachers': teachers})

@login_required
def teacher_add_view(request):
    # Only Admin or Staff
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    if not (request.user.is_superuser or is_staff):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    if request.method == 'POST':
        # Simple form handling for now (could be a ModelForm)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        school_branch = request.POST.get('school_branch')
        assigned_class = request.POST.get('assigned_class')
        assigned_section = request.POST.get('assigned_section')
        qualification = request.POST.get('qualification')
        designation = request.POST.get('designation')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            u = User.objects.create_user(username, email, password)
            TeacherProfile.objects.create(
                user=u,
                school_branch=school_branch,
                assigned_class=assigned_class,
                assigned_section=assigned_section,
                qualification=qualification,
                designation=designation
            )
            # Add to group
            g, _ = Group.objects.get_or_create(name='Teachers')
            u.groups.add(g)
            messages.success(request, f"Teacher {username} added successfully.")
            return redirect('manage_teachers')
            
    return render(request, 'core/teacher_form.html', {'action': 'Add', 'available_branches': SchoolBranch.objects.all()})

@login_required
def teacher_edit_view(request, teacher_id):
    # Only Admin or Staff
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    if not (request.user.is_superuser or is_staff):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    profile = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Username update
        if username and username != profile.user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return render(request, 'core/teacher_form.html', {'action': 'Edit', 'profile': profile, 'available_branches': SchoolBranch.objects.all()})
            profile.user.username = username
            profile.user.save()
            
        # Password update
        if password:
            profile.user.set_password(password)
            profile.user.save()

        profile.school_branch = request.POST.get('school_branch')
        profile.assigned_class = request.POST.get('assigned_class')
        profile.assigned_section = request.POST.get('assigned_section')
        profile.qualification = request.POST.get('qualification')
        profile.designation = request.POST.get('designation')
        profile.save()
        messages.success(request, "Teacher updated.")
        return redirect('manage_teachers')

    return render(request, 'core/teacher_form.html', {'action': 'Edit', 'profile': profile, 'available_branches': SchoolBranch.objects.all()})

@login_required
def teacher_delete_view(request, teacher_id):
    # Only Admin or Staff with permission
    is_staff = hasattr(request.user, 'staff_profile') or request.user.groups.filter(name='Office Staff').exists()
    if not (request.user.is_superuser or is_staff):
        messages.error(request, "Permission Denied.")
        return redirect('home')

    profile = get_object_or_404(TeacherProfile, id=teacher_id)
    user = profile.user
    
    # Optional: Prevent deleting yourself if you are a teacher (though usually admins do this)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_teachers')

    # Deleting the user will cascade delete the profile
    user.delete()
    messages.success(request, f"Teacher {user.username} deleted.")
    return redirect('manage_teachers')

@login_required
def download_student_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'
    
    writer = csv.writer(response)
    # Headers based on Student model
    headers = [
        'student_name', 'fathers_name', 'mothers_name', 'dob (YYYY-MM-DD)', 'sex (M/F)', 
        'class_name', 'section', 'roll_no', 'school_branch', 'adm_date (YYYY-MM-DD)', 
        'session_year', 'contact_1', 'address', 'student_aadhaar', 'fathers_aadhaar'
    ]
    writer.writerow(headers)
    return response

@login_required
def upload_student_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('home')
        
        file_data = csv_file.read().decode('utf-8')
        csv_data = io.StringIO(file_data)
        reader = csv.DictReader(csv_data)
        
        count = 0
        errors = 0
        
        for row in reader:
            try:
                # Basic validation and cleaning
                dob = datetime.strptime(row.get('dob (YYYY-MM-DD)', ''), '%Y-%m-%d').date()
                adm_date = datetime.strptime(row.get('adm_date (YYYY-MM-DD)', ''), '%Y-%m-%d').date()
                
                student = Student(
                    student_name=row.get('student_name'),
                    fathers_name=row.get('fathers_name'),
                    mothers_name=row.get('mothers_name'),
                    dob=dob,
                    sex=row.get('sex (M/F)'),
                    class_name=row.get('class_name'),
                    section=row.get('section'),
                    roll_no=row.get('roll_no') if row.get('roll_no') else None,
                    school_branch=row.get('school_branch'),
                    adm_date=adm_date,
                    session_year=row.get('session_year'),
                    contact_1=row.get('contact_1'),
                    address=row.get('address'),
                    student_aadhaar=row.get('student_aadhaar'),
                    fathers_aadhaar=row.get('fathers_aadhaar')
                )
                student.save() # st_id is auto-generated
                count += 1
            except Exception as e:
                errors += 1
                print(f"Error importing row: {e}")
                
        if errors > 0:
            messages.warning(request, f"Imported {count} students. {errors} rows failed (check date formats).")
        else:
            messages.success(request, f"Successfully imported {count} students.")
            
    return redirect('home')

@login_required
def database_backup_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{db_name}_{timestamp}.sql"
    
    # mysqldump command
    command = f"mysqldump -h {db_host} -u {db_user} -p'{db_password}' {db_name}"
    
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode != 0:
            messages.error(request, f"Backup failed: {error.decode('utf-8')}")
            return redirect('home')
            
        response = HttpResponse(output, content_type='application/sql')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')

@login_required
def database_restore_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    if request.method == 'POST' and request.FILES.get('sql_file'):
        sql_file = request.FILES['sql_file']
        
        if not sql_file.name.endswith('.sql'):
            messages.error(request, "Please upload a SQL file.")
            return redirect('home')
            
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        
        temp_path = f"/tmp/{sql_file.name}"
        with open(temp_path, 'wb+') as destination:
            for chunk in sql_file.chunks():
                destination.write(chunk)
                
        command = f"mysql -h {db_host} -u {db_user} -p'{db_password}' {db_name} < {temp_path}"
        
        try:
            exit_code = os.system(command)
            
            if exit_code == 0:
                messages.success(request, "Database restored successfully.")
            else:
                messages.error(request, "Restore failed. Check logs.")
                
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            
    return redirect('home')



@login_required
def manage_branches_view(request):
    # Only Admin
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    branches = SchoolBranch.objects.all()
    return render(request, 'core/manage_branches.html', {'branches': branches})

@login_required
def branch_add_view(request):
    # Only Admin
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        
        if SchoolBranch.objects.filter(name=name).exists():
             messages.error(request, "Branch already exists.")
        else:
             SchoolBranch.objects.create(name=name, address=address)
             messages.success(request, "Branch added.")
             return redirect('manage_branches')
             
    return render(request, 'core/branch_form.html', {'action': 'Add'})

@login_required
def branch_edit_view(request, branch_id):
    # Only Admin
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
    
    branch = get_object_or_404(SchoolBranch, id=branch_id)
    if request.method == 'POST':
        branch.name = request.POST.get('name')
        branch.address = request.POST.get('address')
        branch.save()
        messages.success(request, "Branch updated.")
        return redirect('manage_branches')
        
    return render(request, 'core/branch_form.html', {'action': 'Edit', 'branch': branch})

@login_required
def branch_delete_view(request, branch_id):
    # Only Admin
    if not request.user.is_superuser:
        messages.error(request, "Permission Denied.")
        return redirect('home')
    
    branch = get_object_or_404(SchoolBranch, id=branch_id)
    branch.delete()
    messages.success(request, "Branch deleted.")
    return redirect('manage_branches')

from django.core.management.base import BaseCommand
from core.models import Student, Subject, StudentSubject
from core.views import CLASS_SUBJECT_MAPPING

class Command(BaseCommand):
    help = 'Assigns default subjects to students based on their class'

    def handle(self, *args, **options):
        # Create subjects if they don't exist
        all_subjects = set()
        for subjects in CLASS_SUBJECT_MAPPING.values():
            all_subjects.update(subjects)
        
        # Add class 11/12 specific subjects if not in mapping (though not auto-assigned)
        elective_subjects = [
            'Physics', 'Accountancy', 'Political Science', 
            'Biology', 'Economics', 'Geography', 'Psychology', 
            'Informatics Practices', 'Computer Science', 'Chemistry', 
            'Business Studies', 'Sociology', 'Physical Education'
        ]
        all_subjects.update(elective_subjects)

        for subj_name in all_subjects:
            Subject.objects.get_or_create(name=subj_name)

        self.stdout.write(self.style.SUCCESS(f'Ensured {len(all_subjects)} subjects exist in database.'))

        # assign subjects
        students = Student.objects.all()
        count = 0
        
        for student in students:
            if student.class_name in CLASS_SUBJECT_MAPPING:
                subjects_to_assign = CLASS_SUBJECT_MAPPING[student.class_name]
                
                # Assign each
                for subj_name in subjects_to_assign:
                    subject = Subject.objects.get(name=subj_name)
                    _, created = StudentSubject.objects.get_or_create(
                        student=student, 
                        subject=subject
                    )
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Processed {count} students. Skpped Class 11/12 (manual assignment required).'))

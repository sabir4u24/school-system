from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Choices
SEX_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
STREAM_CHOICES = [('Science', 'Science'), ('Commerce', 'Commerce'), ('Humanities', 'Humanities'), ('None', 'None')]
CLASS_CHOICES = [
    ('Babyland', 'Babyland'), ('KG', 'KG'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
    ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
    ('11', '11'), ('12', '12')
]
SECTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]



class Session(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2025-2026")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class SchoolBranch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    st_id = models.CharField(primary_key=True, max_length=20, editable=False)
    cbse_reg = models.CharField(max_length=50, blank=True, null=True)
    adm_date = models.DateField()
    session_year = models.CharField(max_length=20, help_text="e.g. 2024-2025")
    school_branch = models.CharField(max_length=100)
    stream = models.CharField(max_length=20, choices=STREAM_CHOICES, default='None', blank=True)
    class_name = models.CharField(max_length=10, choices=CLASS_CHOICES)
    section = models.CharField(max_length=5, choices=SECTION_CHOICES)
    roll_no = models.IntegerField(blank=True, null=True)
    student_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    dob = models.DateField()
    student_aadhaar = models.CharField(max_length=20, blank=True, null=True)
    fathers_name = models.CharField(max_length=100)
    fathers_aadhaar = models.CharField(max_length=20, blank=True, null=True)
    mothers_name = models.CharField(max_length=100, blank=True, null=True)
    mothers_aadhaar = models.CharField(max_length=20, blank=True, null=True)
    contact_1 = models.CharField(max_length=15)
    contact_2 = models.CharField(max_length=15, blank=True, null=True)
    contact_3 = models.CharField(max_length=15, blank=True, null=True)
    contact_4 = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    parent_occupation = models.CharField(max_length=100, blank=True, null=True)
    parent_occupation = models.CharField(max_length=100, blank=True, null=True)
    sibling_st_id = models.CharField(max_length=20, blank=True, null=True)
    
    # Attendance tracking
    days_present = models.IntegerField(blank=True, null=True, default=0, help_text="Number of days student attended")
    total_days = models.IntegerField(blank=True, null=True, default=0, help_text="Total school days for the session")
    
    # Promotion Status
    promotion_status = models.CharField(max_length=20, choices=[('Promoted', 'Promoted'), ('Detained', 'Detained')], blank=True, null=True)
    
    student_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.st_id:
            last = Student.objects.order_by('-st_id').first()
            if last:
                try:
                    # Strip H and convert, e.g. H100001 -> 100001
                    num = int(last.st_id[1:]) + 1
                    self.st_id = f'H{num}'
                except ValueError:
                    self.st_id = 'H100001' # Fallback
            else:
                self.st_id = 'H100001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.st_id} - {self.student_name}"

class Subject(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, blank=True, null=True)
    is_optional = models.BooleanField(default=False, help_text="True for Cls 11/12 electives")
    
    def __str__(self):
        return self.name

class StudentSubject(models.Model):
    """Mapping student to subjects, especially for Class 11/12"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'subject')

class MarksEntry(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.IntegerField(choices=[(1, 'Term 1'), (2, 'Term 2')])
    
    # Marks Breakdown
    periodic_test = models.FloatField(default=0, validators=[MaxValueValidator(40)], help_text="Max 40")
    notebook = models.FloatField(default=5, validators=[MaxValueValidator(5)], help_text="Max 5")
    subject_enrichment = models.FloatField(default=5, validators=[MaxValueValidator(5)], help_text="Max 5")
    exam_marks = models.FloatField(default=0, validators=[MaxValueValidator(80)], help_text="Half Yearly/Yearly Max 80")

    class Meta:
        unique_together = ('student', 'subject', 'term')
        verbose_name_plural = "Marks Entries"

    @property
    def total_marks(self):
        # Calculation: (PT/4) which is effectively (PT/40)*10 + Notebook + Enrichment + Exam
        # Requirement: "The marks of Periodic Test-1 is divided by 4 and it is taken as 10 marks"
        pt_weight = self.periodic_test / 4.0
        return pt_weight + self.notebook + self.subject_enrichment + self.exam_marks

class CoScholasticResult(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='co_scholastic_result')
    
    # Activity 1: Work Education
    work_education_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    work_education_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    
    # Activity 2: Art Education
    art_education_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    art_education_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    
    # Activity 3: Health & Physical Education
    health_education_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    health_education_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    
    # Activity 4: Regularity & Punctuality
    regularity_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    regularity_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    
    # Activity 5: Sincerity
    sincerity_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    sincerity_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    
    # Activity 6: Behaviour & Values
    behaviour_t1 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])
    behaviour_t2 = models.CharField(max_length=2, default='A', choices=[('A','A'), ('B','B'), ('C','C')])

    def __str__(self):
        return f"Co-Scholastic: {self.student.student_name}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    school_branch = models.CharField(max_length=100, blank=True, null=True, help_text="Branch assignment")
    assigned_class = models.CharField(max_length=10, choices=CLASS_CHOICES, blank=True, null=True)
    assigned_section = models.CharField(max_length=5, choices=SECTION_CHOICES, blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        branch_info = f" ({self.school_branch})" if self.school_branch else ""
        return f"{self.user.username} - {self.assigned_class} {self.assigned_section}{branch_info}"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    qualification = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username

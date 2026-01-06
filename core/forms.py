from django import forms
from .models import Student, Subject, SchoolBranch

class StudentAdmissionForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['st_id'] # Auto-generated
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'adm_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'session_year': forms.TextInput(attrs={'placeholder': '2024-2025'}),
            'stream': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'contact_1': 'Primary Contact 1',
            'contact_2': 'Primary Contact 2',
            'contact_3': 'Secondary Contact 1',
            'contact_4': 'Secondary Contact 2',
            'sibling_st_id': 'Sibling Student ID',
            'student_aadhaar': 'Student Aadhaar No',
            'fathers_aadhaar': 'Father Aadhaar No',
            'mothers_aadhaar': 'Mother Aadhaar No',
            'state': 'State',
            'city': 'City',
            'pin': 'PIN Code',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    school_branch = forms.ModelChoiceField(
        queryset=SchoolBranch.objects.all(),
        to_field_name='name',
        empty_label="Select Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class SubjectAssignmentForm(forms.Form):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class AttendanceSettingsForm(forms.Form):
    """Form for teachers to set total attendance days for their class"""
    total_days = forms.IntegerField(
        min_value=0,
        max_value=365,
        label="Total School Days",
        help_text="Set the total number of school days for this session",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 200'})
    )

class StudentAttendanceForm(forms.ModelForm):
    """Form for entering individual student attendance"""
    class Meta:
        model = Student
        fields = ['days_present']
        widgets = {
            'days_present': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


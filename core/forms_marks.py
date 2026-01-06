from django import forms
from django.forms import modelformset_factory
from .models import MarksEntry, Student, Subject, CoScholasticResult

class MarksSelectionForm(forms.Form):
    CLASS_CHOICES = [
        ('KG', 'KG'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
        ('11', '11'), ('12', '12')
    ]
    SECTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]
    TERM_CHOICES = [(1, 'Term 1'), (2, 'Term 2')]

    class_name = forms.ChoiceField(choices=CLASS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    section = forms.ChoiceField(choices=SECTION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    term = forms.ChoiceField(choices=TERM_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        teacher_profile = kwargs.pop('teacher_profile', None)
        allowed_subjects = kwargs.pop('allowed_subjects', None)
        super(MarksSelectionForm, self).__init__(*args, **kwargs)
        
        if teacher_profile:
            # Lock Class and Section
            self.fields['class_name'].initial = teacher_profile.assigned_class
            self.fields['class_name'].widget = forms.HiddenInput()
            self.fields['section'].initial = teacher_profile.assigned_section
            self.fields['section'].widget = forms.HiddenInput()
            
        if allowed_subjects is not None:
             self.fields['subject'].queryset = allowed_subjects

MarksEntryFormSet = modelformset_factory(
    MarksEntry,
    fields=('periodic_test', 'notebook', 'subject_enrichment', 'exam_marks'),
    extra=0,
    can_delete=False,
    widgets={
        'periodic_test': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'style': 'width: 80px'}),
        'notebook': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'style': 'width: 80px'}),
        'subject_enrichment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'style': 'width: 80px'}),
        'exam_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'style': 'width: 80px'}),
    }
)

class CoScholasticEntryForm(forms.ModelForm):
    class Meta:
        model = CoScholasticResult
        exclude = ['student']
        widgets = {
            # T1 Widgets
            'work_education_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'art_education_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'health_education_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'regularity_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'sincerity_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'behaviour_t1': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),

            # T2 Widgets
            'work_education_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'art_education_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'health_education_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'regularity_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'sincerity_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'behaviour_t2': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}),
        }

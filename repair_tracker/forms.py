from django import forms
from .models import Repair

class RepairForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = [
            'device_name','device_DAM_ID', 'device_serial',
            'student_name', 'student_id', 'student_grade','student_email','student_school',
            'issue_description', 'resolution_notes','service_now_inc_number',
            'status', 'loaner', 'assigned_to',
            'contains_student_data', 'third_party_access', 
            'consent_on_file', 
            'sent_to_dell_check','dell_service_number', 'submitted_under',
            'vineetha_checked', 'vineetha_repair_comments','vineetha_closed',
        ]
        widgets = {
            'service_now_inc_number' : forms.Textarea(attrs={
                'class' : 'form-control',
                'rows' : 1,
                'style' : 'width : 300px; display: inline-block; vertical-align: middle;',
                }),
             'submitted_under' : forms.Textarea(attrs={
                'class' : 'form-control',
                'rows' : 1,
                'style' : 'width : 300px; display: inline-block; vertical-align: middle;',
                }),
            'dell_service_number': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width: 300px;',
                'placeholder': 'e.g. SVC-ABC123',
                }),
            'issue_description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,  # This sets the height by number of lines
                }),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows' : 4,
                }),
            'student_email': forms.Textarea(attrs={
                'class': 'form-control',
                'rows' : 1,
                'style' : 'width: 400px',

                }),
            'vineetha_repair_comments': forms.Textarea(attrs={
                'class': 'form-conrtol',
                'rows' : 1,
                'style': 'width: 500px',
                }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
    
    # Remove student info fields if user lacks permission
        if user and not user.has_perm('repair_tracker.view_student_info'):
            del self.fields['student_name']
            del self.fields['student_id']
            del self.fields['student_grade']
            del self.fields['student_school']
        if user and not user.is_superuser:
            del self.fields['vineetha_checked']
            del self.fields['vineetha_closed']
            del self.fields['vineetha_repair_comments']



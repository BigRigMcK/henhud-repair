from django import forms
from .models import Repair, RepairNote
from django.contrib.auth.forms import AuthenticationForm

#'student_name', 'student_id', 'student_grade','student_email','student_school',

class RepairForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = [
            'device_name','device_DAM_ID', 'device_serial',
            'district_member',
            'issue_description', 'resolution_notes','service_now_inc_number',
            'status', 'loaner', 'assigned_to',
            'contains_student_data', 'third_party_access', 
            'consent_on_file', 
            'sent_to_dell_check','dell_service_number', 'submitted_under',
            'vineetha_checked', 'vineetha_repair_comments','vineetha_closed',
        ]
        widgets = {
            'service_now_inc_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. INC0012345',
            }),
            'submitted_under': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Requesting account',
            }),
            'dell_service_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. SVC-ABC123',
            }),
            'issue_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the issue in detail…',
            }),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'What was done to resolve?',
            }),
            'vineetha_repair_comments': forms.Textarea(attrs={
                'class': 'form-control',   # fixed typo: was 'form-conrtol'
                'rows': 2,
            }),
            'device_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'device_DAM_ID': forms.TextInput(attrs={'class': 'form-control'}),
            'device_serial': forms.TextInput(attrs={'class': 'form-control'}),
            'status':        forms.Select(attrs={'class': 'form-select'}),
            'assigned_to':   forms.Select(attrs={'class': 'form-select'}),
            'loaner':        forms.Select(attrs={'class': 'form-select'}),
            'vineetha_checked':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vineetha_closed':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sent_to_dell_check':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contains_student_data': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'third_party_access':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'consent_on_file':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district_member'].widget = forms.HiddenInput()
        self.fields['district_member'].required = False
    
    # Remove student info fields if user lacks permission
        if user and not user.has_perm('repair_tracker.view_student_info'):
            del self.fields['district_member']
        if user and not user.is_superuser:
            del self.fields['vineetha_checked']
            del self.fields['vineetha_closed']
            del self.fields['vineetha_repair_comments']


from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'autocomplete': 'username',
        'class': 'form-control', # Optional: for styling
        'placeholder': 'Username',
        'id': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'autocomplete': 'current-password',
        'class': 'form-control',
        'placeholder': 'Password',
        'id' : 'password',
    }))

class RepairNoteForm(forms.ModelForm):
    class Meta:
        model = RepairNote
        fields = ['note_type', 'note']
        widgets = {
            'note_type': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'What did you do? What did you find?',
            }),
        }
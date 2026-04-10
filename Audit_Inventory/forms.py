from django import forms
from .models import District_Device_Audit, Individual_AuditDevice

class AuditForm(forms.ModelForm):
    class Meta:
        model = District_Device_Audit
        fields = ['location', 'auditor', 'notes', 'devices']
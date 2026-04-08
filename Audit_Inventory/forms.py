from django import forms
from .models import Audit, AuditDevice

class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['location', 'auditor', 'notes']
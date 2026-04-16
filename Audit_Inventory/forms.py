from django import forms
from .models import District_Device_Audit, Individual_AuditDevice


class StartAuditForm(forms.ModelForm):
    """
    Shown before a new audit begins — lets the tech add optional notes
    before the session starts. Location and auditor are set in the view,
    not by the user, so they are excluded here.
    """
    class Meta:
        model = District_Device_Audit
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: describe the scope or purpose of this audit…',
            }),
        }
        labels = {
            'notes': 'Audit Notes (optional)',
        }


class IndividualAuditDeviceForm(forms.ModelForm):
    """
    Inline form for a single device row on the perform_audit page.
    Only exposes the fields a tech can change during an audit.
    The audit and device FKs are set by the view/formset, not the user.
    """
    class Meta:
        model = Individual_AuditDevice
        fields = ['found', 'notes']
        widgets = {
            'found': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'transform: scale(1.4);',
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Optional note…',
            }),
        }
        labels = {
            'found': '',   # Label rendered manually in the template
            'notes': '',
        }


# Formset for processing all device rows in one POST
IndividualAuditDeviceFormSet = forms.modelformset_factory(
    Individual_AuditDevice,
    form=IndividualAuditDeviceForm,
    extra=0,       # No blank rows — rows are created by start_audit view
    can_delete=False,
)


class CompleteAuditForm(forms.ModelForm):
    """
    Used on the 'Mark Complete' confirmation step.
    Allows the tech to add or update notes before closing the audit.
    is_complete and completed_at are set in the view via audit.complete().
    """
    class Meta:
        model = District_Device_Audit
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Final notes for this audit (missing devices, discrepancies, etc.)…',
            }),
        }
        labels = {
            'notes': 'Closing Notes (optional)',
        }
from django.db import models
from Inventory.models import *
# Create your models here.

from django.db import models
from Inventory.models import District_Device_Inventory  # Import from the other app

class District_Device_Audit(models.Model):
    audit_date = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255)          # or ForeignKey to a Location model
    auditor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    # Many-to-many relationship with extra data
    devices = models.ManyToManyField(
        'Inventory.District_Device_Inventory',
        through='Individual_AuditDevice',
        related_name='audits'
    )

    class Meta:
        ordering = ['-audit_date']

    def __str__(self):
        return f"Audit {self.id} - {self.location} ({self.audit_date.date()})"


class Individual_AuditDevice(models.Model):
    """This is the key model that expresses "this device was found in this audit" """
    audit = models.ForeignKey(District_Device_Audit, on_delete=models.CASCADE)
    device = models.ForeignKey('Inventory.District_Device_Inventory', on_delete=models.CASCADE)
    
    found = models.BooleanField(default=False)          # ← Checkbox value
    notes = models.TextField(blank=True, null=True)     # Optional per-device notes
    found_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('audit', 'device')   # Prevent duplicate entries
        ordering = ['device']             # or whatever field you use

    def __str__(self):
        status = "✓ Found" if self.found else "✗ Missing"
        return f"{self.device} - {status} in Audit {self.audit.id}"

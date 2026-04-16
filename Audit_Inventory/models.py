from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from Inventory.models import District_Device_Inventory


class District_Device_Audit(models.Model):
    """
    One record per audit session per location.
    A new record is created each time an audit is started —
    history is preserved so you can compare audits over time.
    """
    location = models.ForeignKey(
        'Base_Models.District_Location',
        on_delete=models.PROTECT,
        related_name='audits',
    )
    auditor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audits_performed',
    )
    notes = models.TextField(blank=True)

    # Lifecycle
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)



    # Many-to-many through Individual_AuditDevice (no redundant M2M field)
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Device Audit"
        verbose_name_plural = "Device Audits"

    def __str__(self):
        status = "✓ Complete" if self.is_complete else "In Progress"
        return f"Audit #{self.id} — {self.location} ({self.started_at.date()}) [{status}]"

    def complete(self):
        """Mark this audit as finished."""
        self.is_complete = True
        self.completed_at = timezone.now()
        self.save()

    # ── Summary helpers ──────────────────────────────────────────────────────

    def total_devices(self):
        return self.audit_devices.count()

    def found_count(self):
        return self.audit_devices.filter(found=True).count()

    def missing_count(self):
        return self.audit_devices.filter(found=False).count()

    def completion_percentage(self):
        total = self.total_devices()
        if total == 0:
            return 0
        return round((self.found_count() / total) * 100)


class Individual_AuditDevice(models.Model):
    """
    One row per device per audit session.
    Preserves whether the device was found, when, and any notes.
    The 'found_at' timestamp doubles as "last seen" when surfaced on the device.
    """
    audit = models.ForeignKey(
        District_Device_Audit,
        on_delete=models.CASCADE,
        related_name='audit_devices',
    )
    device = models.ForeignKey(
        District_Device_Inventory,
        on_delete=models.CASCADE,
        related_name='audit_records',
    )

    found = models.BooleanField(default=False)
    found_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('audit', 'device')
        ordering = ['device__asset_name']
        verbose_name = "Audit Device Record"
        verbose_name_plural = "Audit Device Records"

    def __str__(self):
        status = "✓ Found" if self.found else "✗ Missing"
        return f"{self.device} — {status} in Audit #{self.audit.id}"

    def mark_found(self):
        """Mark as found and record the timestamp."""
        self.found = True
        self.found_at = timezone.now()
        self.save()
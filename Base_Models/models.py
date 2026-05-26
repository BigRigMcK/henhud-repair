from django.db import models
from repair_tracker.audit_models import AuditLog
from django.contrib.contenttypes.fields import GenericRelation # Add this





class District_Location(models.Model):
    school = models.CharField(max_length=50)
    room = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "District Locations"
        ordering = ['school', 'room']

    audit_logs = GenericRelation(AuditLog)
    def __str__(self):
        return f"{self.school} - {self.room}"
	
class District_Department(models.Model):
    department = models.CharField(max_length=100)

    audit_logs = GenericRelation(AuditLog)
    class Meta:
        verbose_name_plural = "District Departments"
        
        ordering = ['department']

    def __str__(self):
        return self.department


# Base_Models/models.py — better pattern
class Current_Device_Status(models.Model):

    class StatusChoices(models.TextChoices):
        ASSIGN = 'ASSIGN', 'Assign Device Status'
        IN_USE = 'IN_USE', 'In Use'
        IN_STORAGE = 'IN_STORAGE', 'In Storage'
        MISSING = 'MISSING', 'Missing'
        BEING_REPAIRED = 'BEING_REPAIRED', 'Being Repaired'
        DISPOSED = 'DISPOSED', 'Disposed-End of Life'
        LOST_PENDING = 'LOST_PENDING', 'Lost/Stolen-Pending Payment'
        LOST_PAID = 'LOST_PAID', 'Lost/Stolen-Paid'

    Status = models.CharField(
        max_length=40,
        choices=StatusChoices.choices,
        
        unique=True,
    )
    class Meta:
        verbose_name = "Device Status"
        verbose_name_plural = "Device Statuses"
        ordering = ['Status']

    def __str__(self):
        # get_Status_display() returns the human label ("In Use")
        # rather than the stored key ("IN_USE").
        return self.get_Status_display()
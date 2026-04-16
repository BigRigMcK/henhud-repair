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


class Current_Status(models.Model):
	Status= models.CharField(max_length=50)
	class Meta:
		verbose_name_plural = "Device Statuses"
		ordering = ['Status']

	def __str__(self):
		return f"{self.Status}"
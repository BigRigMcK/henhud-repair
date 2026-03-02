#Audit Context
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AuditLog(models.Model):
    """Track all access to student data for FERPA compliance"""
    
    ACTION_CHOICES = [
        ('VIEW', 'Viewed Record'),
        ('CREATE', 'Created Record'),
        ('UPDATE', 'Updated Record'),
        ('DELETE', 'Deleted Record'),
        ('EXPORT', 'Exported Data'),
        ('PRINT', 'Printed Record'),
        ('SEARCH', 'Searched Records'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('PERMISSION_DENIED', 'Permission Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # What was accessed
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=200, blank=True)
    
    # Details
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # FERPA specific
    justification = models.TextField(blank=True, help_text="Reason for accessing student data")
    legitimate_educational_interest = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"


class ConsentRecord(models.Model):
    """Track parent/student consent for data disclosure"""
    
    student_identifier = models.CharField(max_length=200, unique=True)
    parent_name = models.CharField(max_length=200)
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateField(null=True, blank=True)
    consent_scope = models.TextField(help_text="What the consent covers")
    expiration_date = models.DateField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    revoked_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student_identifier} - Consent: {self.consent_given}"
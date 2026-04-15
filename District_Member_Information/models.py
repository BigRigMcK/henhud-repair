from django.db import models
from django_cryptography.fields import encrypt
from django.contrib.auth.models import User


class District_Member(models.Model):
    GRADE_CHOICES = [
        ('K', 'Kindergarten'), ('1', '1st'), ('2', '2nd'), ('3', '3rd'),
        ('4', '4th'), ('5', '5th'), ('6', '6th'), ('7', '7th'),
        ('8', '8th'), ('9', '9th'), ('10', '10th'), ('11', '11th'),
        ('12', '12th'), ('STAFF', 'Staff'),
    ]
    BUILDING_CHOICES = [
        ('BMMS', "Blue Mountain Middle School"),
        ('BV', "Buchanan-Verplanck Elementary School"),
        ('FGL', 'Frank G. Lindsey'),
        ('FW', 'Furnace Woods'),
        ('HHHS', 'Hendrick Hudson High School'),
        ('DO', 'District Office'),
        ('BUSG', 'Bus Garage'),
        ('MAITG', 'Maintainance Garage'),
        # ... add the rest of your schools
    ]

    # All FERPA fields encrypted
    district_member_name = encrypt(models.CharField(max_length=200, blank=True, default="Please Update ID"))
    district_member_id = encrypt(models.CharField(max_length=50, blank=True, unique=True, default="Please Update Name"))
    district_member_email = encrypt(models.EmailField(blank=True, default="@students.henhudschools.org"))
    district_member_grade = models.CharField(max_length=10, blank=True, choices=GRADE_CHOICES,default="Please Update Grade")
    district_member_building = models.CharField(max_length=25, blank=True, choices=BUILDING_CHOICES, default="Please Update Building"),

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "District Member"
        verbose_name_plural = "District Members"
        permissions = [
            ("view_student_pii", "Can view student PII (FERPA protected)"),
        ]

    def __str__(self):
        return f"Student #{self.district_member_id}"  # Never expose name in __str__ (audit safety)

    def get_audit_representation(self):
        return f"Student Record #{self.district_member_id} - Grade: {self.district_member_grade} - Building: {self.district_member_building}"


class District_Member_DeviceAssignment(models.Model):
    district_member = models.ForeignKey(
        District_Member,
        on_delete=models.PROTECT,
        related_name='device_assignments'
    )
    device = models.ForeignKey(
        'Inventory.District_Device_Inventory',
        on_delete=models.PROTECT,
        related_name='student_assignments'
    )
    repair = models.ForeignKey(
        'repair_tracker.Repair',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_assignments'
    )
    assigned_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='device_assignments_made'
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Student Device Assignment"
        verbose_name_plural = "Student Device Assignments"
        ordering = ['-assigned_date']

    def __str__(self):
        return f"Assignment #{self.pk} - Device: {self.device} - District Member: {self.district_member}"

    def is_active(self):
        return self.returned_date is None# Create your models here.
        

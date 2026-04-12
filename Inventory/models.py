from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
# Assuming these imports are correct based on your file structure
#from Base_Models.base_models import Current_Status 
from django.contrib.contenttypes.fields import GenericRelation # Add this
from repair_tracker.audit_models import AuditLog # Add this
from django_cryptography.fields import encrypt
class Device_Model(models.Model):
    Model_Type = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return f"{self.Model_Type}"
    class Meta:
        verbose_name = "Device Model"
        verbose_name_plural = "Device Models"

class District_Location(models.Model):
    school = models.CharField(max_length=50)
    room = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "District Locations"

    audit_logs = GenericRelation(AuditLog)
    def __str__(self):
        return f"{self.school} - {self.room}"
	
class District_Department(models.Model):
    department = models.CharField(max_length=100)

    audit_logs = GenericRelation(AuditLog)
    class Meta:
        verbose_name_plural = "District Departments"

    def __str__(self):
        return self.department


class District_Device_Inventory(models.Model):
    asset_name = models.CharField(max_length=50)
    asset_id = models.IntegerField(validators=[MinValueValidator(0)])
    serial_number = models.CharField(max_length=30, null=True, blank=True)
    
    # Corrected ForeignKey logic
    # Note: default=1 assumes a record with ID 1 exists. 
    # If not sure, use on_delete=models.SET_NULL and null=True.
    current_status = models.ForeignKey(
        'Base_Models.Current_Status', 
        on_delete=models.SET_DEFAULT,
        default=0,
        null=True, 
    )
    location = models.ForeignKey(
        District_Location, 
        on_delete=models.PROTECT,
        null=True
        
    
    )
    department = models.ForeignKey(
        District_Department, 
        on_delete=models.PROTECT,
        null=True,
    )
    
    # Use underscores for variable names, never spaces
    mac_address = models.CharField(max_length=20, blank=True, null=True)
    capacity_hard_drive_size = models.CharField(max_length=50, blank=True)
    manufacture_make = models.CharField(max_length=50, blank=True, null=True)
    
    model_type = models.ForeignKey(
        Device_Model, 
        on_delete=models.SET_DEFAULT,
        null=True,
        default=0,
         
    )
    
    vendor = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(blank=True)
    source_of_funding = models.CharField(max_length=50, blank=True, null=True)
    po_order = models.CharField(max_length=50, blank=True, null=True)
    purchase_value = models.CharField(max_length=50, blank=True, null=True, default="$")
    student_id_number = models.IntegerField(blank=True, null=True)
    student_id_number_encrypted = encrypt(models.CharField(max_length=50, blank=True, null=True, default="$"))
    audit_logs = GenericRelation(AuditLog)

    class Meta:
		#verbose_name = "District Device Inventory"
        verbose_name_plural = "District Device Inventory"

    def __str__(self):
        return self.asset_name

    def get_audit_representation(self):
        return f"{self.asset_name} (Asset ID: {self.asset_id} | Serial: {self.serial_number or 'N/A'})"

# Simple Audit Log Model
class Asset_History(models.Model):
    asset = models.ForeignKey(District_Device_Inventory, on_delete=models.CASCADE, related_name='history')
    change_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    changed_by = models.CharField(max_length=100) # Or link to User model


class Classroom_Device_Purpose(models.Model):
        name = models.CharField(max_length=100, unique=True)

        def __str__(self):
            return self.name
        class Meta:
            verbose_name = "Classroom Device Purpose"
            verbose_name_plural = "Classroom Device Purposes"
            ordering = ['name']



class ClassroomDevices(models.Model):
    classroom = models.CharField(max_length=50, blank=True)
    # classroom_device_model = models.ForeignKey(
    #     Device_Model,
    #     on_delete=models.PROTECT,
    #     related_name='devices'
    #     )
    classroom_dam_id = models.CharField(max_length=50, blank=True, null=True)
    classroom_device_serial_number = models.CharField(blank=True,null=True)
    classroom_device_checkout = models.DateTimeField(blank=True, null=True)
    classroom_device_checkin = models.DateTimeField(blank=True, null=True)
    classroom_device_purpose = models.ForeignKey(
        Classroom_Device_Purpose,
        on_delete=models.PROTECT,  # Prevents deleting a purpose that is in use
        related_name='devices'
        )
    classroom_teacher = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return f" {self.classroom_device_purpose} - {self.classroom} - {self.classroom_device_serial_number}"

    class Meta:
        verbose_name = "Classroom Device"
        verbose_name_plural = "Classroom Devices"
        ordering = ['classroom_device_purpose']


class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



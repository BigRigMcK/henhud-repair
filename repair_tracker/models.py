# Updated models.py with Loaner Checkout History Tracking

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django_cryptography.fields import encrypt



class Device_Model(models.Model):
    Model_Type = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return f"{self.Model_Type}"
    class Meta:
        verbose_name = "Device Model"
        verbose_name_plural = "Device Models"

# class Device_Current_Status(models.Model):

# class District_Location(models.Model):

# class District_Department(models.Model):

class Repair(models.Model):
    # Device information
    device_name = models.CharField(max_length=200, null=True, blank=True)
    device_DAM_ID = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    device_serial = models.CharField(max_length=20, default="")
    
    # Student information (ENCRYPTED for FERPA compliance)
    student_name = encrypt(models.CharField(max_length=200, blank=True))
    student_id = encrypt(models.CharField(max_length=50, blank=True))
    student_email= encrypt(models.TextField(blank=True, default="@students.henhudschools.org"))
    student_grade = models.CharField(max_length=10, blank=True, choices=[
        ('K', 'Kindergarten'), ('1', '1st'), ('2', '2nd'), ('3', '3rd'),
        ('4', '4th'), ('5', '5th'), ('6', '6th'), ('7', '7th'),
        ('8', '8th'), ('9', '9th'), ('10', '10th'), ('11', '11th'),
        ('12', '12th'), ('STAFF', 'Staff'),
    ])
    
    student_school = models.CharField(max_length=10, blank=True, choices=[
        ('BMMS', "Blue Mountain Middle School"), ('BV', "Buchanan-Verplanck Elementary School"), 
        ('FGL', 'Frank G. Lindsey'), ('FW', 'Furnace Woods'), ('HHHS', 'Hendrick Hudson High School'),
        ])

    #Dell Repair information
    sent_to_dell_check = models.BooleanField(default=False)
    dell_service_number = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    submitted_under = models.CharField(max_length=200, null=True, blank=True, default="techbilling@henhudschools.org")



    # Repair information
    service_now_inc_number = models.TextField(default="TBD")
    issue_description = models.TextField()
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('need_to_assess', 'Need To Assess'),
        ('waiting_on_box', 'Waiting On Box'),
        ('sent_to_dell', 'Sent To Dell'),
        ('on_site_repair', 'On Site Repair'),
        ('returned_from_dell', 'Returned From Dell'),
        ('fixed_by_tech', 'Fixed By Tech'),
        ('returned', 'Returned to Student'),
        ('tech_completed', 'Tech Completed'),
        ('vineetha_completed', 'Vineetha Completed'),
    ], default='pending')




    vineetha_checked = models.BooleanField(default=False)
    vineetha_repair_comments = models.CharField(max_length=500, blank=True)
    vineetha_closed = models.BooleanField(default=False)

    loaner = models.ForeignKey(
        'LongTermLoaner', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='repairs'
    )
        

    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='repairs_created'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='repairs_assigned'
    )
    
    # Privacy flags
    contains_student_data = models.BooleanField(default=True)
    third_party_access = models.BooleanField(
        default=False, 
        help_text="Third-party vendor accessed device"
    )
    consent_on_file = models.BooleanField(
        default=False, 
        help_text="Parent consent obtained"
    )
    
    class Meta:
        permissions = [
            ("view_student_info", "Can view student identifying information"),
            ("export_repair_data", "Can export repair data"),
        ]
        
    def __str__(self):
        return f"{self.device_name} - {self.status}"
    
    def get_audit_representation(self):
        """Safe representation for audit logs (no PII)"""
        return f"Repair #{self.id} - {self.device_name}"

# class Repair_Notes(modesl.Model):
#     - repair_pk (ForeignKey)
#     - device_DAM_ID (ForeignKey - device_DAM_ID)
#     - created_at (DateTimeField)
#     - user (ForeignKey - user)
#     - note (TextField)



class LongTermLoaner(models.Model):
    """
    Represents a loaner device that can be checked out multiple times.
    Current checkout information is stored directly on this model.
    Historical checkouts are tracked in LoanerCheckoutHistory.
    """
    # Device information
    device_name = models.CharField(max_length=200)
    device_DAM_ID = models.IntegerField(
        validators=[MinValueValidator(0)], 
        null=True, 
        blank=True, 
        default=0
    )
    device_serial = models.CharField(max_length=20, default="")
    
    # Device status
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('checked_out', 'Checked Out'),
        ('in_repair', 'In Repair'),
        ('retired', 'Retired'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='available'
    )
    
    # Current checkout information (if checked out)
    current_student_name = encrypt(models.CharField(
        max_length=200, 
        blank=True,
        help_text="Current student - ENCRYPTED"
    ))
    current_student_id = encrypt(models.CharField(
        max_length=50, 
        blank=True,
        help_text="Current student ID - ENCRYPTED"
    ))
    current_checkout_date = models.DateField(null=True, blank=True)
    current_expected_return = models.DateField(null=True, blank=True)
    current_checkout_notes = models.TextField(blank=True)
    current_checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_loaners',
        help_text="Staff member who checked out this device currently"
    )
    
    # Device metadata
    device_condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="General device notes")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        permissions = [
            ("view_loaner_student_info", "Can view student info on loaners"),
            ("checkout_loaner", "Can checkout loaner devices"),
            ("return_loaner", "Can return loaner devices"),
        ]
        ordering = ['device_name', 'device_DAM_ID']
    
    def __str__(self):
        status_display = f" ({self.get_status_display()})" if self.status != 'available' else ""
        return f"{self.device_name}" #- DAM:{self.device_DAM_ID}{status_display}
    
    def is_available(self):
        """Check if device is available for checkout"""
        return self.status == 'available'
    
    def get_current_checkout(self):
        """Get the current active checkout record if exists"""
        if self.status == 'checked_out':
            return self.checkout_history.filter(returned_date__isnull=True).first()
        return None
    
    def get_checkout_count(self):
        """Get total number of times this device has been checked out"""
        return self.checkout_history.count()
    
    def checkout_to_student(self, student_name, student_id, checkout_date, 
                           expected_return, checked_out_by, notes=""):
        """
        Checkout this loaner to a student.
        Creates a history record and updates current status.
        """
        # Update current status
        self.current_student_name = student_name
        self.current_student_id = student_id
        self.current_checkout_date = checkout_date
        self.current_expected_return = expected_return
        self.current_checkout_notes = notes
        self.current_checked_out_by = checked_out_by
        self.status = 'checked_out'
        self.save()
        
        # Create history record
        history = LoanerCheckoutHistory.objects.create(
            loaner=self,
            student_name=student_name,
            student_id=student_id,
            checkout_date=checkout_date,
            expected_return_date=expected_return,
            checkout_notes=notes,
            checked_out_by=checked_out_by,
            device_condition_out=self.device_condition,
        )
        
        return history
    
    def return_from_student(self, returned_by, return_notes="", condition_in=None):
        """
        Return this loaner from current student.
        Updates history record and clears current checkout.
        """
        from django.utils import timezone
        
        # Get current checkout history
        current_checkout = self.get_current_checkout()
        if current_checkout:
            current_checkout.returned_date = timezone.now().date()
            current_checkout.returned_by = returned_by
            current_checkout.return_notes = return_notes
            if condition_in:
                current_checkout.device_condition_in = condition_in
                self.device_condition = condition_in
            current_checkout.save()
        
        # Clear current checkout info
        self.current_student_name = ""
        self.current_student_id = ""
        self.current_checkout_date = None
        self.current_expected_return = None
        self.current_checkout_notes = ""
        self.current_checked_out_by = None
        self.status = 'available'
        self.save()
        
        return current_checkout


class LoanerCheckoutHistory(models.Model):
    """
    Complete history of every checkout for a loaner device.
    Tracks who had the device, when, and in what condition.
    """
    # Link to the loaner device
    loaner = models.ForeignKey(
        LongTermLoaner,
        on_delete=models.CASCADE,
        related_name='checkout_history',
        help_text="The loaner device this checkout is for"
    )
    
    # Student information (ENCRYPTED)
    student_name = encrypt(models.CharField(
        max_length=200,
        help_text="Student name - ENCRYPTED"
    ))
    student_id = encrypt(models.CharField(
        max_length=50,
        help_text="Student ID - ENCRYPTED"
    ))
    
    # Checkout information
    checkout_date = models.DateField(help_text="When device was checked out")
    expected_return_date = models.DateField(help_text="When device should be returned")
    returned_date = models.DateField(
        null=True, 
        blank=True,
        help_text="When device was actually returned (null = still checked out)"
    )
    
    # Staff tracking
    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checkouts_performed',
        help_text="Staff member who performed the checkout"
    )
    returned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns_performed',
        help_text="Staff member who processed the return"
    )
    
    # Condition tracking
    device_condition_out = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        help_text="Device condition when checked out"
    )
    device_condition_in = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged - Needs Repair'),
        ],
        blank=True,
        help_text="Device condition when returned"
    )
    
    # Notes
    checkout_notes = models.TextField(
        blank=True,
        help_text="Notes from checkout (reason, special instructions, etc.)"
    )
    return_notes = models.TextField(
        blank=True,
        help_text="Notes from return (damage, issues, etc.)"
    )
    
    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Privacy flag
    contains_student_data = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-checkout_date', '-created_at']
        verbose_name = "Loaner Checkout History"
        verbose_name_plural = "Loaner Checkout Histories"
        indexes = [
            models.Index(fields=['loaner', '-checkout_date']),
            models.Index(fields=['checkout_date']),
            models.Index(fields=['returned_date']),
        ]
    
    def __str__(self):
        status = "Returned" if self.returned_date else "Checked Out"
        return f"{self.loaner.device_name} - {status} on {self.checkout_date}"
    
    def is_overdue(self):
        """Check if this checkout is overdue"""
        from django.utils import timezone
        if self.returned_date:
            return False  # Already returned
        return timezone.now().date() > self.expected_return_date
    
    def days_checked_out(self):
        """Calculate how many days device has been/was checked out"""
        from django.utils import timezone
        end_date = self.returned_date or timezone.now().date()
        return (end_date - self.checkout_date).days
    
    def get_audit_representation(self):
        """Safe representation for audit logs (no PII)"""
        return f"Checkout #{self.id} - {self.loaner.device_name}"

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



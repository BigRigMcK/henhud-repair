# Updated admin.py with FIXED Loaner Checkout History Tracking

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Repair, LongTermLoaner, LoanerCheckoutHistory, ClassroomDevices, Classroom_Device_Purpose, DeviceModel
from .audit_models import AuditLog, ConsentRecord

# ============================================================================
# REPAIR ADMIN
# ============================================================================

@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'device_name', 
        'status', 
        'created_by',
        'created_at',
        'contains_student_data'
    ]
    list_filter = [
        'status', 
        'created_at', 
        'contains_student_data',
        'third_party_access'
    ]
    search_fields = [
        'device_name', 
        'device_serial', 
        'issue_description'
    ]
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_name', 'device_DAM_ID', 'device_serial')
        }),
        ('Student Information (RESTRICTED - ACCESS LOGGED)', {
            'fields': ('student_name', 'student_id', 'student_grade'),
            'classes': ('collapse',),
            'description': 'FERPA-protected data. All access is logged.'
        }),
        ('Repair Details', {
            'fields': ('issue_description', 'resolution_notes', 'status', 'loaner')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Privacy & Compliance', {
            'fields': ('contains_student_data', 'third_party_access', 'consent_on_file')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            action = 'CREATE'
        else:
            action = 'UPDATE'
            
        changes = {}
        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, ''))
                }
        
        super().save_model(request, obj, form, change)
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=action,
            content_object=obj,
            object_repr=obj.get_audit_representation(),
            changes=changes if changes else None,
        )


# ============================================================================
# LOANER CHECKOUT HISTORY INLINE
# ============================================================================

class LoanerCheckoutHistoryInline(admin.TabularInline):
    """
    Shows checkout history directly on the loaner admin page.
    Allows viewing past checkouts without leaving the loaner page.
    """
    model = LoanerCheckoutHistory
    extra = 0
    can_delete = False
    
    fields = [
        'checkout_date',
        'expected_return_date', 
        'returned_date',
        'student_id',
        'student_name',
        'checked_out_by',
        'device_condition_out',
        'device_condition_in',
        'is_overdue_display',
        'days_out_display',
    ]
    
    readonly_fields = [
        'checkout_date',
        'expected_return_date',
        'returned_date',
        'checked_out_by',
        'returned_by',
        'device_condition_out',
        'device_condition_in',
        'is_overdue_display',
        'days_out_display',
        'student_name',
        'student_id',
    ]
    
    def is_overdue_display(self, obj):
        """Show if checkout is/was overdue"""
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ OVERDUE</span>')
        return '✓ On Time'
    is_overdue_display.short_description = 'Status'
    
    def days_out_display(self, obj):
        """Show how many days device was/is checked out"""
        days = obj.days_checked_out()
        if obj.returned_date:
            return f"{days} days"
        else:
            return format_html('<span style="font-weight: bold;">{} days (ongoing)</span>', days)
    days_out_display.short_description = 'Duration'
    
    def has_add_permission(self, request, obj=None):
        """Don't allow manual creation - use checkout/return methods"""
        return False


# ============================================================================
# LONG TERM LOANER ADMIN
# ============================================================================

@admin.register(LongTermLoaner)
class LongTermLoanerAdmin(admin.ModelAdmin):
    list_display = [
        'device_name_display',
        'device_DAM_ID', 
        'device_serial',
        'status_display',
        'current_checkout_info',
        'checkout_count_display',
        'device_condition',
    ]
    
    list_filter = [
        'status',
        'device_condition',
        'created_at',
    ]
    
    search_fields = [
        'device_name', 
        'device_DAM_ID', 
        'device_serial',
    ]
    
    fieldsets = (
        ('Device Information', {
            'fields': (
                'device_name', 
                'device_DAM_ID', 
                'device_serial',
                'device_condition',
                'purchase_date',
                'notes',
            )
        }),
        ('Current Status', {
            'fields': ('status',),
        }),
        ('Current Checkout (if checked out)', {
            'fields': (
                'current_student_name',
                'current_student_id',
                'current_checkout_date',
                'current_expected_return',
                'current_checkout_notes',
                'current_checked_out_by',
            ),
            'classes': ('collapse',),
            'description': 'FERPA-protected student data. Access is audited. '
                          'History is automatically created when you save.'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [LoanerCheckoutHistoryInline]
    
    actions = ['checkout_device_action', 'return_device_action']
    
    # ========================================================================
    # CUSTOM LIST DISPLAY METHODS
    # ========================================================================
    
    def device_name_display(self, obj):
        """Show device name with visual indicator for checked out devices"""
        if obj.status == 'checked_out':
            return format_html(
                '<span style="font-weight: bold;">📤 {}</span>', 
                obj.device_name
            )
        elif obj.status == 'in_repair':
            return format_html(
                '<span style="color: orange;">🔧 {}</span>', 
                obj.device_name
            )
        elif obj.status == 'retired':
            return format_html(
                '<span style="color: gray;">⚠️ {}</span>', 
                obj.device_name
            )
        return obj.device_name
    device_name_display.short_description = 'Device Name'
    device_name_display.admin_order_field = 'device_name'
    
    def status_display(self, obj):
        """Show status with color coding"""
        colors = {
            'available': 'green',
            'checked_out': 'blue',
            'in_repair': 'orange',
            'retired': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def current_checkout_info(self, obj):
        """Show current checkout information in list view"""
        if obj.status == 'checked_out':
            current = obj.get_current_checkout()
            if current:
                days_out = current.days_checked_out()
                is_overdue = current.is_overdue()
                
                if is_overdue:
                    return format_html(
                        '<span style="color: red; font-weight: bold;">⚠️ OVERDUE ({} days)</span>',
                        days_out
                    )
                else:
                    return format_html(
                        '<span style="color: blue;">Checked out {} days ago</span>',
                        days_out
                    )
        return '-'
    current_checkout_info.short_description = 'Current Checkout'
    
    def checkout_count_display(self, obj):
        """Show total number of checkouts"""
        count = obj.get_checkout_count()
        if count == 0:
            return format_html('<span style="color: gray;">Never checked out</span>')
        return format_html('<strong>{}</strong> times', count)
    checkout_count_display.short_description = 'Total Checkouts'
    
    # ========================================================================
    # ADMIN ACTIONS
    # ========================================================================
    
    def checkout_device_action(self, request, queryset):
        """
        Admin action to checkout selected devices.
        """
        available_devices = queryset.filter(status='available')
        count = available_devices.count()
        
        if count == 0:
            self.message_user(
                request,
                'No available devices selected. Only available devices can be checked out.',
                level='warning'
            )
        else:
            self.message_user(
                request,
                f'{count} device(s) ready for checkout. '
                f'Click on each device to enter checkout details.',
                level='success'
            )
    checkout_device_action.short_description = "Prepare selected devices for checkout"
    
    def return_device_action(self, request, queryset):
        """
        Admin action to return selected devices.
        """
        checked_out_devices = queryset.filter(status='checked_out')
        count = 0
        
        for device in checked_out_devices:
            device.return_from_student(
                returned_by=request.user,
                return_notes=f"Returned via admin action by {request.user.username}"
            )
            count += 1
            
            # Log the return
            AuditLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='UPDATE',
                content_object=device,
                object_repr=str(device),
                changes={'action': 'Device returned via admin action'},
            )
        
        if count == 0:
            self.message_user(
                request,
                'No checked out devices selected.',
                level='warning'
            )
        else:
            self.message_user(
                request,
                f'{count} device(s) successfully returned.',
                level='success'
            )
    return_device_action.short_description = "Return selected devices"
    
    # ========================================================================
    # SAVE METHOD WITH HISTORY TRACKING - THIS IS THE FIX!
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """
        FIXED: Now properly creates and updates history records
        """
        
        action_type = 'UPDATE'
        changes = {}
        
        # Track what changed
        if change:
            for field in form.changed_data:
                old_value = form.initial.get(field, '')
                new_value = form.cleaned_data.get(field, '')
                changes[field] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
        
        # ====================================================================
        # DETECT CHECKOUT (status changed to 'checked_out')
        # ====================================================================
        if change and 'status' in form.changed_data:
            old_status = form.initial.get('status', '')
            new_status = form.cleaned_data.get('status', '')
            
            # Going from available/other to checked_out = NEW CHECKOUT
            if new_status == 'checked_out' and old_status != 'checked_out':
                action_type = 'CHECKOUT'
                
                # Save the object first
                super().save_model(request, obj, form, change)
                
                # Create history record if we have the required fields
                if obj.current_student_name and obj.current_checkout_date:
                    LoanerCheckoutHistory.objects.create(
                        loaner=obj,
                        student_name=obj.current_student_name,
                        student_id=obj.current_student_id or '',
                        checkout_date=obj.current_checkout_date,
                        expected_return_date=obj.current_expected_return or obj.current_checkout_date,
                        checkout_notes=obj.current_checkout_notes,
                        checked_out_by=obj.current_checked_out_by or request.user,
                        device_condition_out=obj.device_condition,
                    )
                    
                    self.message_user(
                        request,
                        f'✓ Checkout history created for {obj.device_name}',
                        level='success'
                    )
                else:
                    self.message_user(
                        request,
                        '⚠️ Warning: Checkout history not created - missing student name or checkout date',
                        level='warning'
                    )
            
            # Going from checked_out to available/other = RETURN
            elif old_status == 'checked_out' and new_status != 'checked_out':
                action_type = 'RETURN'
                
                # Find the current (unreturned) checkout history
                current_checkout = obj.checkout_history.filter(returned_date__isnull=True).first()
                
                if current_checkout:
                    # Update the history with return information
                    current_checkout.returned_date = timezone.now().date()
                    current_checkout.returned_by = request.user
                    current_checkout.return_notes = f"Returned via admin - status changed to {new_status}"
                    current_checkout.device_condition_in = obj.device_condition
                    current_checkout.save()
                    
                    self.message_user(
                        request,
                        f'✓ Return recorded in history for {obj.device_name}',
                        level='success'
                    )
                
                # Save the object
                super().save_model(request, obj, form, change)
                
                # Clear current checkout fields
                obj.current_student_name = ''
                obj.current_student_id = ''
                obj.current_checkout_date = None
                obj.current_expected_return = None
                obj.current_checkout_notes = ''
                obj.current_checked_out_by = None
                obj.save(update_fields=[
                    'current_student_name',
                    'current_student_id', 
                    'current_checkout_date',
                    'current_expected_return',
                    'current_checkout_notes',
                    'current_checked_out_by'
                ])
            else:
                # Status changed but not checkout/return related
                super().save_model(request, obj, form, change)
        
        # ====================================================================
        # UPDATE EXISTING CHECKOUT (student changed while still checked out)
        # ====================================================================
        elif change and obj.status == 'checked_out':
            # Check if student info changed while device is checked out
            student_changed = any(field in form.changed_data for field in [
                'current_student_name', 
                'current_student_id',
                'current_checkout_date',
                'current_expected_return'
            ])
            
            if student_changed:
                # Find current checkout
                current_checkout = obj.checkout_history.filter(returned_date__isnull=True).first()
                
                if current_checkout:
                    # Update the existing history record
                    if 'current_student_name' in form.changed_data:
                        current_checkout.student_name = obj.current_student_name
                    if 'current_student_id' in form.changed_data:
                        current_checkout.student_id = obj.current_student_id
                    if 'current_checkout_date' in form.changed_data:
                        current_checkout.checkout_date = obj.current_checkout_date
                    if 'current_expected_return' in form.changed_data:
                        current_checkout.expected_return_date = obj.current_expected_return
                    
                    current_checkout.save()
                    
                    self.message_user(
                        request,
                        f'✓ Checkout history updated for {obj.device_name}',
                        level='info'
                    )
            
            super().save_model(request, obj, form, change)
        
        # ====================================================================
        # NORMAL SAVE (not checkout/return related)
        # ====================================================================
        else:
            super().save_model(request, obj, form, change)
        
        # ====================================================================
        # CREATE AUDIT LOG
        # ====================================================================
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=action_type,
            content_object=obj,
            object_repr=str(obj),
            changes=changes if changes else None,
        )


# ============================================================================
# LOANER CHECKOUT HISTORY ADMIN
# ============================================================================

@admin.register(LoanerCheckoutHistory)
class LoanerCheckoutHistoryAdmin(admin.ModelAdmin):
    """
    Standalone admin for viewing complete checkout history across all devices.
    Useful for reports and audits.
    """
    list_display = [
        'id',
        'loaner_link',
        'checkout_date',
        'expected_return_date',
        'returned_date',
        'checked_out_by',
        'returned_by',
        'overdue_status',
        'duration_display',
    ]
    
    list_filter = [
        'checkout_date',
        'returned_date',
        'checked_out_by',
        'returned_by',
        'device_condition_out',
        'device_condition_in',
    ]
    
    search_fields = [
        'loaner__device_name',
        'loaner__device_serial',
        'checkout_notes',
        'return_notes',
    ]
    
    date_hierarchy = 'checkout_date'
    
    fieldsets = (
        ('Loaner Device', {
            'fields': ('loaner',)
        }),
        ('Student Information (RESTRICTED - ACCESS LOGGED)', {
            'fields': ('student_name', 'student_id'),
            'classes': ('collapse',),
            'description': 'FERPA-protected data. Access is audited.'
        }),
        ('Checkout Details', {
            'fields': (
                'checkout_date',
                'expected_return_date',
                'checked_out_by',
                'device_condition_out',
                'checkout_notes',
            )
        }),
        ('Return Details', {
            'fields': (
                'returned_date',
                'returned_by',
                'device_condition_in',
                'return_notes',
            )
        }),
    )
    
    readonly_fields = [
        'loaner',
        'student_name',
        'student_id',
        'checkout_date',
        'expected_return_date',
        'checked_out_by',
        'device_condition_out',
        'checkout_notes',
        'created_at',
        'updated_at',
    ]
    
    def loaner_link(self, obj):
        """Create a link to the loaner device"""
        url = reverse('admin:repair_tracker_longtermloaner_change', args=[obj.loaner.id])
        return format_html('<a href="{}">{}</a>', url, obj.loaner)
    loaner_link.short_description = 'Loaner Device'
    loaner_link.admin_order_field = 'loaner__device_name'
    
    def overdue_status(self, obj):
        """Show if checkout is/was overdue"""
        if obj.is_overdue():
            days_overdue = (timezone.now().date() - obj.expected_return_date).days
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ OVERDUE by {} days</span>',
                days_overdue
            )
        elif obj.returned_date:
            return format_html('<span style="color: green;">✓ Returned on time</span>')
        else:
            return format_html('<span style="color: blue;">✓ On time (checked out)</span>')
    overdue_status.short_description = 'Status'
    
    def duration_display(self, obj):
        """Show checkout duration"""
        days = obj.days_checked_out()
        if obj.returned_date:
            return f"{days} days"
        else:
            return format_html('<strong>{} days (ongoing)</strong>', days)
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Don't allow manual creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete history"""
        return request.user.is_superuser


# ============================================================================
# AUDIT LOG ADMIN
# ============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'username',
        'action',
        'object_repr',
        'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'user','ip_address']
    search_fields = ['username', 'object_repr', 'ip_address']
    readonly_fields = [
        'user', 
        'username', 
        'action', 
        'content_type', 
        'object_id',
        'object_repr', 
        'changes', 
        'timestamp', 
        'ip_address', 
        'user_agent'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================================
# CONSENT RECORD ADMIN
# ============================================================================

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = [
        'student_identifier',
        'parent_name',
        'consent_given',
        'consent_date',
        'expiration_date',
        'revoked'
    ]
    list_filter = ['consent_given', 'revoked', 'consent_date']
    search_fields = ['student_identifier', 'parent_name']
    
    fieldsets = (
        ('Student & Parent Information', {
            'fields': ('student_identifier', 'parent_name')
        }),
        ('Consent Details', {
            'fields': (
                'consent_given',
                'consent_date',
                'consent_scope',
                'expiration_date',
            )
        }),
        ('Revocation', {
            'fields': ('revoked', 'revoked_date'),
            'classes': ('collapse',)
        }),
    )

# ==================================================
# Classroom Device Purposes
# ===================================================

@admin.register(ClassroomDevices)
class ClassroomDevice(admin.ModelAdmin):
    list_display = [
        'classroom', 'classroom_dam_id','classroom_device_serial_number'
    ]
    list_filter = [ 'classroom', 'classroom_dam_id','classroom_device_serial_number']

    fieldsets = (

        ('Classroom Device', { 
            'fields': ( 'classroom_device_purpose','classroom_dam_id',
                 'classroom_device_serial_number','classroom','classroom_teacher', 'classroom_device_model',)}),
        ('Device Check', {
            'fields': ('classroom_device_checkout', 'classroom_device_checkin')
            })
        )

@admin.register(Classroom_Device_Purpose)
class ClassroomDevicePurpose(admin.ModelAdmin):
    list_display = [
        'name'
        ]

@admin.register(DeviceModel)
class Device_Model(admin.ModelAdmin):
    list_display = [
        'Model_Type'
    ]
    list_filter = [ 'Model_Type']

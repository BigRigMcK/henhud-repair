from django.contrib import admin
from .models import District_Member, District_Member_DeviceAssignment
from repair_tracker.audit_models import AuditLog, ConsentRecord
# Register your models here.




@admin.register(District_Member)
class District_Member_Admin(admin.ModelAdmin):
    actions = ['']
    list_display = [
        'id',
        'district_member_id',
        'district_member_name', 
        'district_member_email',
        'district_member_grade', 
        'district_member_building',
        
        
    ]
    list_filter = [
       
    ]
    search_fields = [
       
    ]
    readonly_fields = ['created_at','updated_at',]
    
    fieldsets = (
        
        ('District Member Information (RESTRICTED - ACCESS LOGGED)', {
            'fields': ('district_member_name','district_member_id','district_member_email','district_member_grade','district_member_building',
        'created_at','updated_at',),
            #'classes': ('collapse',),
            'description': 'FERPA-protected data. All access is logged.'
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
    #export_repairs_csv = export_repairs_csv



@admin.register(District_Member_DeviceAssignment)
class District_Member_DeviceAssignment_Admin(admin.ModelAdmin):
    actions = ['']
    list_display = [
        'district_member', 
        'device',
        'repair',
        'assigned_date',
        'returned_date',
        'assigned_by',
        ]
    list_filter = [
       
    ]
    search_fields = [
       
    ]
    
    fieldsets = (
        
        ('District Device Assignment', {
            'fields': ('district_member','device','repair','assigned_date','returned_date','assigned_by',),
            'classes': ('collapse',),
            'description': 'FERPA-protected data. All access is logged.'
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
    #export_repairs_csv = export_repairs_csv
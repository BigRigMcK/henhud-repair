from django.contrib import admin
from .models import District_Device_Inventory, District_Location, District_Department
from repair_tracker.audit_models import AuditLog
from Base_Models.models import Current_Status

@admin.register(District_Device_Inventory)
class District_Device_InventoryAdmin(admin.ModelAdmin):
    list_display = ['asset_name', 'asset_id', 'serial_number']

    def save_model(self, request, obj, form, change):
        # 1. Initialize variables
        action = 'UPDATE' if change else 'CREATE'
        changes = {}

        # 2. Capture changes if this is an update
        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, ''))
                }

        # 3. Save the actual object first
        super().save_model(request, obj, form, change)

        # 4. Log the action to AuditLog
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=action,
            content_object=obj,
            object_repr=obj.get_audit_representation(),
            changes=changes if changes else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@admin.register(District_Location)
class District_LocationAdmin(admin.ModelAdmin):
    list_display = ['school','room']


@admin.register(District_Department)
class District_DepartmentAdmin(admin.ModelAdmin):
    list_display = ['department']


@admin.register(Current_Status)
class Device_Current_StatusAdmin(admin.ModelAdmin):
    list_display = ['Status']
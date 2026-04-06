from django.contrib import admin
from django.utils import timezone

from repair_tracker.audit_models import AuditLog
from Base_Models.models import Current_Status

from .models import (
    District_Device_Inventory,
    District_Location,
    District_Department,
    Asset_History,
)
from .csv_export_actions import export_inventory_csv, export_asset_history_csv


# ============================================================================
# HELPERS
# ============================================================================

def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def _audit(request, action, obj, changes=None):
    """Create a single AuditLog entry."""
    AuditLog.objects.create(
        user=request.user,
        username=request.user.username,
        action=action,
        content_object=obj,
        object_repr=str(obj),
        changes=changes or None,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )


# ============================================================================
# ASSET HISTORY INLINE
# ============================================================================

class AssetHistoryInline(admin.TabularInline):
    model = Asset_History
    extra = 0
    readonly_fields = ['change_date', 'description', 'changed_by']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ============================================================================
# DISTRICT DEVICE INVENTORY
# ============================================================================

@admin.register(District_Device_Inventory)
class District_Device_InventoryAdmin(admin.ModelAdmin):
    actions = [export_inventory_csv]

    list_display = ['asset_name', 'asset_id', 'serial_number', 'current_status', 'location', 'department']
    list_filter = ['current_status', 'department', 'location']
    search_fields = ['asset_name', 'serial_number', 'asset_id']

    inlines = [AssetHistoryInline]

    fieldsets = (
        ('Asset Identification', {
            'fields': ('asset_name', 'asset_id', 'serial_number', 'model_type','current_status'),
        }),
        ('Location & Department', {
            'fields': ('location', 'department'),
        }),
        ('Hardware Details', {
            'fields': ('mac_address', 'capacity_hard_drive_size', 'manufacture_make', 'vendor'),
        }),
        ('Financial & Administrative', {
            'fields': ('source_of_funding', 'po_order', 'purchase_value',),
        }),
        ('Student Info (RESTRICTED - ACCESS LOGGED)', {
            'fields': ('student_id_number',),
            'classes': ('collapse',),
            'description': 'FERPA-protected data. All access is logged.',
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
    )

    def save_model(self, request, obj, form, change):
        action = 'UPDATE' if change else 'CREATE'
        changes = {}

        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, '')),
                }

        super().save_model(request, obj, form, change)

        # Primary AuditLog entry
        _audit(request, action, obj, changes if changes else None)

        # Double-log: also write to Asset_History
        change_summary = (
            'Updated fields: ' + ', '.join(changes.keys())
            if changes
            else 'Record created'
        )
        Asset_History.objects.create(
            asset=obj,
            description=f'[AuditLog mirror] {change_summary}',
            changed_by=request.user.username,
        )

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        # Asset_History cascades on delete so no separate entry needed
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)


# ============================================================================
# ASSET HISTORY
# ============================================================================

@admin.register(Asset_History)
class AssetHistoryAdmin(admin.ModelAdmin):
    actions = [export_asset_history_csv]

    list_display = ['asset', 'change_date', 'changed_by', 'description']
    list_filter = ['change_date', 'changed_by']
    search_fields = ['asset__asset_name', 'asset__serial_number', 'description', 'changed_by']
    date_hierarchy = 'change_date'

    readonly_fields = ['asset', 'change_date', 'description', 'changed_by']

    def save_model(self, request, obj, form, change):
        action = 'UPDATE' if change else 'CREATE'
        changes = {}
        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, '')),
                }
        super().save_model(request, obj, form, change)
        _audit(request, action, obj, changes if changes else None)

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ============================================================================
# DISTRICT LOCATION
# ============================================================================

@admin.register(District_Location)
class District_LocationAdmin(admin.ModelAdmin):
    list_display = ['school', 'room']
    search_fields = ['school', 'room']

    def save_model(self, request, obj, form, change):
        action = 'UPDATE' if change else 'CREATE'
        changes = {}
        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, '')),
                }
        super().save_model(request, obj, form, change)
        _audit(request, action, obj, changes if changes else None)

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)


# ============================================================================
# DISTRICT DEPARTMENT
# ============================================================================

@admin.register(District_Department)
class District_DepartmentAdmin(admin.ModelAdmin):
    list_display = ['department']
    search_fields = ['department']

    def save_model(self, request, obj, form, change):
        action = 'UPDATE' if change else 'CREATE'
        changes = {}
        if change:
            for field in form.changed_data:
                changes[field] = {
                    'old': str(form.initial.get(field, '')),
                    'new': str(form.cleaned_data.get(field, '')),
                }
        super().save_model(request, obj, form, change)
        _audit(request, action, obj, changes if changes else None)

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)


# ============================================================================
# CURRENT STATUS (Base_Models)
# ============================================================================

@admin.register(Current_Status)
class Device_Current_StatusAdmin(admin.ModelAdmin):
    list_display = ['Status']
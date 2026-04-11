from django.contrib import admin
from django.utils import timezone
from repair_tracker.audit_models import AuditLog
from Inventory.models import Asset_History
from .models import District_Device_Audit, Individual_AuditDevice


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def _audit(request, action, obj, changes=None):
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


@admin.register(District_Device_Audit)
class District_Device_AuditAdmin(admin.ModelAdmin):
    list_display = ['audit_date', 'location', 'auditor']
    list_filter = ['audit_date', 'location', 'auditor']
    search_fields = ['location']
    readonly_fields = ('audit_date', 'devices')

    fieldsets = (
        ('Audit Info', {
            'fields': ('auditor', 'devices'),
        }),
        ('Location', {
            'fields': ('location',),
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
        _audit(request, action, obj, changes if changes else None)

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)


@admin.register(Individual_AuditDevice)
class Individual_AuditDevice_Admin(admin.ModelAdmin):
    list_display = ['audit', 'device', 'found', 'notes', 'found_at']
    list_filter = ['found', 'found_at']
    search_fields = ['audit__location']

    fieldsets = (
        ('Asset Identification', {
            'fields': ('audit', 'device', 'found', 'found_at'),
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
        _audit(request, action, obj, changes if changes else None)

    def delete_model(self, request, obj):
        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _audit(request, 'DELETE', obj, {'deleted': str(obj)})
        super().delete_queryset(request, queryset)
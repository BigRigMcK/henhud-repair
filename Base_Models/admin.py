from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from repair_tracker.audit_models import AuditLog
from .models import District_Location, District_Department

from Inventory.admin import _audit

@admin.register(District_Location)
class District_LocationAdmin(admin.ModelAdmin):
    list_display = ['pk','school', 'room']
    list_filter = ['school']
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


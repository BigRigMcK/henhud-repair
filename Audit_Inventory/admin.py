from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from repair_tracker.audit_models import AuditLog
from .models import District_Device_Audit, Individual_AuditDevice


# ============================================================================
# HELPERS
# ============================================================================

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


# ============================================================================
# INDIVIDUAL AUDIT DEVICE INLINE
# ============================================================================

class IndividualAuditDeviceInline(admin.TabularInline):
    model = Individual_AuditDevice
    extra = 0
    can_delete = False
    readonly_fields = ['device', 'found_at']
    fields = ['device', 'found', 'found_at', 'notes']

    def has_add_permission(self, request, obj=None):
        # Rows are created programmatically by start_audit view — not manually
        return False


# ============================================================================
# DISTRICT DEVICE AUDIT
# ============================================================================

@admin.register(District_Device_Audit)
class District_Device_AuditAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'location',
        'auditor',
        'started_at',
        'completed_at',
        'status_badge',
        'progress_display',
    ]
    list_filter = [
        'is_complete',
        'started_at',
        'location__school',   # group filter by school name
        'auditor',
    ]
    search_fields = [
        'location__school',
        'location__room',
        'auditor__username',
        'auditor__first_name',
        'auditor__last_name',
    ]
    readonly_fields = [
        'started_at',
        'completed_at',
        'is_complete',
        'progress_display',
    ]
    ordering = ['-started_at']
    inlines = [IndividualAuditDeviceInline]

    fieldsets = (
        ('Audit Info', {
            'fields': ('auditor', 'started_at', 'is_complete', 'completed_at', 'progress_display'),
        }),
        ('Location', {
            'fields': ('location',),
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
    )

    # ── Custom display columns ───────────────────────────────────────────────

    def status_badge(self, obj):
        if obj.is_complete:
            return format_html(
                '<span style="color:#198754; font-weight:bold;">✓ Complete</span>'
            )
        return format_html(
            '<span style="color:#ffc107; font-weight:bold;">⏳ In Progress</span>'
        )
    status_badge.short_description = 'Status'

    def progress_display(self, obj):
        total = obj.total_devices()
        if total == 0:
            return '—'
        found = obj.found_count()
        pct = obj.completion_percentage()
        return format_html(
            '{} / {} devices found &nbsp;({}%)',
            found, total, pct
        )
    progress_display.short_description = 'Progress'

    # ── Audit logging ────────────────────────────────────────────────────────

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
# INDIVIDUAL AUDIT DEVICE
# ============================================================================

@admin.register(Individual_AuditDevice)
class IndividualAuditDeviceAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'audit_link',
        'device',
        'found',
        'found_at',
        'notes_preview',
    ]
    list_filter = [
        'found',
        'found_at',
        'audit__location__school',   # filter by school
        'audit__is_complete',
    ]
    search_fields = [
        'audit__location__school',
        'audit__location__room',
        'device__asset_name',
        'device__serial_number',
        'device__asset_id',
    ]
    readonly_fields = ['found_at', 'audit', 'device']
    ordering = ['-audit__started_at', 'device__asset_name']

    fieldsets = (
        ('Audit & Device', {
            'fields': ('audit', 'device'),
            'description': 'These are set automatically and cannot be changed here.',
        }),
        ('Audit Result', {
            'fields': ('found', 'found_at', 'notes'),
        }),
    )

    # ── Custom display columns ───────────────────────────────────────────────

    def audit_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:Audit_Inventory_district_device_audit_change', args=[obj.audit.pk])
        return format_html('<a href="{}">Audit #{}</a>', url, obj.audit.pk)
    audit_link.short_description = 'Audit'

    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:60] + ('…' if len(obj.notes) > 60 else '')
        return '—'
    notes_preview.short_description = 'Notes'

    # ── Audit logging ────────────────────────────────────────────────────────

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
        # Rows are created by start_audit view — prevent manual creation
        return False
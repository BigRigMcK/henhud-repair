import csv
from django.http import HttpResponse
from django.utils import timezone
from repair_tracker.audit_models import AuditLog


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def _log_export(request, description, record_count):
    AuditLog.objects.create(
        user=request.user,
        username=request.user.username,
        action='EXPORT',
        object_repr=description,
        changes={
            'record_count': record_count,
            'exported_at': timezone.now().isoformat(),
            'ip_address': _get_client_ip(request),
        },
    )


# ==============================================================
# DISTRICT DEVICE INVENTORY
# ==============================================================

def export_inventory_csv(modeladmin, request, queryset):
    """Export selected District_Device_Inventory records to CSV.
    student_id_number is gated behind the view_student_info permission."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="district_inventory_' + timestamp + '.csv"'
    )

    can_view_student = request.user.has_perm('repair_tracker.view_student_info')

    writer = csv.writer(response)

    headers = [
        'ID', 'Asset Name', 'Asset ID', 'Serial Number',
        'Current Status', 'Model Type',
        'Location (School)', 'Location (Room)',
        'Department',
        'MAC Address', 'Capacity / Hard Drive Size',
        'Manufacturer / Make', 'Vendor',
        'Source of Funding', 'PO Order', 'Purchase Value',
        'Notes',
    ]
    if can_view_student:
        headers.append('Student ID Number')

    writer.writerow(headers)

    count = queryset.count()

    for device in queryset.select_related('location', 'department', 'model_type'):
        row = [
            device.id,
            device.asset_name,
            device.asset_id,
            device.serial_number or '',
            device.current_status or '',
            device.model_type.Model_Type if device.model_type else '',
            device.location.school if device.location else '',
            device.location.room if device.location else '',
            device.department.department if device.department else '',
            device.mac_address or '',
            device.capacity_hard_drive_size or '',
            device.manufacture_make or '',
            device.vendor or '',
            device.source_of_funding or '',
            device.po_order or '',
            device.purchase_value or '',
            device.notes or '',
        ]
        if can_view_student:
            row.append(device.student_id_number if device.student_id_number else '')
        writer.writerow(row)

    pii_note = ' [included student PII]' if can_view_student else ' [PII excluded]'
    _log_export(
        request,
        'District Device Inventory CSV export - ' + str(count) + ' record(s)' + pii_note,
        count,
    )

    return response

export_inventory_csv.short_description = "Export selected inventory records to CSV"


# ==============================================================
# ASSET HISTORY
# ==============================================================

def export_asset_history_csv(modeladmin, request, queryset):
    """Export selected Asset_History records to CSV."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="asset_history_' + timestamp + '.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Asset Name', 'Asset ID', 'Serial Number',
        'Change Date', 'Description', 'Changed By',
    ])

    count = queryset.count()

    for record in queryset.select_related('asset'):
        writer.writerow([
            record.id,
            record.asset.asset_name,
            record.asset.asset_id,
            record.asset.serial_number or '',
            record.change_date.strftime('%Y-%m-%d %H:%M:%S'),
            record.description or '',
            record.changed_by or '',
        ])

    _log_export(
        request,
        'Asset History CSV export - ' + str(count) + ' record(s)',
        count,
    )

    return response

export_asset_history_csv.short_description = "Export selected asset history to CSV"
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

def write_inventory_csv(queryset, request):
    """Core CSV-writing logic for District_Device_Inventory.
    Can be called from any view OR from an admin action.
    
    Args:
        queryset: a filtered QuerySet of District_Device_Inventory
        request: the HttpRequest (needed for permission check + audit log)
    
    Returns:
        HttpResponse with CSV content as an attachment download
    """
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="district_inventory_' + timestamp + '.csv"'
    )

    can_view_student = request.user.has_perm('repair_tracker.view_student_info')

    writer = csv.writer(response)

    headers = [
        'ID', 'Asset Name', 'Asset ID', 'Serial Number',]

    if can_view_student:
        headers.append('District Member ID')

    headers +=[
        'Current Status', 'Model Type',
        'Location (School)', 'Location (Room)',
        'Department',
        'MAC Address', 'Capacity / Hard Drive Size',
        'Manufacturer / Make', 'Vendor',
        'Source of Funding', 'PO Order', 'Purchase Value',
        'Notes',
    ]
    
    writer.writerow(headers)

    # ────────────────────────────────────────────────────────────────
    # Performance: re-apply select_related AND prefetch_related here.
    #
    # The view's helper already prefetched student_assignments, but
    # calling .select_related(...) on the queryset returns a NEW
    # queryset that loses any earlier prefetch_related. We have to
    # add it back, or we get an N+1 query problem (one extra query
    # per device row to fetch its assignments).
    #
    # Rule of thumb: every chained queryset method returns a new
    # queryset. Optimizations only apply to the queryset they're
    # called on — they don't "stick" across re-filtering.
    # ────────────────────────────────────────────────────────────────
    optimized_queryset = queryset.select_related(
        'location', 'department', 'model_type'
    ).prefetch_related(
        'student_assignments__district_member'
    )

    count = queryset.count()

    for device in optimized_queryset:
        # Start with the first four columns
        row = [
            device.id,
            device.asset_name,
            device.asset_id,
            device.serial_number or '',
        ]

        # Insert District Member ID right after Serial Number (permission-gated)
        if can_view_student:
            # ────────────────────────────────────────────────────
            # Find the ACTIVE assignment (returned_date is None).
            #
            # We walk the prefetched list in Python instead of
            # calling .filter() — .filter() would trigger a fresh
            # DB query and defeat the prefetch.
            #
            # next() with a generator expression is a compact way
            # to say "give me the first match, or None if there
            # isn't one." It stops as soon as it finds a hit.
            # ────────────────────────────────────────────────────
            active_assignment = next(
                (a for a in device.student_assignments.all() if not a.returned_date),
                None
            )

            if active_assignment:
                row.append(active_assignment.district_member.district_member_id or '')
            else:
                row.append('')

        # Continue with the rest of the columns
        row += [
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

        writer.writerow(row)

    pii_note = ' [included district member IDs]' if can_view_student else ' [PII excluded]'
    _log_export(
        request,
        'District Device Inventory CSV export - ' + str(count) + ' record(s)' + pii_note,
        count,
    )

    return response


def export_inventory_csv(modeladmin, request, queryset):
    """Admin action wrapper. Django's admin requires this specific
    function signature (modeladmin, request, queryset), so we keep
    this thin shim that just delegates to the real logic."""
    return write_inventory_csv(queryset, request)

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
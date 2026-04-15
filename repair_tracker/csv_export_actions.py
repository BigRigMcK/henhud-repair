import csv
from django.http import HttpResponse
from django.utils import timezone
from .audit_models import AuditLog


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
# REPAIRS
# ==============================================================

def export_repairs_csv(modeladmin, request, queryset):
    """Export selected Repair records to CSV. Student PII gated by permission."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="repairs_' + timestamp + '.csv"'

    can_view_student = request.user.has_perm('repair_tracker.view_student_info')

    writer = csv.writer(response)

    headers = [
        'ID', 'Device Name', 'DAM ID', 'Serial Number',
        'Status', 'Service Now INC',
        'Sent to Dell', 'Dell Service #', 'Submitted Under',
        'Loaner', 'Assigned To', 'Created By',
        'Created At', 'Updated At',
        'Contains Student Data', 'Third Party Access', 'Consent On File',
        'Vineetha Checked', 'Vineetha Closed', 'Vineetha Comments',
        'Issue Description', 'Resolution Notes',
    ]
    if can_view_student:
        headers += ['District Member']

    writer.writerow(headers)

    count = queryset.count()

    for repair in queryset.select_related('assigned_to', 'created_by', 'loaner'):
        row = [
            repair.id,
            repair.device_name or '',
            repair.device_DAM_ID or '',
            repair.device_serial or '',
            repair.get_status_display(),
            repair.get_student_school_display() if repair.student_school else '',
            repair.service_now_inc_number or '',
            'Yes' if repair.sent_to_dell_check else 'No',
            repair.dell_service_number or '',
            repair.submitted_under or '',
            str(repair.loaner) if repair.loaner else '',
            repair.assigned_to.username if repair.assigned_to else '',
            repair.created_by.username if repair.created_by else '',
            repair.created_at.strftime('%Y-%m-%d %H:%M') if repair.created_at else '',
            repair.updated_at.strftime('%Y-%m-%d %H:%M') if repair.updated_at else '',
            'Yes' if repair.contains_student_data else 'No',
            'Yes' if repair.third_party_access else 'No',
            'Yes' if repair.consent_on_file else 'No',
            'Yes' if repair.vineetha_checked else 'No',
            'Yes' if repair.vineetha_closed else 'No',
            repair.vineetha_repair_comments or '',
            repair.issue_description or '',
            repair.resolution_notes or '',
        ]
        if can_view_student:
            dm = repair.district_member
            row += [
                str(dm) if dm else '',   # district_member __str__
            ]
        writer.writerow(row)

    pii_note = ' [included student PII]' if can_view_student else ' [PII excluded]'
    _log_export(request, 'Repairs CSV export - ' + str(count) + ' record(s)' + pii_note, count)

    return response

export_repairs_csv.short_description = "Export selected repairs to CSV"


# ==============================================================
# LONG TERM LOANERS
# ==============================================================

def export_loaners_csv(modeladmin, request, queryset):
    """Export selected LongTermLoaner records to CSV."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loaners_' + timestamp + '.csv"'

    can_view_student = request.user.has_perm('repair_tracker.view_loaner_student_info')

    writer = csv.writer(response)

    headers = [
        'ID', 'Device Name', 'DAM ID', 'Serial Number',
        'Status', 'Device Condition', 'Purchase Date',
        'Total Checkouts', 'Notes',
    ]
    if can_view_student:
        headers += [
            'Current Student Name', 'Current Student ID',
            'Checkout Date', 'Expected Return', 'Checked Out By',
        ]

    writer.writerow(headers)

    count = queryset.count()

    for loaner in queryset:
        row = [
            loaner.id,
            loaner.device_name,
            loaner.device_DAM_ID or '',
            loaner.device_serial or '',
            loaner.get_status_display(),
            loaner.get_device_condition_display(),
            loaner.purchase_date.strftime('%Y-%m-%d') if loaner.purchase_date else '',
            loaner.get_checkout_count(),
            loaner.notes or '',
        ]
        if can_view_student:
            row += [
                str(loaner.current_district_member) if loaner.current_district_member else '',
                loaner.current_checkout_date.strftime('%Y-%m-%d') if loaner.current_checkout_date else '',
                loaner.current_expected_return.strftime('%Y-%m-%d') if loaner.current_expected_return else '',
                loaner.current_checked_out_by.username if loaner.current_checked_out_by else '',
            ]
        writer.writerow(row)

    pii_note = ' [included student PII]' if can_view_student else ' [PII excluded]'
    _log_export(request, 'Loaners CSV export - ' + str(count) + ' record(s)' + pii_note, count)

    return response

export_loaners_csv.short_description = "Export selected loaners to CSV"


# ==============================================================
# CHECKOUT HISTORY
# ==============================================================

def export_checkout_history_csv(modeladmin, request, queryset):
    """Export selected LoanerCheckoutHistory records to CSV."""
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="checkout_history_' + timestamp + '.csv"'

    can_view_student = request.user.has_perm('repair_tracker.view_loaner_student_info')

    writer = csv.writer(response)

    headers = [
        'ID', 'Loaner Device', 'DAM ID', 'Serial',
        'Checkout Date', 'Expected Return', 'Returned Date',
        'Days Out', 'Overdue',
        'Checked Out By', 'Returned By',
        'Condition Out', 'Condition In',
        'Checkout Notes', 'Return Notes',
    ]
    if can_view_student:
        headers += ['Student Name', 'Student ID']

    writer.writerow(headers)

    count = queryset.count()

    for record in queryset.select_related('loaner', 'checked_out_by', 'returned_by'):
        row = [
            record.id,
            record.loaner.device_name,
            record.loaner.device_DAM_ID or '',
            record.loaner.device_serial or '',
            record.checkout_date.strftime('%Y-%m-%d'),
            record.expected_return_date.strftime('%Y-%m-%d'),
            record.returned_date.strftime('%Y-%m-%d') if record.returned_date else 'Still Out',
            record.days_checked_out(),
            'Yes' if record.is_overdue() else 'No',
            record.checked_out_by.username if record.checked_out_by else '',
            record.returned_by.username if record.returned_by else '',
            record.get_device_condition_out_display(),
            record.get_device_condition_in_display() if record.device_condition_in else '',
            record.checkout_notes or '',
            record.return_notes or '',
        ]
        if can_view_student:
            row += [
            str(record.district_member) if record.district_member else '',
            ]
        writer.writerow(row)

    pii_note = ' [included student PII]' if can_view_student else ' [PII excluded]'
    _log_export(request, 'Checkout History CSV export - ' + str(count) + ' record(s)' + pii_note, count)

    return response

export_checkout_history_csv.short_description = "Export selected checkout history to CSV"


# ==============================================================
# AUDIT LOG
# ==============================================================

def export_audit_log_csv(modeladmin, request, queryset):
    """Export selected AuditLog records to CSV. Superuser only."""
    if not request.user.is_superuser:
        modeladmin.message_user(request, "Only superusers can export audit logs.", level='error')
        return

    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_log_' + timestamp + '.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Timestamp', 'Username', 'Action',
        'Object', 'IP Address', 'User Agent',
        'Justification', 'Legitimate Educational Interest',
    ])

    count = queryset.count()

    for log in queryset:
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.username,
            log.get_action_display(),
            log.object_repr or '',
            log.ip_address or '',
            log.user_agent or '',
            log.justification or '',
            'Yes' if log.legitimate_educational_interest else 'No',
        ])

    _log_export(request, 'Audit Log CSV export - ' + str(count) + ' record(s) [superuser action]', count)

    return response

export_audit_log_csv.short_description = "Export selected audit logs to CSV (Superuser only)"
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from Base_Models.models import District_Location
from Inventory.models import District_Device_Inventory 
from .models import District_Device_Audit, Individual_AuditDevice
import json



# ============================================================================
# AUDIT DASHBOARD  -  /audit/
# ============================================================================

@login_required
def audit_dashboard(request):
    locations = District_Location.objects.all().order_by('school', 'room')

    location_data = []
    for loc in locations:
        latest_audit = (
            District_Device_Audit.objects
            .filter(location=loc)
            .order_by('-started_at')
            .first()
        )
        device_count = District_Device_Inventory.objects.filter(location=loc).count()
        location_data.append({
            'location': loc,
            'latest_audit': latest_audit,
            'device_count': device_count,
        })

    schools = {}
    for item in location_data:
        school = item['location'].school
        if school not in schools:
            schools[school] = []
        schools[school].append(item)

    return render(request, 'audit_dashboard.html', {'schools': schools})


# ============================================================================
# START NEW AUDIT  -  /audit/<location_id>/start/
# ============================================================================

@login_required
def start_audit(request, location_id):
    location = get_object_or_404(District_Location, pk=location_id)
    inventory_devices = District_Device_Inventory.objects.filter(location=location)

    if not inventory_devices.exists():
        messages.warning(
            request,
            f"No devices are assigned to {location} in inventory. "
            "Please update inventory before auditing."
        )
        return redirect('audit_dashboard')

    audit = District_Device_Audit.objects.create(
        location=location,
        auditor=request.user,
    )
    Individual_AuditDevice.objects.bulk_create([
        Individual_AuditDevice(audit=audit, device=device)
        for device in inventory_devices
    ])

    messages.success(request, f"New audit started for {location}.")
    return redirect('perform_audit', audit_id=audit.pk)


# ============================================================================
# PERFORM AUDIT  -  /audit/session/<audit_id>/
# ============================================================================

@login_required
def perform_audit(request, audit_id):
    audit = get_object_or_404(
        District_Device_Audit.objects.select_related('location', 'auditor'),
        pk=audit_id,
    )

    if request.method == 'POST':
        audit_records = Individual_AuditDevice.objects.filter(
            audit=audit
        ).select_related('device')

        for record in audit_records:
            was_found_before = record.found
            is_found_now = request.POST.get(f'found_{record.id}') == 'on'
            note = request.POST.get(f'notes_{record.id}', '').strip()

            if is_found_now and not was_found_before:
                now = timezone.now()
                record.found_at = now

                # Write last_seen_at and last_seen_location back to the
                # inventory record so it's visible everywhere in the system.
                device = record.device
                device.last_seen_at = now
                device.last_seen_location = audit.location
                device.save(update_fields=['last_seen_at', 'last_seen_location'])

            record.found = is_found_now
            record.notes = note
            record.save()

        messages.success(request, "Audit progress saved.")
        return redirect('perform_audit', audit_id=audit.pk)

    # ── GET ──────────────────────────────────────────────────────────────────
    audit_devices = list(
        Individual_AuditDevice.objects
        .filter(audit=audit)
        .select_related(
            'device',
            'device__model_type',
            'device__location',
            'device__last_seen_location',   # pre-fetch FK so template hits no extra queries
        )
        .order_by('device__asset_name')
    )

    # For devices not yet found this session, look up the most recent
    # found_at AND the location of that sighting from any prior audit.
    # We do this in the view because Django templates cannot call .filter().
    device_ids_not_yet_found = [
        ad.device_id for ad in audit_devices if not ad.found_at
    ]

    prior_time_map = {}     # device_id -> datetime
    prior_location_map = {} # device_id -> District_Location instance

    if device_ids_not_yet_found:
        # Step 1: find the most recent found_at per device across all prior audits
        prior_timestamps = (
            Individual_AuditDevice.objects
            .filter(device_id__in=device_ids_not_yet_found, found=True)
            .exclude(audit=audit)
            .values('device_id')
            .annotate(last_found=Max('found_at'))
        )
        prior_time_map = {row['device_id']: row['last_found'] for row in prior_timestamps}

        # Step 2: for each device, fetch the audit record that matches that
        # exact timestamp so we can pull its location.
        if prior_time_map:
            from django.db.models import Q
            import functools, operator

            # Build a filter: (device_id=X AND found_at=T) OR (device_id=Y AND found_at=U) ...
            conditions = [
                Q(device_id=dev_id, found_at=ts)
                for dev_id, ts in prior_time_map.items()
            ]
            combined = functools.reduce(operator.or_, conditions)

            matching_records = (
                Individual_AuditDevice.objects
                .filter(combined)
                .select_related('audit__location')
            )
            for rec in matching_records:
                prior_location_map[rec.device_id] = rec.audit.location

    # Attach both values directly onto the object so the template is clean.
    for ad in audit_devices:
        ad.prior_found_at       = prior_time_map.get(ad.device_id)
        ad.prior_found_location = prior_location_map.get(ad.device_id)

    context = {
        'audit': audit,
        'audit_devices': audit_devices,
        'found_count': audit.found_count(),
        'missing_count': audit.missing_count(),
        'total_count': audit.total_devices(),
        'completion_pct': audit.completion_percentage(),
    }
    return render(request, 'perform_audit.html', context)


# ============================================================================
# COMPLETE AUDIT  -  /audit/session/<audit_id>/complete/
# ============================================================================

@login_required
def complete_audit(request, audit_id):
    audit = get_object_or_404(District_Device_Audit, pk=audit_id)
    if request.method == 'POST':
        audit.complete()
        messages.success(
            request,
            f"Audit for {audit.location} marked complete. "
            f"{audit.found_count()} of {audit.total_devices()} devices found."
        )
        return redirect('audit_dashboard')
    return redirect('perform_audit', audit_id=audit_id)


# ============================================================================
# AUDIT HISTORY  -  /audit/<location_id>/history/
# ============================================================================

@login_required
def audit_history(request, location_id):
    location = get_object_or_404(District_Location, pk=location_id)
    audits = (
        District_Device_Audit.objects
        .filter(location=location)
        .prefetch_related('audit_devices__device')
        .order_by('-started_at')
    )
    return render(request, 'audit_history.html', {'location': location, 'audits': audits})

@login_required

def scan_device(request, audit_id):
    """Called via AJAX when a QR code is scanned during an audit."""
    audit = get_object_or_404(District_Device_Audit, pk=audit_id)

    if audit.is_complete:
        return JsonResponse({'status': 'error', 'message': 'Audit is complete.'}, status=400)

    data = json.loads(request.body)
    scanned_value = data.get('value', '').strip()

    # Try matching asset_id (numeric) or serial_number
    record = None
    if scanned_value.isdigit():
        record = Individual_AuditDevice.objects.filter(
            audit=audit, device__asset_id=int(scanned_value)
        ).select_related('device').first()

    if not record:
        record = Individual_AuditDevice.objects.filter(
            audit=audit, device__serial_number__iexact=scanned_value
        ).select_related('device').first()

    if not record:
        return JsonResponse({'status': 'not_found', 'message': f'No device matched: {scanned_value}'})

    if not record.found:
        now = timezone.now()
        record.found = True
        record.found_at = now
        record.save()

        device = record.device
        device.last_seen_at = now
        device.last_seen_location = audit.location
        device.save(update_fields=['last_seen_at', 'last_seen_location'])

    return JsonResponse({
        'status': 'ok',
        'record_id': record.id,
        'asset_name': record.device.asset_name,
        'asset_id': record.device.asset_id,
        'already_found': record.found,
    })
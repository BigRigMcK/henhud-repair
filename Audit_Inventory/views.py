from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max

from Inventory.models import District_Device_Inventory, District_Location
from .models import District_Device_Audit, Individual_AuditDevice


# ============================================================================
# AUDIT DASHBOARD  —  /audit/
# ============================================================================

@login_required
def audit_dashboard(request):
    """
    Show all locations grouped by school.
    Each location card shows the most recent audit's date, who ran it,
    and a found/total summary so techs know what needs attention.
    """
    locations = District_Location.objects.all().order_by('school', 'room')

    # Annotate each location with its most recent audit
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

    # Group by school name for the template
    schools = {}
    for item in location_data:
        school = item['location'].school
        if school not in schools:
            schools[school] = []
        schools[school].append(item)

    context = {
        'schools': schools,  # dict: {school_name: [location_data, ...]}
    }
    return render(request, 'audit_dashboard.html', context)


# ============================================================================
# START NEW AUDIT  —  /audit/<location_id>/start/
# ============================================================================

@login_required
def start_audit(request, location_id):
    """
    Always creates a fresh audit record for this location.
    Pre-populates Individual_AuditDevice rows for every device at that location.
    Redirects immediately into perform_audit.
    """
    location = get_object_or_404(District_Location, pk=location_id)

    inventory_devices = District_Device_Inventory.objects.filter(location=location)

    if not inventory_devices.exists():
        messages.warning(
            request,
            f"No devices are assigned to {location} in inventory. "
            "Please update inventory before auditing."
        )
        return redirect('audit_dashboard')

    # Create a brand-new audit record
    audit = District_Device_Audit.objects.create(
        location=location,
        auditor=request.user,
    )

    # Bulk-create one row per device
    Individual_AuditDevice.objects.bulk_create([
        Individual_AuditDevice(audit=audit, device=device)
        for device in inventory_devices
    ])

    messages.success(request, f"New audit started for {location}.")
    return redirect('perform_audit', audit_id=audit.pk)


# ============================================================================
# PERFORM AUDIT  —  /audit/session/<audit_id>/
# ============================================================================

@login_required
def perform_audit(request, audit_id):
    """
    The main audit-taking view.
    Techs check off each device as found and optionally add notes.
    Saving does NOT close the audit — use complete_audit for that.
    """
    audit = get_object_or_404(
        District_Device_Audit.objects.select_related('location', 'auditor'),
        pk=audit_id,
    )

    if request.method == 'POST':
        audit_records = Individual_AuditDevice.objects.filter(audit=audit)

        for record in audit_records:
            was_found_before = record.found
            is_found_now = request.POST.get(f'found_{record.id}') == 'on'
            note = request.POST.get(f'notes_{record.id}', '').strip()

            # Only stamp found_at the first time it transitions to found
            if is_found_now and not was_found_before:
                record.found_at = timezone.now()

            record.found = is_found_now
            record.notes = note
            record.save()

        messages.success(request, "Audit progress saved.")
        return redirect('perform_audit', audit_id=audit.pk)

    # GET — build context
    audit_devices = list(
        Individual_AuditDevice.objects
        .filter(audit=audit)
        .select_related('device', 'device__model_type', 'device__location')
        .order_by('device__asset_name')
    )

    # For devices not yet found this session, find the most recent found_at
    # from any prior audit so the template can show "Last seen <date>".
    # This is done in the view — Django templates cannot call .filter().
    device_ids_not_found = [
        ad.device_id for ad in audit_devices if not ad.found_at
    ]
    if device_ids_not_found:
        from django.db.models import Max
        prior_qs = (
            Individual_AuditDevice.objects
            .filter(device_id__in=device_ids_not_found, found=True)
            .exclude(audit=audit)
            .values('device_id')
            .annotate(last_found=Max('found_at'))
        )
        prior_map = {row['device_id']: row['last_found'] for row in prior_qs}
    else:
        prior_map = {}

    # Attach prior_found_at directly onto each object so the template
    # can access {{ ad.prior_found_at }} without any custom filters.
    for ad in audit_devices:
        ad.prior_found_at = prior_map.get(ad.device_id)

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
# COMPLETE AUDIT  —  /audit/session/<audit_id>/complete/
# ============================================================================

@login_required
def complete_audit(request, audit_id):
    """
    Marks the audit as complete and redirects back to the dashboard.
    Only accepts POST to prevent accidental completion via link.
    """
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
# AUDIT HISTORY  —  /audit/<location_id>/history/
# ============================================================================

@login_required
def audit_history(request, location_id):
    """
    Show all past audits for a specific location so techs can compare
    results over time and see when each device was last seen.
    """
    location = get_object_or_404(District_Location, pk=location_id)
    audits = (
        District_Device_Audit.objects
        .filter(location=location)
        .prefetch_related('audit_devices__device')
        .order_by('-started_at')
    )

    context = {
        'location': location,
        'audits': audits,
    }
    return render(request, 'audit_history.html', context)
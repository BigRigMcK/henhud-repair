from django.shortcuts import render, redirect
from django.contrib import messages
from Inventory.models import District_Device_Inventory, District_Location
from .models import District_Device_Audit, Individual_AuditDevice
from django.utils import timezone
from .forms import *

def perform_audit(request, location):
    # 1. Fetch/Create the Audit header for this location
    audit, created = District_Device_Audit.objects.get_or_create(location=location)

    # 2. Get all devices currently assigned to this location in Inventory
    inventory_devices = District_Device_Inventory.objects.filter(
        location=location
    ).select_related('location', 'model_type', 'current_status',)
    
    if request.user.is_authenticated:
            audit.auditor = request.user
            audit.save()
    if not inventory_devices.exists():
        district_location = District_Location.objects.get(id=location)
        #messages.warning(request, f"No devices found for location: {district_location}")
        return render(request, 'perform_audit.html', {'no_devices': True, 'district_location': district_location})

    # 3. Ensure every inventory device has a corresponding Individual_AuditDevice entry
    existing_ids = Individual_AuditDevice.objects.filter(audit=audit).values_list('device_id', flat=True)
    new_audit_entries = [
        Individual_AuditDevice(audit=audit, device=device)
        for device in inventory_devices if device.id not in existing_ids
    ]
    if new_audit_entries:
        Individual_AuditDevice.objects.bulk_create(new_audit_entries)

    # 4. Handle Save (POST)
    if request.method == 'POST':
        audit_records = Individual_AuditDevice.objects.filter(audit=audit)
        for record in audit_records:
            # Checkbox names are 'found_{{ record.id }}'
            is_found = request.POST.get(f'found_{record.id}') == 'on'

            
            # Only update found_at if status changes to True
            if is_found and not record.found:
                record.found_at = timezone.now()
            
            record.found = is_found
            record.save()
            
        messages.success(request, f"Audit for {location} saved successfully.")
        return redirect('perform_audit', location=location)

    # 5. Prepare data for template
    audit_devices = Individual_AuditDevice.objects.filter(audit=audit).select_related('device', 'device__model_type')
    district_location = District_Location.objects.get(id=location)

    context = {
        'audit_devices': audit_devices,
        'audit': audit,
        'district_location': district_location,
        'location': location,
        
        'no_devices': False,
    }
    return render(request, 'perform_audit.html', context)

def audit_dashboard(request):

    locations = District_Location.objects.all()


    context = {

        'locations': locations,

    }

    return render(request, 'audit_dashboard.html', context)
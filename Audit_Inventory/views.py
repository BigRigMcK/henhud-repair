from django.shortcuts import render
from django.contrib import messages
from Inventory.models import District_Device_Inventory
from .models import District_Device_Audit, Individual_AuditDevice

def perform_audit(request, location):
    devices = District_Device_Inventory.objects.filter(
        location=location
    ).select_related('location', 'model_type', 'current_status')

    # Handle empty database / no devices at location
    if not devices.exists():
        messages.warning(request, f"No devices found for this location.")
        context = {
            'audit_devices': [],
            'audit': None,
            'no_devices': True,
        }
        return render(request, 'perform_audit.html', context)

    audit, created = District_Device_Audit.objects.get_or_create(location=location)

    existing_device_ids = Individual_AuditDevice.objects.filter(
        audit=audit
    ).values_list('device_id', flat=True)
    
    new_audit_devices = [
        Individual_AuditDevice(audit=audit, device=device)
        for device in devices
        if device.id not in existing_device_ids
    ]
    if new_audit_devices:
        Individual_AuditDevice.objects.bulk_create(new_audit_devices)

    audit_devices = Individual_AuditDevice.objects.filter(
        audit=audit
    ).select_related('device')

    context = {
        'audit_devices': audit_devices,
        'audit': audit,
        'no_devices': False,
    }
    return render(request, 'perform_audit.html', context)

def audit_dashboard(request):

    context = {}

    return render(request, 'audit_dashboard.html', context)
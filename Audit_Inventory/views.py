from django.shortcuts import render

# Create your views here.
def perform_audit(request, location):
    devices = Device.objects.filter(location=location)   # or whatever your filter is
    
    # If audit already exists, load existing results
    audit, created = Audit.objects.get_or_create(
        location=location, 
        # other identifying fields...
    )
    
    # Create AuditDevice entries for every device (if not exist)
    for device in devices:
        AuditDevice.objects.get_or_create(audit=audit, device=device)
    
    # Now query with status
    audit_devices = AuditDevice.objects.filter(audit=audit).select_related('device')
    
    context = {'audit_devices': audit_devices, 'audit': audit}
    return render(request, 'audit/perform_audit.html', context)
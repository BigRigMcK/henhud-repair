from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, F, ExpressionWrapper, IntegerField
from django.db.models.functions import Now, TruncDate
from datetime import date
import hashlib

from .models import District_Member, District_Member_DeviceAssignment
from repair_tracker.audit_models import AuditLog
from Inventory.models import District_Device_Inventory



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


def _hash_for_search(value, hash_key):
    """
    Reproduce exactly what django-searchable-encrypted-fields SearchField
    stores in the database via get_prep_value():

        stored = "xx" + sha256( (value + hash_key).encode() ).hexdigest()

    Source: encrypted_fields/fields.py — get_prep_value()
    """
    SEARCH_HASH_PREFIX = "xx"
    raw = str(value) + hash_key
    return SEARCH_HASH_PREFIX + hashlib.sha256(raw.encode()).hexdigest()


# ============================================================================
# ASSIGNMENT LIST — active checkouts + history tab
# ============================================================================

@login_required
def assignment_list(request):
    tab = request.GET.get('tab', 'active')

    active_assignments = District_Member_DeviceAssignment.objects.filter(
        returned_date__isnull=True
    ).select_related('district_member', 'device', 'assigned_by').order_by('-assigned_date')

    history_assignments = District_Member_DeviceAssignment.objects.filter(
        returned_date__isnull=False
    ).select_related('district_member', 'device', 'assigned_by').order_by('-returned_date')[:100]

    

    context = {
        'active_assignments': active_assignments,
        'history_assignments': history_assignments,
        'active_count': active_assignments.count(),
        'tab': tab,
    
    }
    return render(request, 'members/assignment_list.html', context)


# ============================================================================
# CHECKOUT — assign a device to a district member
# ============================================================================

@login_required
def assignment_checkout(request):
    if request.method == 'POST':
        device_pk = request.POST.get('device_pk')
        member_pk = request.POST.get('member_pk')
        notes = request.POST.get('notes', '').strip()

        if not device_pk or not member_pk:
            messages.error(request, 'Please select both a device and a district member.')
            return redirect('assignment_checkout')

        device = get_object_or_404(District_Device_Inventory, pk=device_pk)
        member = get_object_or_404(District_Member, pk=member_pk)

        already_out = District_Member_DeviceAssignment.objects.filter(
            device=device,
            returned_date__isnull=True
        ).first()

        if already_out:
            messages.error(
                request,
                f'Device "{device.asset_name}" (Asset ID: {device.asset_id}) is already '
                f'checked out and has not been returned yet.'
            )
            return redirect('assignment_checkout')

        assignment = District_Member_DeviceAssignment.objects.create(
            district_member=member,
            device=device,
            assigned_date=timezone.now().date(),
            assigned_by=request.user,
            notes=notes,
        )

        _audit(request, 'CREATE', assignment, changes={
            'action': 'Device checked out',
            'device': str(device),
            'member': member.get_audit_representation(),
        })

        messages.success(
            request,
            f'Device "{device.asset_name}" successfully checked out to Member #{member.pk}.'
        )
        return redirect('assignment_list')

    return render(request, 'members/assignment_checkout.html')


# ============================================================================
# CHECK-IN — mark a device as returned
# ============================================================================

@login_required
def assignment_checkin(request, pk):
    assignment = get_object_or_404(District_Member_DeviceAssignment, pk=pk)

    if assignment.returned_date is not None:
        messages.warning(request, 'This device has already been checked in.')
        return redirect('assignment_list')

    if request.method == 'POST':
        return_notes = request.POST.get('return_notes', '').strip()
        assignment.returned_date = timezone.now().date()
        assignment.save()

        if return_notes:
            assignment.notes = (assignment.notes + '\n\n[Return Notes]: ' + return_notes).strip()
            assignment.save(update_fields=['notes'])

        _audit(request, 'UPDATE', assignment, changes={
            'action': 'Device checked in / returned',
            'device': str(assignment.device),
            'member': assignment.district_member.get_audit_representation(),
            'returned_date': str(assignment.returned_date),
        })

        messages.success(
            request,
            f'Device "{assignment.device.asset_name}" successfully checked in.'
        )
        return redirect('assignment_list')

    return render(request, 'members/assignment_checkin.html', {'assignment': assignment})


# ============================================================================
# MEMBER DETAIL — full assignment history for one district member
# ============================================================================

@login_required
def member_detail(request, pk):
    member = get_object_or_404(District_Member, pk=pk)
    can_view_pii = request.user.has_perm('District_Member_Information.view_student_pii')

    assignments = District_Member_DeviceAssignment.objects.filter(
        district_member=member
    ).select_related('device', 'assigned_by').order_by('-assigned_date')

    active = assignments.filter(returned_date__isnull=True)
    history = assignments.filter(returned_date__isnull=False)

    context = {
        'member': member,
        'active': active,
        'history': history,
        'can_view_pii': can_view_pii,
    }
    return render(request, 'members/member_detail.html', context)


# ============================================================================
# AJAX — Device search by Asset ID or Serial Number
# ============================================================================

@login_required
def device_search_api(request):
    q = request.GET.get('q', '').strip()
    results = []

    if len(q) >= 1:
        filters = Q(serial_number__icontains=q) | Q(asset_name__icontains=q)
        if q.isdigit():
            filters |= Q(asset_id=q)

        devices = District_Device_Inventory.objects.filter(filters).select_related(
            'model_type', 'current_status'
        )[:8]

        checked_out_device_ids = set(
            District_Member_DeviceAssignment.objects.filter(
                returned_date__isnull=True
            ).values_list('device_id', flat=True)
        )

        for d in devices:
            results.append({
                'pk': d.pk,
                'asset_name': d.asset_name,
                'asset_id': d.asset_id,
                'serial_number': d.serial_number or '—',
                'model': d.model_type.Model_Type if d.model_type else '—',
                'status': str(d.current_status) if d.current_status else '—',
                'is_checked_out': d.pk in checked_out_device_ids,
            })

    return JsonResponse({'results': results})


# ============================================================================
# AJAX — Member search by name, district ID, or email (hashed exact-match)
# ============================================================================

@login_required
def member_search_api(request):
    from django.conf import settings as django_settings

    q = request.GET.get('q', '').strip()

    if len(q) < 1:
        return JsonResponse({'results': []})

    # django-searchable-encrypted-fields stores:
    #   "xx" + sha256( (plaintext + hash_key).encode() ).hexdigest()
    # We reproduce that here to do an exact DB lookup.
    found = {}  # pk → member, deduplicated across all three lookups

    # 1. Search by district ID
    try:
        id_hash = _hash_for_search(q, django_settings.SEARCH_D_M_ID_HASH_KEY)
        for m in District_Member.objects.filter(district_member_id_index=id_hash):
            found[m.pk] = m
    except Exception as e:
        pass

    # 2. Search by full name
    try:
        name_hash = _hash_for_search(q, django_settings.SEARCH_D_M_NME_HASH_KEY)
        for m in District_Member.objects.filter(district_member_name_index=name_hash):
            found[m.pk] = m
    except Exception as e:
        pass

    # 3. Search by email address
    try:
        email_hash = _hash_for_search(q, django_settings.SEARCH_D_M_EML_HASH_KEY)
        for m in District_Member.objects.filter(district_member_email_index=email_hash):
            found[m.pk] = m
    except Exception as e:
        pass

    results = []
    for m in found.values():
        results.append({
            'pk': m.pk,
            'grade': m.get_district_member_grade_display(),
            'building': m.district_member_building,
            'district_member_id': m.district_member_id or '',  # decrypted plaintext
        })


    return JsonResponse({'results': results})
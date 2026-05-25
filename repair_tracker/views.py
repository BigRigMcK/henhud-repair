
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .forms import RepairForm, RepairNoteForm 
from .models import Repair
from Inventory.models import District_Device_Inventory
from District_Member_Information.models import (
    District_Member,
    District_Member_DeviceAssignment,
)

def inputloaner(requests):
	return render(requests, 'inputloaner.html')


def tickets(requests):

	return render(requests, 'Tickets/tickets.html')


@login_required
def device_lookup_api(request):
    """
    Look up a device by DAM ID or Serial Number and return:
      - the device's canonical fields
      - the currently assigned district member (if any)

    Query params (exactly one required):
        ?dam_id=12345
        ?serial=ABC123XYZ

    Response shape:
        {
          "found": true|false,
          "reason": "ok" | "no_device_match" | "no_active_assignment" | "bad_request",
          "device": {device_name, device_DAM_ID, device_serial} | null,
          "active_member": {pk, district_member_id, name, grade, email} | null
        }
    """
    dam_id = request.GET.get('dam_id', '').strip()
    serial = request.GET.get('serial', '').strip()

    # Validate: need exactly one query param
    if not dam_id and not serial:
        return JsonResponse({
            'found': False,
            'reason': 'bad_request',
            'device': None,
            'active_member': None,
        }, status=400)

    # Build the filter — DAM ID is exact-match on asset_id, serial is case-insensitive
    if dam_id:
        device_qs = District_Device_Inventory.objects.filter(asset_id=dam_id)
    else:
        device_qs = District_Device_Inventory.objects.filter(serial_number__iexact=serial)

    device = device_qs.first()

    if not device:
        return JsonResponse({
            'found': False,
            'reason': 'no_device_match',
            'device': None,
            'active_member': None,
        })

    # Device payload — these field names match the repair form's inputs
    device_data = {
        'device_name': device.asset_name or '',
        'device_DAM_ID': device.asset_id or '',
        'device_serial': device.serial_number or '',
    }

    # Find the active assignment (returned_date IS NULL means still checked out)
    active_assignment = (
        District_Member_DeviceAssignment.objects
        .filter(device=device, returned_date__isnull=True)
        .select_related('district_member')
        .order_by('-assigned_date')
        .first()
    )

    if not active_assignment:
        return JsonResponse({
            'found': True,
            'reason': 'no_active_assignment',
            'device': device_data,
            'active_member': None,
        })

    # Build member payload — respect PII permissions
    member = active_assignment.district_member
    can_view_pii = request.user.has_perm('District_Member_Information.view_student_pii')

    active_member = {
        'pk': member.pk,
        'district_member_id': member.district_member_id or '',
        'grade': member.get_district_member_grade_display() if member.district_member_grade else '',
        'building': getattr(member, 'district_member_building', '') or '',
        'name':  member.district_member_name  if can_view_pii else None,
        'email': member.district_member_email if can_view_pii else None,
    }

    return JsonResponse({
        'found': True,
        'reason': 'ok',
        'device': device_data,
        'active_member': active_member,
    })


#Repair Ticket
@login_required
def create_repair(request):
    can_view_pii = request.user.has_perm('District_Member_Information.view_student_pii')
    if request.method == 'POST':
        form = RepairForm(request.POST, user=request.user)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.created_by = request.user  # Set the creator
            repair.save()
            messages.success(request, 'Repair created successfully!')
            return redirect('repair_detail', pk=repair.pk)  # Adjust URL name
        else:
            print(form.errors)
    else:
        form = RepairForm(user=request.user)

    context = {
    'form': form, 
    'action': 'Create',
    'can_view_pii' : can_view_pii

    }

    return render(request, 'repair_form.html', context)


@login_required
def edit_repair(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    can_view_pii = request.user.has_perm('District_Member_Information.view_student_pii')
    
    if request.method == 'POST':
        form = RepairForm(request.POST, instance=repair, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Repair updated successfully!')
            return redirect('repair_list')
    else:
        form = RepairForm(instance=repair, user=request.user)
    

    context = {
        'form': form, 
        'action': 'Edit',
        'repair': repair,
        'can_view_pii' : can_view_pii
    }


    return render(request, 'repair_form.html', context)

@login_required
def repair_detail(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    
    # Check if user can view student info
    can_view_student_info = request.user.has_perm('repair_tracker.view_student_info')
    is_technician = request.user.groups.filter(name="Technicians").exists()
    
    context = {
        'repair': repair,
        'can_view_student_info': can_view_student_info,
        'is_technician': is_technician,
        'note_form' : RepairNoteForm(),
    }
    
    return render(request, 'repair_detail.html', context)


from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def repair_list(request):
    # Get all repairs
    repairs = Repair.objects.all().select_related('assigned_to', 'loaner', 'created_by')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'exclude_completed')
    search_query = request.GET.get('search', '')
    assigned_filter = request.GET.get('assigned', '')
    sort_by = request.GET.get('sort', '-created_at')  # default sort
    
    # Apply status filter
    if status_filter == 'exclude_completed':
        repairs = repairs.exclude(status__in=['completed', 'vineetha_completed'])
    elif status_filter:
        repairs = repairs.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        repairs = repairs.filter(
            Q(device_name__icontains=search_query) |
            Q(device_serial__icontains=search_query) |
            Q(device_DAM_ID__icontains=search_query)
        )
    
    # Apply assignment filter
    if assigned_filter == 'unassigned':
        repairs = repairs.filter(assigned_to__isnull=True)
    elif assigned_filter == 'me':
        repairs = repairs.filter(assigned_to=request.user)
    
    # Order by most recent
    VALID_SORTS = ['device_serial', '-device_serial', 'created_at', '-created_at']
    if sort_by not in VALID_SORTS:
        sort_by = '-created_at'
    repairs = repairs.order_by(sort_by)


    # NEW — multi-select building filter
    building_filter = request.GET.getlist('building')   # returns []  or  ['HHS', 'BMS', ...]
    
    if building_filter:
        repairs = repairs.filter(
            district_member__district_member_building__in=building_filter
        )

    # NEW — building sort handling (extends your existing sort logic)
    sort_by = request.GET.get('sort', '')
    valid_sorts = {
        'device_serial', '-device_serial',
        'building', '-building',
        # ... whatever else you allow ...
    }
    if sort_by in valid_sorts:
        # Map "building" sort to the actual FK path
        sort_map = {
            'building':  'district_member__district_member_building',
            '-building': '-district_member__district_member_building',
        }
        repairs = repairs.order_by(sort_map.get(sort_by, sort_by))

    # NEW — list of buildings for the checkbox panel
    # Use the model's choices if you have them, or DISTINCT values from the DB
    all_buildings = (
        District_Member.objects
        .exclude(district_member_building__isnull=True)
        .exclude(district_member_building='')
        .values_list('district_member_building', flat=True)
        .distinct()
        .order_by('district_member_building')
    )

    # Get counts for badges
    current_count = Repair.objects.exclude(status__in=['completed', 'vineetha_completed']).count()
    sent_to_dell_count = Repair.objects.filter(status='sent_to_dell').count()
    in_progress_count = Repair.objects.filter(
        status__in=['sent_to_dell', 'on_site_repair', 'awaiting_parts', 'returned_from_dell']
    ).count()
    completed_count = Repair.objects.filter(
        status__in=['completed', 'vineetha_completed']
    ).count()
    total_count = Repair.objects.count()
    
    # Pagination
    paginator = Paginator(repairs, 25)  # Show 25 repairs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check permissions
    can_view_student_info = request.user.has_perm('repair_tracker.view_student_info')
    
    context = {
        'repairs': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'status_filter': status_filter,
        'search_query': search_query,
        'assigned_filter': assigned_filter,
        'can_view_student_info': can_view_student_info,
        'current_count': current_count,
        'sent_to_dell_count': sent_to_dell_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'total_count' : total_count,
        'sort_by' : sort_by,
        'building_filter': building_filter,
        'all_buildings':   all_buildings,
        }
    
    return render(request, 'repair_list.html', context)



@login_required
def repair_print(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    can_view_student_info = request.user.has_perm('repair_tracker.view_student_info')
    return render(request, 'repair_print.html', {
        'repair': repair,
        'can_view_student_info': can_view_student_info,
        'now': timezone.now(),
    })
@login_required
def add_repair_note(request, pk):
    repair = get_object_or_404(Repair, pk=pk)

    if request.method == 'POST':
        form = RepairNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.repair = repair
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note added.')
            return redirect('repair_detail', pk=repair.pk)
    # If GET or invalid, fall back to detail page
    return redirect('repair_detail', pk=repair.pk)
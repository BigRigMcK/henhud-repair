
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import RepairForm 
from .models import Repair
from django.utils import timezone




def inputloaner(requests):
	return render(requests, 'inputloaner.html')


def tickets(requests):

	return render(requests, 'Tickets/tickets.html')


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
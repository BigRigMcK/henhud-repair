
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import RepairForm
from .models import Repair


# Create your views here.
def home(request):
    if request.method == 'POST':
        # 1. Fill the form with the data the user sent
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # 2. Log the user in
            user = form.get_user()
            login(request, user)
            return redirect('repairs/') # Refresh to show the logged-in state
    else:
        # 3. Just show a blank form for GET requests
        form = AuthenticationForm()
    return render(request, 'home.html', {'form': form})


def inputloaner(requests):
	return render(requests, 'inputloaner.html')


def tickets(requests):

	return render(requests, 'Tickets/tickets.html')


#Repair Ticket
@login_required
def create_repair(request):
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
    
    return render(request, 'repair_form.html', {'form': form, 'action': 'Create'})

@login_required
def edit_repair(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    
    if request.method == 'POST':
        form = RepairForm(request.POST, instance=repair, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Repair updated successfully!')
            return redirect('repair_list')
    else:
        form = RepairForm(instance=repair, user=request.user)
    
    return render(request, 'repair_form.html', {
        'form': form, 
        'action': 'Edit',
        'repair': repair
    })

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
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    assigned_filter = request.GET.get('assigned', '')
    
    # Apply status filter
    if status_filter:
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
    repairs = repairs.order_by('-created_at')
    
    # Get counts for badges
    total_count = Repair.objects.count()
    sent_to_dell_count = Repair.objects.filter(status='sent_to_dell').count()
    in_progress_count = Repair.objects.filter(
        status__in=['sent_to_dell', 'on_site_repair', 'awaiting_parts', 'returned_from_dell']
    ).count()
    completed_count = Repair.objects.filter(
        status__in=['fixed_by_tech', 'returned']
    ).count()
    
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
        'total_count': total_count,
        'sent_to_dell_count': sent_to_dell_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'repair_list.html', context)
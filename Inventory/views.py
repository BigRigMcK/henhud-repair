from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.db.models.functions import Cast
from django.db.models import CharField
from .forms import District_Device_Inventory_Form
from .models import District_Device_Inventory
from repair_tracker.models import Repair


# Views

def inventory_home(request):


	return render(request, 'inventory_home.html' , {})


@login_required
def inventory_add_new_device(request):

	if request.method == 'POST':
		form = District_Device_Inventory_Form(request.POST, user=request.user)
		if form.is_valid():
			device = form.save(commit=False)
			device.created_by = request.user
			device.save()
			messages.success(request, 'Device was Added to System Successfully!!')
			return redirect('inventory_detail', pk=device.pk)
		else:
			print(form.errors)
	else:
		form = District_Device_Inventory_Form(user=request.user)

	return render(request, 'inventory_device_form.html', {'form':form, 'action':'Create'})

@login_required
def edit_inventory(request, pk):
	device = get_object_or_404(District_Device_Inventory, pk=pk)

	if request.method == 'POST':
		form = District_Device_Inventory_Form(request.POST, instance=device, user=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, f"Device : {device.asset_id} has been Updated Successfully")
			return redirect('inventory_detail',pk=device.pk)
		else:
			print(form.errors)
	else:
		form = District_Device_Inventory_Form(instance=device, user=request.user)

	return render(request, 'inventory_device_form.html', {
		'form': form,
		'action': 'Edit',
		'device' : device
		})

@login_required
def inventory_detail(request, pk):
	device = get_object_or_404(District_Device_Inventory, pk=pk)

	repairs = Repair.objects.filter(
    Q(device_DAM_ID=device.asset_id) |
    Q(device_serial__iexact=device.serial_number)
	).select_related('assigned_to', 'created_by')

 # Check if user can view student info
    #can_view_student_info = request.user.has_perm('repair_tracker.view_student_info')
    #is_technician = request.user.groups.filter(name="Technicians").exists()

	context = {
	'device' : device,
	'repairs': repairs,

	}

	return render(request, 'inventory_device_detail.html', context)

def inventory_list(request):

	devices = District_Device_Inventory.objects.all()



	 # Pagination
	paginator = Paginator(devices, 25)  # Show 25 repairs per page
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	context = {
	  'devices': page_obj,
	  'page_obj': page_obj,
	  'is_paginated': page_obj.has_other_pages(),
	  #'sort_by' : sort_by,
	}

	return render(request, 'inventory_list.html', context)

def inventory_search(request):
	q = request.GET.get('q', '').strip()
	results = []
	if len(q) >= 2:
        # Try matching asset_id numerically first, then serial_number as text
		filters = Q(serial_number__icontains=q) | Q(asset_id__icontains=q)
		if q.isdigit():
			# Cast asset_id to text so partial matches work (e.g. "123" matches "12345")
			devices = District_Device_Inventory.objects.annotate(
				asset_id_str=Cast('asset_id', output_field=CharField())
			).filter(
				filters | Q(asset_id_str__icontains=q)
			).select_related('model_type', 'location')[:5]
		else:
			devices = District_Device_Inventory.objects.filter(filters).select_related('model_type', 'location')[:5]


		for d in devices:
			results.append({
				'id': d.pk,
				'asset_name': d.asset_name,
				'asset_id': d.asset_id,
				'serial_number': d.serial_number or '—',
				'model': d.model_type.Model_Type if d.model_type else '—',
				'location': str(d.location) if d.location else '—',
				'url': f'/inventory/inventory_detail/{d.pk}/',
			})
	return JsonResponse({'results': results})	
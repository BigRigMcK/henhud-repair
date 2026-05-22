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
from .models import District_Device_Inventory, Device_Model
from Base_Models.models import Current_Status, District_Location, District_Department
from repair_tracker.models import Repair



# Views
@login_required
def _get_filtered_inventory(request):
	"""
	Reads filter params off the request and returns a filtered queryset.
	The leading underscore is a Python convention meaning "this is for
	internal use within this module — not part of the public API."
	"""
	search_query = request.GET.get('search', '').strip()
	model_filter = request.GET.getlist('model_type')
	status_filter = request.GET.getlist('current_status')
	location_filter = request.GET.getlist('location')
	department_filter = request.GET.getlist('department')

	devices = District_Device_Inventory.objects.all().select_related(
		'model_type', 'location', 'department', 'current_status'
	).prefetch_related('student_assignments__district_member')

	if search_query:
		devices = devices.filter(
			Q(asset_id__icontains=search_query) |
			Q(serial_number__icontains=search_query) |
			Q(asset_name__icontains=search_query)
		)

	if model_filter:
		devices = devices.filter(model_type_id__in=model_filter)
	if status_filter:
		devices = devices.filter(current_status_id__in=status_filter)
	if location_filter:
		devices = devices.filter(location_id__in=location_filter)
	if department_filter:
		devices = devices.filter(department_id__in=department_filter)

	# Return both the queryset AND the active filter values, so callers
	# don't have to re-read request.GET themselves. Tuple return is fine
	# for two values; if it grew to 5+ I'd switch to a dict or dataclass.
	return devices, {
		'search_query': search_query,
		'model_filter': model_filter,
		'status_filter': status_filter,
		'location_filter': location_filter,
		'department_filter': department_filter,
	}




@login_required
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

@login_required
def inventory_list(request):
	# All the filter logic now lives in the helper. We just call it.
	devices, active_filters = _get_filtered_inventory(request)

	# Pagination
	paginator = Paginator(devices, 25)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	# No-results toast
	has_active_filter = any(active_filters.values())
	if not page_obj.object_list and has_active_filter:
		messages.warning(
			request,
			'No devices match the selected filters. Try a different filter.'
		)

	context = {
		'devices': page_obj,
		'page_obj': page_obj,
		'is_paginated': page_obj.has_other_pages(),

		# Spread the active_filters dict into the context.
		# **dict_name unpacks the dict's key/value pairs as kwargs.
		# This is equivalent to writing each key out by hand.
		**active_filters,

		# Lookup options for the dropdowns
		'model_types': Device_Model.objects.all().order_by('Model_Type'),
		'statuses': Current_Status.objects.all().order_by('Status'),
		'locations': District_Location.objects.all().order_by('school', 'room'),
		'departments': District_Department.objects.all().order_by('department'),
	}

	return render(request, 'inventory_list.html', context)

	
@login_required
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

@login_required
def inventory_export_csv(request):
	"""
	Export the currently filtered inventory list as a CSV download.
	Re-runs the same filter logic as inventory_list so the export
	matches exactly what the user is viewing on screen.
	"""
	# Delegate to the existing helper (which gates PII and writes the
	# audit log). We pass the FILTERED queryset, not the full one.
	from .csv_export_actions import write_inventory_csv

	devices, _ = _get_filtered_inventory(request)
	return write_inventory_csv(devices, request)
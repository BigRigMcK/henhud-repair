from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import District_Device_Inventory_Form
from .models import District_Device_Inventory



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

	return render(request, 'inventory_add_new_device.html', {'form':form, 'action':'Create'})

@login_required
def edit_inventory(request, pk, asset_id):
	device = get_object_or_404(District_Device_Inventory, pk=pk, asset_id=asset_id)

	if request.method == 'POST':
		form = District_Device_Inventory_Form(request.POST, instance=device, user=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, f"Device : {asset_id} has been Updated Successfully")
			return redirect('inventory_detail',pk=device.pk)
		else:
			print(form.errors)
	else:
		form = District_Device_Inventory_Form(instance=device, user=request.user)

	return render(request, 'inventory_device_edit.html', {
		'form': form,
		'action': 'Edit',
		'device' : device
		})

@login_required
def inventory_detail(request, pk):
	device = get_object_or_404(District_Device_Inventory, pk=pk)

 # Check if user can view student info
    #can_view_student_info = request.user.has_perm('repair_tracker.view_student_info')
    #is_technician = request.user.groups.filter(name="Technicians").exists()


	return render(request, 'inventory_device_detail.html', {'device': device})
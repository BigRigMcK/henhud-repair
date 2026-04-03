from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
#from .forms import RepairForm, VideoUploadForm
#from .models import Repair, Video



# Views

def inventory_home(request):


	return render(request, 'inventory_home.html' , {})
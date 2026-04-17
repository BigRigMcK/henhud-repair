
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import LoginForm

from django.utils import timezone








# Create your views here.
def home(request):
    if request.method == 'POST':
        # 1. Fill the form with the data the user sent
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # 2. Log the user in
            user = form.get_user()
            login(request, user)
            return redirect('/') # Refresh to show the logged-in state
    else:
        # 3. Just show a blank form for GET requests
        form = LoginForm()
    return render(request, 'home.html', {'form': form})

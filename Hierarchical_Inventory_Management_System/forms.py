from django import forms
from . import views
from django.contrib.auth.forms import AuthenticationForm



class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'autocomplete': 'username',
        'class': 'form-control', # Optional: for styling
        'placeholder': 'Username',
        'id': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'autocomplete': 'current-password',
        'class': 'form-control',
        'placeholder': 'Password',
        'id' : 'password',
    }))
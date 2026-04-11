from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
path('<int:location>/', views.perform_audit , name='perform_audit'),
path('', views.audit_dashboard , name='audit_dashboard'),
]
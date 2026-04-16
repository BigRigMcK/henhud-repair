from django.urls import path
from . import views

urlpatterns = [
    # Dashboard — list all locations with latest audit info
    path('', views.audit_dashboard, name='audit_dashboard'),

    # Start a brand-new audit session for a location
    path('<int:location_id>/start/', views.start_audit, name='start_audit'),

    # Take/save an in-progress audit session
    path('session/<int:audit_id>/', views.perform_audit, name='perform_audit'),

    # Mark an audit session as complete
    path('session/<int:audit_id>/complete/', views.complete_audit, name='complete_audit'),

    # View all past audits for a location
    path('<int:location_id>/history/', views.audit_history, name='audit_history'),
]
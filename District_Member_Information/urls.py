from django.urls import path
from . import views
 
urlpatterns = [
    # Assignment dashboard — active checkouts + history tab
    path('assignments/', views.assignment_list, name='assignment_list'),
 
    # Create a new checkout (assign device to member)
    path('assignments/checkout/', views.assignment_checkout, name='assignment_checkout'),
 
    # Check in a device (mark returned)
    path('assignments/<int:pk>/checkin/', views.assignment_checkin, name='assignment_checkin'),
 
    # District member detail — their full assignment history
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
 
    # AJAX endpoints
    path('api/device-search/', views.device_search_api, name='device_search_api'),
    path('api/member-search/', views.member_search_api, name='member_search_api'),
]
 
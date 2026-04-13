from django.urls import path
from . import views

urlpatterns = [
	path('', views.inventory_home , name='Inventory Home'),
	path('addnewdevice/', views.inventory_add_new_device , name='inventory_add_new_devcie'),
	path('inventory_list/', views.inventory_list , name= 'inventory_list'),
	path('inventory_detail/<int:pk>/', views.inventory_detail, name='inventory_detail'),
	path('inventory_detail/<int:pk>/edit', views.edit_inventory, name='inventory_device_edit'),
	path('search/', views.inventory_search, name='inventory_search'),



]
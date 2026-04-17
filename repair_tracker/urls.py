from django.urls import path
from . import views, pdf_views

urlpatterns = [
	
	# path('inputloaner', views.inputloaner , name="Input Loaner"),
	# path('tickets', views.tickets, name="Tickets"),
	# path('tickets/open', views.tickets, name="Tickets Open"),
	# path('tickets/closed', views.tickets, name="Tickets Closed"),
	path('', views.repair_list, name="repair_list"),
    path('create/', views.create_repair, name='create_repair'),
    path('<int:pk>/', views.repair_detail, name='repair_detail'),
    path('<int:pk>/edit/', views.edit_repair, name='edit_repair'),
    path('<int:pk>/print/', views.repair_print, name='repair_print'),
    path('<int:pk>/pdf/',   pdf_views.repair_pdf, name='repair_pdf'),

]

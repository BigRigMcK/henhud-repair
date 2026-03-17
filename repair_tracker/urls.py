from django.urls import path
from . import views

urlpatterns = [
	path('', views.home , name="home"),
	path('inputloaner', views.inputloaner , name="Input Loaner"),
	path('tickets', views.tickets, name="Tickets"),
	path('tickets/open', views.tickets, name="Tickets Open"),
	path('tickets/closed', views.tickets, name="Tickets Closed"),
	path('repairs/', views.repair_list, name="repair_list"),
    path('repairs/create/', views.create_repair, name='create_repair'),
    path('repairs/<int:pk>/', views.repair_detail, name='repair_detail'),
    path('repairs/<int:pk>/edit/', views.edit_repair, name='edit_repair'),
    path('videos/test', views.video_page, name='test_Video'),
    path('videos/test', views.video_page, name='IT_Tool_Video'),
    path('videos/', views.video_list, name='video_list'),
	path('videos/upload/', views.video_upload, name='video_upload'),
	path('videos/<int:pk>/', views.video_detail, name='video_detail'),
	

]

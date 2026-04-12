from django.urls import path
from . import views

urlpatterns = [

    path('videos/test', views.video_page, name='test_Video'),
    path('videos/test', views.video_page, name='IT_Tool_Video'),
    path('videos/', views.video_list, name='video_list'),
	path('videos/upload/', views.video_upload, name='video_upload'),
	path('videos/<int:pk>/', views.video_detail, name='video_detail'),
	
]

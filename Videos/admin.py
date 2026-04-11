from django.contrib import admin
from .models import  Video,
# Register your models here.
@admin.register(Video)
class Video(admin.ModelAdmin):
    list_display = [
        'title',    
    'description', 
    'video_file',
    'uploaded_by', 
    'uploaded_at',
    ]
    list_filter = [ 'title', 'uploaded_at']
from django.shortcuts import render
from .models import Video
from .forms import VideoUploadForm
# Create your views here.



def video_page(request):
    return render(request, 'videos/test_video.html')



@login_required
def video_list(request):
    videos = Video.objects.all().order_by('-uploaded_at')
    return render(request, 'videos/video_list.html', {'videos': videos})

@login_required
def video_upload(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.uploaded_by = request.user
            video.save()
            messages.success(request, 'Video uploaded successfully!')
            return redirect('video_list')
    else:
        form = VideoUploadForm()
    return render(request, 'videos/video_upload.html', {'form': form})

@login_required
def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return render(request, 'videos/video_detail.html', {'video': video})
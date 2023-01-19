from django.urls import path
from codion import views
app_name = 'codion'

urlpatterns = [
    path('delete-all-file/', views.delete_file, name="delete_file"),
    path('segmentation/', views.SegmentationView.as_view(), name='segmentation'),
    path('about/', views.About.as_view(), name='about'),
    path('', views.index, name='index'),
]
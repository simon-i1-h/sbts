from django.urls import path

from .views import BlobView, UploadView, CreateView


app_name = 'file'
urlpatterns = [
    path('blobs/<uuid:key>/', BlobView.as_view(), name='blob'),
    path('blobs/', UploadView.as_view(), name='upload'),
    path('files/', CreateView.as_view(), name='create'),
]

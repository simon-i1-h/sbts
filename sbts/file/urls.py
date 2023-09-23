from django.urls import path

from .views import BlobView, UploadView


app_name = 'file'
urlpatterns = [
    path('blobs/<uuid:key>/', BlobView.as_view(), name='blob'),
    path('blobs/', UploadView.as_view(), name='upload'),
]

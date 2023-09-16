from django.urls import path

from . import views


app_name = 'file'
urlpatterns = [
    path('blobs/<uuid:key>/', views.file, name='blob'),
    path('blobs/', views.upload, name='upload'),
    path('files/', views.create, name='create'),
]

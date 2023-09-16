from django.contrib import admin
from django.urls import path
import file.views
import page.views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', page.views.index, name='index'),

    path('api/blobs/<uuid:key>/', file.views.file, name='file'),
    path('api/blobs/', file.views.upload, name='upload'),
    path('api/files/', file.views.create, name='create'),
]

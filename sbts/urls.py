from django.contrib import admin
from django.urls import path
import file.views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', file.views.index, name='index'),
    path('upload/', file.views.upload, name='upload'),
    path('file/<uuid:key>/', file.views.file, name='file'),
]

from django.contrib import admin
from django.urls import include, path
import page.views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', page.views.index, name='index'),
    path('api/file/', include('file.urls')),
]

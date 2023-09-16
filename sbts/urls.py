from django.contrib import admin
from django.urls import include, path
import page.views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', page.views.TopPageView.as_view(), name='top'),
    path('api/file/', include('file.urls')),
]

from django.contrib import admin
from django.urls import include, path
from page.views import TopPageView, LoginPageView, LogoutPageView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TopPageView.as_view(), name='top'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutPageView.as_view(), name='logout'),
    path('api/file/', include('file.urls')),
]

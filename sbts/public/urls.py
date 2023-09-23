from django.urls import include, path
from sbts.page.views import top, FilePageView, LoginPageView, LogoutPageView


urlpatterns = [
    path('', top, name='top'),
    path('file/', FilePageView.as_view(), name='file'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutPageView.as_view(), name='logout'),
    path('api/file/', include('sbts.file.urls')),
]

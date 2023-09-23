from django.urls import include, path
from sbts.page.views import TopPageView, FilePageView, TicketPageView, \
    LoginPageView, LogoutPageView, CreateTicketPageView


urlpatterns = [
    path('', TopPageView.as_view(), name='top'),
    path('file/', FilePageView.as_view(), name='file'),
    path('ticket/', TicketPageView.as_view(), name='ticket'),
    path('ticket/create/', CreateTicketPageView.as_view(), name='create_ticket'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutPageView.as_view(), name='logout'),
    path('api/file/', include('sbts.file.urls')),
]

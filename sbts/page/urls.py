from django.urls import include, path
from sbts.page.views import TopPageView, FilePageView, TicketPageView, \
    LoginPageView, LogoutPageView, CreateTicketView, \
    TicketDetailPageView, CreateCommentView, CreateFileView


app_name = 'page'
urlpatterns = [
    path('', TopPageView.as_view(), name='top'),
    path('file/', FilePageView.as_view(), name='file'),
    path('file/create/', CreateFileView.as_view(), name='create_file'),
    path('ticket/', TicketPageView.as_view(), name='ticket'),
    path('ticket/create/', CreateTicketView.as_view(), name='create_ticket'),
    path('ticket/<uuid:key>/', TicketDetailPageView.as_view(), name='ticket_detail'),
    path('ticket/<uuid:key>/create/', CreateCommentView.as_view(), name='create_comment'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutPageView.as_view(), name='logout'),
    path('api/file/', include('sbts.file.urls')),
]

from django.urls import include, path
from sbts.page.views import TopPageView, FilePageView, TicketPageView, \
    LoginPageView, LogoutPageView, CreateTicketView, \
    TicketDetailPageView, CreateCommentView, CreateFileView


app_name = 'page'
urlpatterns = [
    path('', TopPageView.as_view(), name='top'),
    path('file/', FilePageView.as_view(), name='file'),
    path('ticket/', TicketPageView.as_view(), name='ticket'),
    path('ticket/<uuid:key>/', TicketDetailPageView.as_view(), name='ticket_detail'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutPageView.as_view(), name='logout'),
    path('api/page/files/', CreateFileView.as_view(), name='create_file'),
    path('api/page/tickets/', CreateTicketView.as_view(), name='create_ticket'),
    path('api/page/comments/', CreateCommentView.as_view(), name='create_comment'),
    path('api/file/', include('sbts.file.urls')),
]

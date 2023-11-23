from django.urls import include, path
from sbts.page.views import TopPageView, FilePageView, TicketPageView, \
    LoginPageView, LogoutPageView, CreateTicketView, \
    TicketDetailPageView, CreateCommentView, CreateFileView


app_name = 'page'
urlpatterns = [
    path('', TopPageView.as_view(), name='top_page'),
    path('file/', FilePageView.as_view(), name='file_page'),
    path('ticket/', TicketPageView.as_view(), name='ticket_page'),
    path('ticket/<uuid:key>/', TicketDetailPageView.as_view(), name='ticket_detail_page'),
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('logout/', LogoutPageView.as_view(), name='logout_page'),
    path('api/page/files/', CreateFileView.as_view(), name='file'),
    path('api/page/tickets/', CreateTicketView.as_view(), name='ticket'),
    path('api/page/comments/', CreateCommentView.as_view(), name='comment'),
    path('api/file/', include('sbts.file.urls')),
]

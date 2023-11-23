from django.urls import include, path
from sbts.page.views import TopPageView, FilePageView, TicketPageView, \
    LoginPageView, LogoutPageView, TicketView, TicketDetailPageView, \
    CommentView, FileView


app_name = 'page'
urlpatterns = [
    path('', TopPageView.as_view(), name='top_page'),
    path('file/', FilePageView.as_view(), name='file_page'),
    path('ticket/', TicketPageView.as_view(), name='ticket_page'),
    path('ticket/<uuid:key>/', TicketDetailPageView.as_view(), name='ticket_detail_page'),
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('logout/', LogoutPageView.as_view(), name='logout_page'),
    path('api/page/files/', FileView.as_view(), name='file'),
    path('api/page/tickets/', TicketView.as_view(), name='ticket'),
    path('api/page/comments/', CommentView.as_view(), name='comment'),
    path('api/file/', include('sbts.file.urls')),
]

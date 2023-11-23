from django.urls import include, path


urlpatterns = [
    path('', include('sbts.page.urls')),
]

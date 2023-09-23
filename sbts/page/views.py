from django.urls import reverse
from django.views.generic.base import TemplateView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from sbts.file.models import UploadedFile


class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    pass


class TopPageView(LoginRequiredTemplateView):
    template_name = 'page/top.html'


class FilePageView(LoginRequiredTemplateView):
    template_name = 'page/file.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['file_list'] = [
            {
                'kind': 'File',
                'name': f.name,
                'lastmod': f.last_modified.isoformat(' ', 'seconds'),
                'size': f.size,
                'key': str(f.key),
            }
            for f in UploadedFile.objects.all().order_by('name', 'last_modified')
        ]
        ctx['constant_map'] = {
            'url_map': {
                name: reverse(name)
                for name in ['file:upload', 'file:create']
            }
        }
        return ctx


class LoginPageView(LoginView):
    template_name = 'page/login.html'
    redirect_authenticated_user = True


class LogoutPageView(LogoutView):
    pass

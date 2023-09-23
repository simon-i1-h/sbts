from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import TemplateView, View

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from sbts.file.models import UploadedFile
from sbts.ticket.models import Ticket

import uuid


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


class TicketPageView(LoginRequiredTemplateView):
    template_name = 'page/ticket.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ticket_list'] = [
            {
                'title': t.title,
                'lastmod': '?',
                'key': t.key,
            }
            for t in Ticket.objects.sorted_tickets()
        ]
        return ctx


class CreateTicketPageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        now = timezone.now()
        Ticket.objects.create(key=uuid.uuid4(),
                              title=request.POST['title'],
                              created_at=now)

        return HttpResponseRedirect(reverse('ticket'))


class LoginPageView(LoginView):
    template_name = 'page/login.html'
    redirect_authenticated_user = True


class LogoutPageView(LogoutView):
    pass

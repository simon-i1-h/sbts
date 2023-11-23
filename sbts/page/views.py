from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import TemplateView, View

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from sbts.file.models import UploadedFile
from sbts.ticket.models import Ticket

import uuid


class LoginRequiredView(LoginRequiredMixin, View):
    raise_exception = True


class BaseFilePageView(TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_tab'] = 'file'
        return ctx


class BaseTicketPageView(TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_tab'] = 'ticket'
        return ctx


class TopPageView(TemplateView):
    template_name = 'page/top.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['text'] = settings.TOPPAGE_TEXT
        return ctx


class FilePageView(BaseFilePageView):
    template_name = 'page/file.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['file_list'] = UploadedFile.objects.all().order_by('name', 'last_modified', 'key')
        ctx['constant_map'] = {
            'url_map': {
                name: reverse(name)
                for name in ['file:upload']
            }
        }

        return ctx


class CreateFileView(LoginRequiredView):
    def post(self, request, *args, **kwargs):
        UploadedFile.objects.create_from_s3(
            key=request.POST['blobkey'],
            username=request.user.username,
            filename=request.POST['filename'],
            last_modified=timezone.now())

        return HttpResponseRedirect(reverse('file'))


class TicketPageView(BaseTicketPageView):
    template_name = 'page/ticket.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ticket_list'] = Ticket.objects.sorted_tickets()
        return ctx


class CreateTicketView(LoginRequiredView):
    def post(self, request, *args, **kwargs):
        now = timezone.now()
        Ticket.objects.create(key=uuid.uuid4(),
                              title=request.POST['title'],
                              created_at=now)

        return HttpResponseRedirect(reverse('ticket'))


class TicketDetailPageView(BaseTicketPageView):
    template_name = 'page/ticket_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ticket = Ticket.objects.get(key=kwargs['key'])
        ctx['comment_list'] = ticket.sorted_comments()
        ctx['ticket'] = ticket

        return ctx


class CreateCommentView(LoginRequiredView):
    def post(self, request, *args, **kwargs):
        now = timezone.now()
        t = Ticket.objects.get(key=kwargs['key'])
        t.comment_set.create(key=uuid.uuid4(),
                             comment=request.POST['comment'],
                             created_at=now)

        url = reverse('ticket_detail', kwargs={
            'key': kwargs['key'],
        })
        return HttpResponseRedirect(url)


class LoginPageView(LoginView):
    template_name = 'page/login.html'
    # TODO: social media fingerprinting
    # https://docs.djangoproject.com/en/4.2/topics/auth/default/#django.contrib.auth.views.LoginView
    redirect_authenticated_user = True


class LogoutPageView(LogoutView):
    pass

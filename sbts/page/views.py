from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import TemplateView, View

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from sbts.file.models import UploadedFile
from sbts.ticket.models import Ticket

import uuid


def pretty_nbytes(nbytes):
    units = ['B', 'kiB', 'MiB', 'GiB', 'TiB', 'PiB']
    i = 0
    while i < len(units) - 1 and nbytes >= 1024:
        nbytes /= 1024
        i += 1

    if nbytes % 1:
        return f'{nbytes:,.1f} {units[i]}'
    else:
        return f'{nbytes:,.0f} {units[i]}'


class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    pass


class LoginRequiredView(LoginRequiredMixin, View):
    pass


class BaseFilePageView(LoginRequiredTemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_tab'] = 'file'
        return ctx


class BaseTicketPageView(LoginRequiredTemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_tab'] = 'ticket'
        return ctx


class TopPageView(LoginRequiredTemplateView):
    template_name = 'page/top.html'


class FilePageView(BaseFilePageView):
    template_name = 'page/file.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['file_list'] = [
            {
                'name': f.name,
                'lastmod': f.last_modified.isoformat(' ', 'seconds'),
                'size': pretty_nbytes(f.size),
                'key': str(f.key),
            }
            for f in UploadedFile.objects.all().order_by('name', 'last_modified')
        ]
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
            name=request.POST['filename'],
            last_modified=timezone.now())

        return HttpResponseRedirect(reverse('file'))


class TicketPageView(BaseTicketPageView):
    template_name = 'page/ticket.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['ticket_list'] = []
        for t in Ticket.objects.sorted_tickets():
            lastcomment = t.comment_set.order_by('-last_updated').first()
            if lastcomment is None:
                lastmod = t.created_at
            else:
                lastmod = lastcomment.last_updated

            ctx['ticket_list'].append({
                'title': t.title,
                'lastmod': lastmod,
                'key': t.key,
            })

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
        ctx['comment_list'] = [
            {
                'comment': c.comment,
                'created': c.created_at,
                'last_updated': c.last_updated,
                'is_modified': c.is_modified,
                'key': c.key,
            }
            for c in ticket.sorted_comments()
        ]
        ctx['ticket'] = {
            'key': ticket.key,
        }

        return ctx


class CreateCommentView(LoginRequiredView):
    def post(self, request, *args, **kwargs):
        now = timezone.now()
        t = Ticket.objects.get(key=kwargs['key'])
        t.comment_set.create(key=uuid.uuid4(),
                             comment=request.POST['comment'],
                             created_at=now,
                             last_updated=now)

        url = reverse('ticket_detail', kwargs={
            'key': kwargs['key'],
        })
        return HttpResponseRedirect(url)


class LoginPageView(LoginView):
    template_name = 'page/login.html'
    redirect_authenticated_user = True


class LogoutPageView(LogoutView):
    pass

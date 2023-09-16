from django.urls import reverse
from django.views.generic.base import TemplateView

from file.models import UploadedFile


class TopPageView(TemplateView):
    template_name = 'page/top.html'

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

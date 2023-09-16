from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from django.urls import reverse

from file.models import UploadedFile


def index(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    context = {
        'file_list': [
            {
                'kind': 'File',
                'name': f.name,
                'lastmod': f.last_modified.isoformat(' ', 'seconds'),
                'size': f.size,
                'key': str(f.key),
            }
            for f in UploadedFile.objects.all().order_by('name')
        ],
        'constant_map': {
            'url_map': {
                name: reverse(name)
                for name in ['file:upload', 'file:create']
            }
        },
    }
    return render(request, 'page/index.html', context)

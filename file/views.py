from django.db import transaction

from django.http import HttpResponseRedirect, HttpResponseBadRequest, \
    FileResponse
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse
from .models import UploadedFile, upload_file
import tempfile
import boto3

from sbts.settings import S3_BUCKET_FILE, S3_ENDPOINT


def index(request):
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
        ]
    }
    return render(request, 'file/index.html', context)


# TODO: 分割アップロード
# -> いや、分割アップロードやめる、かも
def upload(request):
    if 'file' in request.FILES:
        key = upload_file(request.FILES['file'])
    else:
        raise HttpResponseBadRequest('invalied request (file)')

    with transaction.atomic():
        UploadedFile.objects.create_from_s3(
            key=key,
            name=request.FILES['file'].name,
            last_modified=timezone.now(),
            size=request.FILES['file'].size)

    return HttpResponseRedirect(reverse('index'))


def file(request, key):
    fname = UploadedFile.objects.get(key=key).name
    s3c = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    f = tempfile.NamedTemporaryFile()
    s3c.download_fileobj(
        Bucket=S3_BUCKET_FILE,
        Key=str(key),
        Fileobj=f)
    f.seek(0)
    return FileResponse(f, as_attachment=True, filename=fname)

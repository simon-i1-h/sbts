from django.db import transaction

from django.http import HttpResponse, FileResponse, JsonResponse, \
    HttpResponseNotAllowed
from django.utils import timezone
from .models import UploadedFile, upload_file
import boto3

from sbts.settings import S3_BUCKET_FILE, S3_ENDPOINT


def upload(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    key = upload_file(request)
    return JsonResponse({
        'key': key
    })


def create(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    with transaction.atomic():
        UploadedFile.objects.create_from_s3(
            key=request.POST['key'],
            name=request.POST['name'],
            last_modified=timezone.now(),
            size=request.POST['size'])

    return HttpResponse()


def file(request, key):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    fname = UploadedFile.objects.get(key=key).name
    s3client = boto3.client('s3', endpoint_url=S3_ENDPOINT)
    s3obj = s3client.get_object(Bucket=S3_BUCKET_FILE, Key=str(key))

    resp = FileResponse(
        s3obj['Body'],
        content_type='application/octet-stream',
        as_attachment=True,
        filename=fname,
    )
    resp['Content-Length'] = s3obj['ContentLength']
    return resp

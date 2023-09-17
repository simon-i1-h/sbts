from django.http import FileResponse
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.parsers import BaseParser
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3

from sbts.public.settings import S3_BUCKET_FILE, S3_ENDPOINT

from .models import UploadedFile, upload_file


class StreamParser(BaseParser):
    media_type = 'application/octet-stream'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream


class StreamRequestView(APIView):
    parser_classes = [StreamParser]


class LoginRequiredView(LoginRequiredMixin, View):
    pass


class UploadView(StreamRequestView):
    def post(self, request, format=None):
        key = upload_file(request.data, request.user.username)
        return Response({'key': key})


class CreateView(APIView):
    def post(self, request, format=None):
        UploadedFile.objects.create_from_s3(
            key=request.data['key'],
            username=request.user.username,
            name=request.data['name'],
            last_modified=timezone.now())
        return Response({})


class BlobView(LoginRequiredView):
    def get(self, request, *args, **kwargs):
        fname = UploadedFile.objects.get(key=kwargs['key']).name
        s3client = boto3.client('s3', endpoint_url=S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=S3_BUCKET_FILE, Key=str(kwargs['key']))

        resp = FileResponse(
            s3obj['Body'],
            content_type='application/octet-stream',
            as_attachment=True,
            filename=fname,
        )
        resp['Content-Length'] = s3obj['ContentLength']
        return resp

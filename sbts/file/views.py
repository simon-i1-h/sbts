from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.parsers import BaseParser
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3
import io

from .models import UploadedFile, upload_file


class StreamParser(BaseParser):
    media_type = 'application/octet-stream'

    def parse(self, stream, media_type=None, parser_context=None):
        return {'blob': stream}


class StreamRequestView(APIView):
    parser_classes = [StreamParser]


class LoginRequiredView(LoginRequiredMixin, View):
    pass


class UploadView(StreamRequestView):
    def post(self, request, format=None):
        key = upload_file(
            # HTTPリクエストのボディが空な場合、request.dataが空辞書に
            # なる
            request.data.get('blob', io.BytesIO(b'')),
            request.user.username)
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
        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(
            Bucket=settings.S3_BUCKET_FILE,
            Key=str(kwargs['key']))

        resp = FileResponse(
            s3obj['Body'],
            content_type='application/octet-stream',
            as_attachment=True,
            filename=fname,
        )
        resp['Content-Length'] = s3obj['ContentLength']
        return resp

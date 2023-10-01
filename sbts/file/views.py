from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse, Http404
from django.views import View
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


class UploadView(StreamRequestView):
    def post(self, request, format=None):
        key = upload_file(
            # HTTPリクエストのボディが空な場合、request.dataが空辞書に
            # なる
            request.data.get('blob', io.BytesIO(b'')),
            request.user.username)
        return Response({'key': key})


class BlobView(View):
    def get(self, request, *args, **kwargs):
        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        try:
            fname = UploadedFile.objects.get(key=kwargs['key']).name
            s3obj = s3client.get_object(
                Bucket=settings.S3_BUCKET_FILE,
                Key=str(kwargs['key']))
        except (ObjectDoesNotExist,
                s3client.exceptions.NoSuchKey,
                s3client.exceptions.InvalidObjectState):
            raise Http404()

        resp = FileResponse(
            s3obj['Body'],
            content_type='application/octet-stream',
            as_attachment=True,
            filename=fname,
        )
        resp['Content-Length'] = s3obj['ContentLength']
        return resp

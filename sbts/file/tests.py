import io
import random

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings

import boto3
from botocore.exceptions import EndpointConnectionError

from sbts.core.test_utils import ObjectStorageTestCase

from .models import upload_file, S3Uploader


class UploadFileTest(ObjectStorageTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')

    def test_ok(self):
        content = b'hello.'
        file = io.BytesIO(content)
        key = upload_file(file, self.user_shimon.username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=settings.S3_BUCKET_FILE, Key=str(key))

        self.assertEqual(s3obj['Body'].read(), content)
        o1 = S3Uploader.objects.get(id=key)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, len(content))

    def test_0byte(self):
        '''
        0バイトのデータもアップロード可能
        '''

        content = b''
        file = io.BytesIO(content)
        key = upload_file(file, self.user_shimon.username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=settings.S3_BUCKET_FILE, Key=str(key))

        self.assertEqual(s3obj['Body'].read(), content)
        o1 = S3Uploader.objects.get(id=key)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, len(content))

    def test_chunk(self):
        '''
        マルチパートアップロードのチャンクと同じ大きさのデータ
        '''

        content = random.Random(0).randbytes(settings.S3_CHUNK_SIZE)
        file = io.BytesIO(content)
        key = upload_file(file, self.user_shimon.username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=settings.S3_BUCKET_FILE, Key=str(key))

        self.assertEqual(s3obj['Body'].read(), content)
        o1 = S3Uploader.objects.get(id=key)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, len(content))

    def test_chunk_plus_1(self):
        '''
        マルチパートアップロードのチャンク+1の大きさのデータ
        '''

        content = random.Random(0).randbytes(settings.S3_CHUNK_SIZE + 1)
        file = io.BytesIO(content)
        key = upload_file(file, self.user_shimon.username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=settings.S3_BUCKET_FILE, Key=str(key))

        self.assertEqual(s3obj['Body'].read(), content)
        o1 = S3Uploader.objects.get(id=key)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, len(content))

    @override_settings(S3_ENDPOINT='http://invalid:9000')
    def test_no_s3(self):
        '''
        オブジェクトストレージにアクセスできない場合でも、データベース
        側にメタデータは残る
        '''

        content = b'hello.'
        file = io.BytesIO(content)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [])

        with self.assertRaises(EndpointConnectionError):
            upload_file(file, self.user_shimon.username)

        o1 = S3Uploader.objects.get(username=self.user_shimon.username)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.UPLOADING)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, -1)

    def test_empty_username(self):
        username = ''
        content = b'hello.'
        file = io.BytesIO(content)
        key = upload_file(file, username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3obj = s3client.get_object(Bucket=settings.S3_BUCKET_FILE, Key=str(key))

        self.assertEqual(s3obj['Body'].read(), content)
        o1 = S3Uploader.objects.get(id=key)
        self.assertQuerySetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, username)
        self.assertEqual(o1.size, len(content))

    def test_nested_atomic(self):
        '''
        データベースの永続性を確保するため、呼び出し側でトランザクショ
        ンを開いておくことはできない。
        '''

        content = b'hello.'
        file = io.BytesIO(content)

        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                upload_file(file, self.user_shimon.username)

        self.assertQuerySetEqual(S3Uploader.objects.all(), [])

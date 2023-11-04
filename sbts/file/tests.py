import datetime
import io
import random
import string
import uuid

from django.db import transaction, DataError
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import TestCase, override_settings

import boto3
from botocore.exceptions import EndpointConnectionError

from sbts.core.test_utils import ObjectStorageTestCase

from .models import upload_file, S3Uploader, UploadedFile


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

        content = random.Random(1).randbytes(settings.S3_CHUNK_SIZE + 1)
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


class UploadedFileCreateFromS3Test(TestCase):
    '''
    各期待しないパラメータについては、原則他のすべてのパラメータは期待
    の値にして検証する。
    '''

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')
        # 実際にアップロードしようとすると、タイミングの問題でS3にアクセスできない。
        # S3にアクセスする必要はないので、テストではupload_fileを使わず、単にオブジェクトを作成しておく。
        cls.blob = S3Uploader.objects.create(
            status=S3Uploader.COMPLETED, username=cls.user_shimon.username, size=6)

    def test_ok(self):
        filename = 'hello.txt'
        lastmod = datetime.datetime.fromisoformat('2023-11-04T12:00:00Z')
        f1 = UploadedFile.objects.create_from_s3(
            self.blob.id, self.user_shimon.username, filename, lastmod)

        self.assertQuerySetEqual(UploadedFile.objects.all(), [f1])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [])
        self.assertEqual(f1.key, self.blob.id)
        self.assertEqual(f1.name, filename)
        self.assertEqual(f1.last_modified, lastmod)
        self.assertEqual(f1.size, self.blob.size)
        self.assertEqual(f1.username, self.user_shimon.username)

    def test_empty_key(self):
        filename = 'hello.txt'
        lastmod = datetime.datetime.fromisoformat('2023-11-04T12:00:00Z')

        with self.assertRaises(ValidationError):
            UploadedFile.objects.create_from_s3(
                '', self.user_shimon.username, filename, lastmod)

        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.blob])

    def test_invalid_key(self):
        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        self.assertNotEqual(key, self.blob.id)

        filename = 'hello.txt'
        lastmod = datetime.datetime.fromisoformat('2023-11-04T12:00:00Z')

        with self.assertRaises(ObjectDoesNotExist):
            UploadedFile.objects.create_from_s3(
                key, self.user_shimon.username, filename, lastmod)

        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.blob])

    def test_invalid_username(self):
        username = ''.join(random.Random(2).choices(string.ascii_lowercase, k=151))
        filename = 'hello.txt'
        lastmod = datetime.datetime.fromisoformat('2023-11-04T12:00:00Z')

        with self.assertRaises(ObjectDoesNotExist):
            UploadedFile.objects.create_from_s3(
                self.blob.id, username, filename, lastmod)

        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.blob])

    def test_invalid_filename(self):
        filename = ''.join(random.Random(3).choices(string.ascii_lowercase, k=256))
        lastmod = datetime.datetime.fromisoformat('2023-11-04T12:00:00Z')

        with self.assertRaises(DataError):
            UploadedFile.objects.create_from_s3(
                self.blob.id, self.user_shimon.username, filename, lastmod)

        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.blob])

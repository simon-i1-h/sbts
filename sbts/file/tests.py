import io

from django.conf import settings
from django.contrib.auth.models import User

import boto3

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
        self.assertQuerysetEqual(S3Uploader.objects.all(), [o1])
        self.assertEqual(o1.status, S3Uploader.COMPLETED)
        self.assertEqual(o1.username, self.user_shimon.username)
        self.assertEqual(o1.size, len(content))

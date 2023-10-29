import subprocess
from subprocess import DEVNULL
import uuid

from django.conf import settings
from django.test import TestCase, override_settings

import boto3


@override_settings(S3_BUCKET_FILE='test-{}'.format(uuid.uuid4()))
class ObjectStorageTestCase(TestCase):
    def setUp(self):
        super().setUp()
        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)
        s3client.create_bucket(Bucket=settings.S3_BUCKET_FILE)

    def tearDown(self):
        super().tearDown()
        # コマンドの方が手っ取り早い
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html
        cmd = ['aws', '--endpoint-url', f'{settings.S3_ENDPOINT}',
               's3', 'rb', f's3://{settings.S3_BUCKET_FILE}', '--force']
        subprocess.run(cmd, stdout=DEVNULL, check=True)

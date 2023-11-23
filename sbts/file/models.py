from django.conf import settings
from django.db import models, transaction
import uuid
import boto3


class UploadedFile(models.Model):
    class Manager(models.Manager):
        def create_from_s3(self, key, username, filename, last_modified, **kwargs):
            with transaction.atomic():
                uploader = S3Uploader.objects.get(
                    key=key,
                    status=S3Uploader.COMPLETED,
                    size__isnull=False,
                    # 他のユーザーのブロブは参照できない
                    username=username)
                # S3のオブジェクトの所有者をS3UploaderからUploadedFileに移動
                file = self.create(
                    key=key,
                    name=filename,
                    last_modified=last_modified,
                    size=uploader.size,
                    username=username,
                    **kwargs)
                uploader.delete()

                return file

    class Meta:
        default_manager_name = 'objects'

    objects = Manager()

    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    last_modified = models.DateTimeField()
    size = models.BigIntegerField()
    username = models.CharField(max_length=150)


# 内部用
class S3Uploader(models.Model):
    COMPLETED = 0
    UPLOADING = 1
    STATUS_CHOICES = [
        (COMPLETED, 'Completed'),
        (UPLOADING, 'Uploading'),
    ]

    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    status = models.IntegerField(choices=STATUS_CHOICES)
    size = models.BigIntegerField(null=True)
    username = models.CharField(max_length=150)

    @classmethod
    def upload(cls, blob, username):
        key = uuid.uuid4()
        size = 0

        with transaction.atomic(durable=True):
            cls.objects.create(
                key=key,
                status=cls.UPLOADING,
                username=username)

        s3client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT)

        resp = s3client.create_multipart_upload(
            Bucket=settings.S3_BUCKET_FILE,
            Key=str(key))
        upload_id = resp['UploadId']

        multipart_upload = {
            'Parts': []
        }
        partnum = 1  # 1 ~ 10,000
        while chunk := blob.read(settings.S3_CHUNK_SIZE):
            part = s3client.upload_part(
                Body=chunk,
                Bucket=settings.S3_BUCKET_FILE,
                Key=str(key),
                PartNumber=partnum,
                UploadId=upload_id)
            multipart_upload['Parts'].append({
                'ETag': part['ETag'],
                'PartNumber': partnum,
            })
            partnum += 1
            size += len(chunk)

        # 空ファイルの場合
        if partnum == 1:
            part = s3client.upload_part(
                Body=b'',
                Bucket=settings.S3_BUCKET_FILE,
                Key=str(key),
                PartNumber=partnum,
                UploadId=upload_id)
            multipart_upload['Parts'].append({
                'ETag': part['ETag'],
                'PartNumber': partnum,
            })

        s3client.complete_multipart_upload(
            Bucket=settings.S3_BUCKET_FILE,
            Key=str(key),
            MultipartUpload=multipart_upload,
            UploadId=upload_id)

        with transaction.atomic(durable=True):
            uploader = cls.objects.get(key=key, status=cls.UPLOADING)
            uploader.status = cls.COMPLETED
            uploader.size = size
            uploader.save()

        return key


def upload_blob(blob, username):
    return S3Uploader.upload(blob, username)

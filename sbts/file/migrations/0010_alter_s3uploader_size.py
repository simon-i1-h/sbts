# Generated by Django 4.2.7 on 2023-11-23 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0009_alter_s3uploader_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='s3uploader',
            name='size',
            field=models.BigIntegerField(default=None, null=True),
        ),
    ]
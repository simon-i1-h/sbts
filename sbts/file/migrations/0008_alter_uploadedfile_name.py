# Generated by Django 4.2.7 on 2023-11-23 10:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0007_rename_id_s3uploader_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='name',
            field=models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
    ]

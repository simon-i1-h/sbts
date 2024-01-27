# Generated by Django 4.2.7 on 2023-11-23 10:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0006_alter_comment_comment_alter_ticket_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='title',
            field=models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
    ]
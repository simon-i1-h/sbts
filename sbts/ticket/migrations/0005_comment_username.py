# Generated by Django 4.2.5 on 2023-10-01 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0004_remove_comment_is_modified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='username',
            field=models.CharField(default='shimon', max_length=150),
            preserve_default=False,
        ),
    ]

# Generated by Django 4.2.5 on 2023-09-23 06:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('key', models.UUIDField(primary_key=True, serialize=False)),
                ('title', models.TextField()),
                ('created_at', models.DateTimeField()),
                ('last_updated', models.DateTimeField()),
            ],
            options={
                'default_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('key', models.UUIDField(primary_key=True, serialize=False)),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField()),
                ('last_updated', models.DateTimeField()),
                ('is_modified', models.BooleanField(default=False)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ticket.ticket')),
            ],
        ),
    ]

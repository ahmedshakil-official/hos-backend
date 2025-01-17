# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-16 10:23
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('prescription', '0008_auto_20170816_1049'),
    ]

    operations = [
        migrations.CreateModel(
            name='DietSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('diet_time', models.TimeField()),
                ('label', models.CharField(blank=True, max_length=255, null=True)),
                ('reminder', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft')], db_index=True, default=0)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft')], db_index=True, default=0)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='diet_person', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
    ]

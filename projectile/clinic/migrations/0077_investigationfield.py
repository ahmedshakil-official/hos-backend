# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-21 07:48
from __future__ import unicode_literals

import autoslug.fields
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0065_auto_20180313_1620'),
        ('clinic', '0076_merge_20180320_0557'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestigationField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from=b'name', unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_global', enumerify.fields.SelectIntegerField(choices=[(0, b'Private'), (1, b'Global'), (2, b'Changed into Global')], db_index=True, default=0)),
                ('price', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('clone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.InvestigationField')),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_investigationfield_entry_by', to=settings.AUTH_USER_MODEL, verbose_name=b'entry by')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='clinic_investigationfield_updated_by', to=settings.AUTH_USER_MODEL, verbose_name=b'last updated by')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]

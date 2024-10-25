# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-26 06:27
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0028_auto_20180511_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnosis',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='diagnosisdepartment',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='dose',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='labtest',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='physicaltest',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='symptom',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
    ]
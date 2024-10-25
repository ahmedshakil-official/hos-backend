# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-26 06:27
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0108_merge_20180623_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bed',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='diagnostictestsample',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='dutyshift',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='investigationfield',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='reportfieldcategory',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='subservice',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='subservicereportfield',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='treatmentsession',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='ward',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
    ]

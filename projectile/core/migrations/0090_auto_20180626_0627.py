# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-26 06:27
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0089_auto_20180623_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='employeedesignation',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='grouppermission',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
        migrations.AlterField(
            model_name='referrercategory',
            name='slug',
            field=autoslug.fields.AutoSlugField(allow_unicode=True, always_update=True, editable=False, populate_from=b'name', unique=True),
        ),
    ]
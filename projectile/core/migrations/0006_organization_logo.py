# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-18 07:17
from __future__ import unicode_literals

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20170714_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='logo',
            field=common.fields.TimestampImageField(blank=True, null=True, upload_to=b'organization/logo'),
        ),
    ]
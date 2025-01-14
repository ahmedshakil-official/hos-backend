# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-20 07:55
from __future__ import unicode_literals

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20170616_0637'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='hero_image',
            field=common.fields.TimestampImageField(blank=True, null=True, upload_to=b'profiles/hero'),
        ),
        migrations.AddField(
            model_name='person',
            name='profile_image',
            field=common.fields.TimestampImageField(blank=True, null=True, upload_to=b'profiles/pic'),
        ),
    ]

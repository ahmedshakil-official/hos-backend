# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-04 09:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20170620_0955'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='degree',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='registration_number',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-29 07:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0082_auto_20181114_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='global_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='local_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='organizationwise_count',
            field=models.IntegerField(default=0),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-24 12:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0106_auto_20180919_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='auto_adjustment',
            field=models.BooleanField(default=False, help_text='Settings for enable/disable auto adjustment'),
        ),
    ]

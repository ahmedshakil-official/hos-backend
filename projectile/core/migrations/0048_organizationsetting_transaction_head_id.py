# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-16 06:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_auto_20180112_1740'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='transaction_head_id',
            field=models.BooleanField(default=True, help_text='Settings for transaction head id while transaction add'),
        ),
    ]
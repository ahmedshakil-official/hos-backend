# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-29 14:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20180129_2040'),
    ]

    operations = [
        migrations.RenameField(
            model_name='smslog',
            old_name='response_form_server',
            new_name='response_from_server',
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-02 07:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0096_organizationsetting_show_referrer_honorarium'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='persongroup',
            name='entry_by',
        ),
        migrations.RemoveField(
            model_name='persongroup',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='persongroup',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='PersonGroup',
        ),
    ]

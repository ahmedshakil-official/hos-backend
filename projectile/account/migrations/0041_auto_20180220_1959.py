# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-20 13:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0040_merge_20180215_1929'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accountcheque',
            old_name='reference',
            new_name='reference_name',
        ),
    ]

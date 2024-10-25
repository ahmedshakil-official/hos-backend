# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-13 14:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0115_subservice_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='allow_honorarium',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='honorarium_paid',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
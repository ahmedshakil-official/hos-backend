# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-15 09:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0029_auto_20180626_0627'),
        ('clinic', '0118_merge_20180814_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='prescription',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumed', to='prescription.Prescription'),
        ),
    ]

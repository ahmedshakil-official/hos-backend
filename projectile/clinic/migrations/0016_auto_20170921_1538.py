# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-21 09:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0015_auto_20170921_1421'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appointmenttreatmentsession',
            options={'ordering': ('-created_at',)},
        ),
        migrations.AlterUniqueTogether(
            name='appointmenttreatmentsession',
            unique_together=set([]),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-02 11:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinic', '0004_auto_20170714_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmenttreatmentsession',
            name='appointment_with',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_with', to=settings.AUTH_USER_MODEL),
        ),
    ]

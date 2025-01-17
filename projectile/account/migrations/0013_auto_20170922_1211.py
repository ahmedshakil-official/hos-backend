# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-22 06:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0017_auto_20170921_1610'),
        ('account', '0012_auto_20170920_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='admission',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='admission_transaction', to='clinic.PatientAdmission'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='service_consumed',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumed_transaction', to='clinic.ServiceConsumed'),
        ),
    ]

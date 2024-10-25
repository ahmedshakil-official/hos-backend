# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-11 10:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0048_patientbill'),
        ('pharmacy', '0050_auto_20180412_0732'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='bill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales_on_patient_bill', to='account.PatientBill'),
        ),
    ]

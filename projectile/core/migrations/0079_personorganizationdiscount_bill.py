# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-11 10:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0048_patientbill'),
        ('core', '0078_merge_20180511_0942'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganizationdiscount',
            name='bill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='organization_discount_on_bill', to='account.PatientBill'),
        ),
    ]

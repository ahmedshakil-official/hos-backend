# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-25 12:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0018_appointmenttreatmentsession_patient_admission'),
        ('prescription', '0012_auto_20170920_1536'),
        ('pharmacy', '0015_merge_20170920_2034'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='patient_admission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales_patient_admission', to='clinic.PatientAdmission'),
        ),
        migrations.AddField(
            model_name='sales',
            name='prescription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales_prescription', to='prescription.Prescription'),
        ),
    ]

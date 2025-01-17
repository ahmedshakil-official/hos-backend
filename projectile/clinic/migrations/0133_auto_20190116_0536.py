# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-16 05:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0132_productofservice'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionconsultant',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='appointmentschedule',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='appointmentschedulemissed',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='appointmentserviceconsumed',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='appointmenttreatmentsession',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='bed',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='bedsection',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='diagnostictestsample',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='dutyshift',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='employeeattendance',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='employeesession',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='investigationfield',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='organizationdepartment',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='patientadmission',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='patientadmissionbed',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='productofservice',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='referrercategorydiscountgroup',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='reportfieldcategory',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='serviceconsumedgroup',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='serviceconsumedgroupsalestransation',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='serviceconsumedimage',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservice',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservicereport',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservicereportfield',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservicereportfieldnormalvalue',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservicesample',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subservicesamplecollection',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='treatmentsession',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='ward',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
    ]

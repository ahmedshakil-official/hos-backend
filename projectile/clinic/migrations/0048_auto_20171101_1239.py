# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-01 06:39
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0047_merge_20171031_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointmentschedule',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='appointmentschedulemissed',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='appointmenttreatmentsession',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='bed',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='bedsection',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dutyshift',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='employeeattendance',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='patientadmission',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='service',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='serviceconsumed',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='serviceconsumedgroup',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='serviceconsumedimage',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='subservice',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='subservicereport',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='subservicereportfield',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='subservicereportfieldnormalvalue',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='treatmentsession',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
    ]

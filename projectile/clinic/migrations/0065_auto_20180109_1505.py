# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-09 09:05
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_auto_20180109_1505'),
        ('clinic', '0064_merge_20180108_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceconsumed',
            name='referer_honorarium',
            field=models.FloatField(db_index=True, default=0.0, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterIndexTogether(
            name='admissionconsultant',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='appointmentschedule',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='appointmentschedulemissed',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='appointmenttreatmentsession',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='bedsection',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='employeeattendance',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='patientadmission',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='serviceconsumed',
            index_together=set([('organization', 'status')]),
        ),
        migrations.AlterIndexTogether(
            name='serviceconsumedgroup',
            index_together=set([('organization', 'status')]),
        ),
    ]

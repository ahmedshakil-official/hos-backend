# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-11 08:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0036_auto_20171010_1944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointmentschedule',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='appointmenttreatmentsession',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='employeeattendance',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='patientadmission',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='serviceconsumed',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
        migrations.AlterField(
            model_name='serviceconsumedgroup',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name=b'organization name'),
        ),
    ]

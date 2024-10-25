# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-11 13:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_auto_20180109_1505'),
        ('clinic', '0065_auto_20180109_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmentschedule',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_schedule_person_organization', to='core.PersonOrganization', verbose_name='appointment schedule by person of organization'),
        ),
        migrations.AddField(
            model_name='appointmenttreatmentsession',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_treatment_person_organization', to='core.PersonOrganization', verbose_name='appointment of person of organization'),
        ),
    ]
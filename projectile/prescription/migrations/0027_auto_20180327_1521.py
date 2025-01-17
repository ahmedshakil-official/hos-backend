# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-27 09:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0067_auto_20180323_1311'),
        ('prescription', '0026_auto_20180305_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='person_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='patient_prescription_person_organization', to='core.PersonOrganization', verbose_name='patient in person organization'),
        ),
        migrations.AddField(
            model_name='prescription',
            name='person_organization_prescriber',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='prescriber_prescription_person_organization', to='core.PersonOrganization', verbose_name='prescriber in person organization'),
        ),
    ]

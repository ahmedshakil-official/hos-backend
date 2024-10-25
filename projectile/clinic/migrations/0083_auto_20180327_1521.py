# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-27 09:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0067_auto_20180323_1311'),
        ('clinic', '0082_auto_20180322_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmentschedule',
            name='person_organization_with',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_schedule_with_person_organization', to='core.PersonOrganization', verbose_name='appointment with in person organization'),
        ),
        migrations.AddField(
            model_name='appointmenttreatmentsession',
            name='person_organization_with',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_with_person_organization', to='core.PersonOrganization', verbose_name='appointment with in person organization'),
        ),
        migrations.AddField(
            model_name='patientadmission',
            name='person_organization_consultant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='consultant_person_organization', to='core.PersonOrganization', verbose_name='consultant person organization'),
        ),
        migrations.AddField(
            model_name='patientadmission',
            name='person_organization_patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='patient_person_organization', to='core.PersonOrganization', verbose_name='patient person organization'),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='person_organization_patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_consumed_patient_person_organization', to='core.PersonOrganization', verbose_name='patient in person organization'),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='person_organization_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_provider_person_organization', to='core.PersonOrganization', verbose_name='provider in person organization'),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='person_organization_reference',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='reference_provider_person_organization', to='core.PersonOrganization', verbose_name='reference in person organization'),
        ),
    ]

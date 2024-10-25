# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-10 10:00
from __future__ import unicode_literals

import common.validators
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_personorganization_duty_shift'),
        ('clinic', '0032_merge_20171010_1505'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('days', enumerify.fields.SelectIntegerField(choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday'), (5, b'Saturday'), (6, b'Sunday')], db_index=True, default=0)),
                ('price', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('discount', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('remarks', models.CharField(max_length=256)),
                ('confirmed', enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Patient Created But Yet Unapproved'), (2, b'Dr. Created But Yet Unapproved'), (3, b'Approved By Both')], db_index=True, default=3)),
                ('payable', models.BooleanField(default=True)),
                ('appointment_with', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_schedule_with', to=settings.AUTH_USER_MODEL, validators=[common.validators.is_employee])),
                ('bed', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.Bed')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization')),
                ('patient_admission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointment_patient_admission_schedule', to='clinic.PatientAdmission')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, validators=[common.validators.is_patient])),
                ('treatment_session', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.TreatmentSession')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='appointmentschedule',
            unique_together=set([('treatment_session', 'bed')]),
        ),
    ]
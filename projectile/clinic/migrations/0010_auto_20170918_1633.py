# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-18 10:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_organizationsetting'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinic', '0009_merge_20170913_1941'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientAdmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('admission_date', models.DateTimeField()),
                ('cost', models.FloatField(default='0.00')),
                ('discount', models.FloatField(default='0.00')),
                ('payable', models.FloatField(default='0.00')),
                ('release_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('remarks', models.CharField(max_length=256)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='admited_patient', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PatientAdmissionBed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cost', models.FloatField(default='0.00')),
                ('admission_date', models.DateTimeField()),
                ('release_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('total_cost', models.FloatField(default='0.00')),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Admitted'), (2, b'Transfered'), (3, b'Checkedout')], db_index=True, default=1)),
                ('bed', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='admission_bed', to='clinic.Bed')),
                ('patient_admission', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='admission', to='clinic.PatientAdmission')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='patient_admission',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='service_for_inhouse_patient', to='clinic.PatientAdmission'),
        ),
    ]

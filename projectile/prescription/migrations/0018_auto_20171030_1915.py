# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-30 13:15
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0017_auto_20171018_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnosis',
            name='is_allergy',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='is_curable',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dietschedule',
            name='reminder',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dietschedule',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dose',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='labtest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='medicineschedule',
            name='reminder',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='medicineschedule',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='physicaltest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptiondiagnosis',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionlabtest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionphysicaltest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionsymptom',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptiontreatment',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='symptom',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
    ]
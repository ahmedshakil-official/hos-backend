# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-28 12:22
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0038_auto_20190201_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnosis',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='diagnosisdepartment',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dietschedule',
            name='reminder',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dietschedule',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='dose',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='labtest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='medicineschedule',
            name='reminder',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='medicineschedule',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='physicaltest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptiondiagnosis',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionlabtest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionphysicaltest',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptionsymptom',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriptiontreatment',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='symptom',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired')], db_index=True, default=0),
        ),
    ]

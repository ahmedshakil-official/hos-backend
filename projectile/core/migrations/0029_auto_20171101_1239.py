# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-01 06:39
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20171030_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='employeedesignation',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='grouppermission',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='organization',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='organizationsetting',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='person',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='persongroup',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganization',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganizationgrouppermission',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft'), (5, b'Absent')], db_index=True, default=0),
        ),
    ]
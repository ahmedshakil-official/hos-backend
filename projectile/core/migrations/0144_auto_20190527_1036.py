# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-27 04:36
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0143_organizationsetting_global_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_profit_margin',
            field=models.BooleanField(default=False, help_text='Settings for enable/disable Profit Margin'),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='profit_margin',
            field=models.FloatField(default=0.0, help_text='Profit input as percentage(%)', validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='department',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='discountgroup',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='employeedesignation',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='grouppermission',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='organization',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='organizationsetting',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='person',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='persongroup',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganization',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganizationdiscount',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganizationgrouppermission',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='personorganizationsalary',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriberdesignation',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='prescriberreferrercategory',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='referrercategory',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='salarygrade',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='salarygradeheads',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='salaryhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='smslog',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order'), (7, b'Suspend'), (8, b'On Hold'), (9, b'Hardwired'), (10, b'Loss')], db_index=True, default=0),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-19 11:38
from __future__ import unicode_literals

from django.db import migrations, models
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0105_merge_20180831_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='discountgroup',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='employeedesignation',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='grouppermission',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='organization',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='serial_type',
            field=enumerify.fields.SelectIntegerField(choices=[(1, b'Default'), (2, b'Organization Wise'), (3, b'No Serial')], db_index=True, default=1, help_text='Choose Serial/ID type'),
        ),
        migrations.AddField(
            model_name='person',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='persongroup',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='personorganization',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='personorganizationdiscount',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='personorganizationgrouppermission',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='personorganizationsalary',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='prescriberdesignation',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='prescriberreferrercategory',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='referrercategory',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
        migrations.AddField(
            model_name='smslog',
            name='organization_wise_serial',
            field=models.PositiveIntegerField(default=0, editable=False, help_text=b'OrganizationWise Serial Number'),
        ),
    ]

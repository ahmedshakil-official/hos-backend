# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-16 05:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0125_organizationsetting_multiple_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='discountgroup',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='employeedesignation',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='grouppermission',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='persongroup',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='personorganization',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='personorganizationdiscount',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='personorganizationgrouppermission',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='personorganizationsalary',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='prescriberdesignation',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='prescriberreferrercategory',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='referrercategory',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='smslog',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, editable=False, null=True),
        ),
    ]
